#!/usr/bin/env python3
import time
import numpy as np
import sounddevice as sd
from evdev import UInput, ecodes
from collections import deque
import sys

# ================= USER CONFIG =================
RATE = 48000
BLOCKSIZE = 128
CALIBRATE_SECONDS = 2.6

WINDOW_MS = 120
MIN_BURST_BLOCKS = 9
REL_FACTOR = 13
MIN_ABS_THRESHOLD = 13000
RELEASE_FACTOR = 0.35
RELEASE_STABLE_MS = 120

SUPPRESS_MS = 360
PRESS_DELAY = 0.04
# ===============================================


# ---------- Device selector ----------
def select_input_device():
    devices = sd.query_devices()
    inputs = []

    print("\n🎧 Available input devices:\n")

    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0:
            inputs.append(i)
            print(f"[{i}] {d['name']} (inputs={d['max_input_channels']})")

    if not inputs:
        print("❌ No input devices found.")
        sys.exit(1)

    while True:
        try:
            choice = int(input("\nSelect device index: "))
            if choice in inputs:
                return choice
            else:
                print("⚠️ Invalid selection.")
        except ValueError:
            print("⚠️ Please enter a number.")


DEVICE_INDEX = select_input_device()
print(f"\n✅ Using device #{DEVICE_INDEX}: {sd.query_devices(DEVICE_INDEX)['name']}")


# ---------- Virtual key ----------
ui = UInput(
    {ecodes.EV_KEY: [ecodes.KEY_PLAYPAUSE]},
    name="headset-quick-hard"
)


# ---------- Calibration ----------
print("\n🎚️ Calibrating background noise...")
print("➡️  Do NOT press the headset button.")

cal = []

def cal_cb(indata, frames, t, status):
    cal.append(np.mean(np.abs(indata[:, 0].astype(int))))

with sd.InputStream(
    device=DEVICE_INDEX,
    samplerate=RATE,
    channels=1,
    dtype="int16",
    blocksize=BLOCKSIZE,
    callback=cal_cb,
    latency="low"
):
    time.sleep(CALIBRATE_SECONDS)

baseline_abs = float(np.median(cal))
sigma_abs = float(np.std(cal))
auto_thr = max(
    MIN_ABS_THRESHOLD,
    baseline_abs + REL_FACTOR * max(1.0, sigma_abs)
)

print("✅ Calibration done")
print(f"   baseline_abs = {int(baseline_abs)}")
print(f"   sigma_abs    = {int(sigma_abs)}")
print(f"   auto_thr     = {int(auto_thr)}")


# ---------- Runtime state ----------
events = deque()
last_fire = 0
suppress_until = 0


def emit():
    print("🎵 PLAY/PAUSE")
    ui.write(ecodes.EV_KEY, ecodes.KEY_PLAYPAUSE, 1)
    ui.syn()
    time.sleep(PRESS_DELAY)
    ui.write(ecodes.EV_KEY, ecodes.KEY_PLAYPAUSE, 0)
    ui.syn()


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

        print(
            time.strftime("[%H:%M:%S]"),
            "TRIG",
            "mean_abs", int(mean_abs),
            "max", maxabs
        )


# ---------- Main loop ----------
print("\n🎧 Listening...")
print("➡️  Press headset button to trigger play/pause")
print("➡️  Ctrl+C to exit\n")

try:
    with sd.InputStream(
        device=DEVICE_INDEX,
        samplerate=RATE,
        channels=1,
        dtype="int16",
        blocksize=BLOCKSIZE,
        callback=cb,
        latency="low"
    ):
        while True:
            time.sleep(0.2)

except KeyboardInterrupt:
    print("\n🛑 Stopped by user")

finally:
    ui.close()
