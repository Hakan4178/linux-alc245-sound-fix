#!/usr/bin/env python3
import time
import os
import sys
import shutil
import subprocess
import numpy as np
import sounddevice as sd
from evdev import UInput, ecodes
from collections import deque

# ---------------- Config ----------------
# BACKEND OPTIONS:
# "playerctl"  -> user session DBus (no sudo). Recommended when run as user.
# "uinput"     -> virtual input device (requires root / sudo). Use if playerctl unavailable.
# "auto"       -> prefer playerctl if available & DBUS session present, else fallback to uinput
BACKEND = "uinput"

RATE = 48000
BLOCKSIZE = 128
CALIBRATE_SECONDS = 2.6

WINDOW_MS = 120
MIN_BURST_BLOCKS = 9
REL_FACTOR = 13
MIN_ABS_THRESHOLD = 13000

SUPPRESS_MS = 340
PRESS_DELAY = 0.04
# ----------------------------------------

def detect_playerctl_available():
    """Return True if 'playerctl' command exists AND a DBUS session is present (so it can reach user players)."""
    if shutil.which("playerctl") is None:
        return False
    # If running as root, DBUS session usually not present -> playerctl won't see user players
    # Prefer to require DBUS_SESSION_BUS_ADDRESS environment variable
    if os.getenv("DBUS_SESSION_BUS_ADDRESS"):
        return True
    # Sometimes user runs with sudo -E preserving env; allow that too
    return False

def emit_playerctl():
    """Call playerctl play-pause in background (no blocking output)."""
    try:
        subprocess.Popen(["playerctl", "play-pause"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print("❌ playerctl call failed:", e)

def init_uinput():
    """Initialize and return a UInput device (may require root)."""
    try:
        ui_dev = UInput({ecodes.EV_KEY: [ecodes.KEY_PLAYPAUSE, ecodes.KEY_MEDIA]}, name="headset-quick-hard")
        return ui_dev
    except Exception as e:
        print("❌ Failed to create uinput device:", e)
        return None

# ---------- Validate BACKEND config ----------
if BACKEND not in ("uinput", "playerctl", "auto"):
    print("⚠️ Invalid BACKEND in config. Must be 'uinput', 'playerctl' or 'auto'.")
    sys.exit(1)

# ---------- Device selector ----------
def select_input_device():
    devices = sd.query_devices()
    inputs = []

    print("\n🎧 Available input devices:\n")
    for i, d in enumerate(devices):
        if d.get("max_input_channels", 0) > 0:
            inputs.append(i)
            print(f"[{i}] {d['name']} (inputs={d['max_input_channels']})")

    if not inputs:
        print("❌ No input devices found.")
        sys.exit(1)

    while True:
        try:
            choice = input("\nSelect device index (or press Enter to use default 0): ").strip()
            if choice == "":
                return inputs[0]
            choice = int(choice)
            if choice in inputs:
                return choice
            else:
                print("⚠️ Invalid selection.")
        except ValueError:
            print("⚠️ Please enter a number.")

DEVICE_INDEX = select_input_device()
print(f"\n✅ Using device #{DEVICE_INDEX}: {sd.query_devices(DEVICE_INDEX)['name']}")

# ---------- Backend selection logic (auto / explicit) ----------
actual_backend = None
ui = None
emit_func = None

if BACKEND == "playerctl":
    if shutil.which("playerctl") is None:
        print("❌ BACKEND is set to 'playerctl' but playerctl executable not found. Install playerctl or use BACKEND='auto'/'uinput'.")
        sys.exit(1)
    # Warn if run as root
    if os.geteuid() == 0 and not os.getenv("DBUS_SESSION_BUS_ADDRESS"):
        print("⚠️ Running as root: playerctl may not be able to reach your user DBus session. Consider running without sudo or use BACKEND='uinput'.")
    actual_backend = "playerctl"
    emit_func = emit_playerctl

elif BACKEND == "uinput":
    actual_backend = "uinput"
    ui = init_uinput()
    if ui is None:
        print("❌ Failed to init uinput. Are you running with sufficient privileges?")
        sys.exit(1)
    def _emit_uinput():
        ui.write(ecodes.EV_KEY, ecodes.KEY_MEDIA, 1); ui.syn()
        time.sleep(PRESS_DELAY)
        ui.write(ecodes.EV_KEY, ecodes.KEY_MEDIA, 0); ui.syn()
    emit_func = _emit_uinput

elif BACKEND == "auto":
    # prefer playerctl if it exists and DBUS session looks available
    if detect_playerctl_available():
        actual_backend = "playerctl"
        emit_func = emit_playerctl
        print("✅ auto: playerctl detected and will be used (user DBus available).")
    else:
        # fallback to uinput
        actual_backend = "uinput"
        ui = init_uinput()
        if ui is None:
            print("❌ auto: playerctl not available and uinput initialization failed. Exiting.")
            sys.exit(1)
        def _emit_uinput():
            ui.write(ecodes.EV_KEY, ecodes.KEY_MEDIA, 1); ui.syn()
            time.sleep(PRESS_DELAY)
            ui.write(ecodes.EV_KEY, ecodes.KEY_MEDIA, 0); ui.syn()
        emit_func = _emit_uinput
        print("⚠️ auto: playerctl not detected or DBUS not available -> falling back to uinput (requires root).")

print(f"[+] Actual backend: {actual_backend}")

# ---------- Calibration ----------
print("\n🎚️ Calibrating background noise...")
print("➡️  Do NOT press the headset button.")

cal = []
def cal_cb(indata, frames, t, status):
    cal.append(np.mean(np.abs(indata[:, 0].astype(int))))

with sd.InputStream(device=DEVICE_INDEX, samplerate=RATE, channels=1, dtype="int16",
                    blocksize=BLOCKSIZE, callback=cal_cb, latency="low"):
    time.sleep(CALIBRATE_SECONDS)

baseline_abs = float(np.median(cal))
sigma_abs = float(np.std(cal))
auto_thr = max(MIN_ABS_THRESHOLD, baseline_abs + REL_FACTOR * max(1.0, sigma_abs))

print("✅ Calibration done")
print(f"   baseline_abs = {int(baseline_abs)}")
print(f"   sigma_abs    = {int(sigma_abs)}")
print(f"   auto_thr     = {int(auto_thr)}")

# ---------- Runtime state ----------
events = deque()
last_fire = 0
suppress_until = 0

def emit():
    print("🎵 PLAY/PAUSE (emit)")
    try:
        emit_func()
    except Exception as e:
        print("❌ emit failed:", e)

def cb(indata, frames, t, status):
    global last_fire, suppress_until

    block = indata[:, 0].astype(int)
    mean_abs = float(np.abs(block).mean())
    maxabs = int(np.abs(block).max())
    now = time.monotonic()

    if mean_abs > auto_thr or maxabs > 32000:
        events.append(now)

    while events and (now - events[0]) * 1000 > WINDOW_MS:
        events.popleft()

    if now < suppress_until:
        return

    if len(events) >= MIN_BURST_BLOCKS and (now - last_fire) > 0.25:
        emit()
        last_fire = now
        suppress_until = now + (SUPPRESS_MS / 1000.0)
        events.clear()

        print(time.strftime("[%H:%M:%S]"), "TRIG", "mean_abs", int(mean_abs), "max", maxabs)

# ---------- Main loop ----------
print("\n🎧 Listening...")
print("➡️  Press headset button to trigger play/pause")
print("➡️  Ctrl+C to exit\n")

try:
    with sd.InputStream(device=DEVICE_INDEX, samplerate=RATE, channels=1, dtype="int16",
                        blocksize=BLOCKSIZE, callback=cb, latency="low"):
        while True:
            time.sleep(0.2)

except KeyboardInterrupt:
    print("\n🛑 Stopped by user")

finally:
    if ui:
        ui.close()
