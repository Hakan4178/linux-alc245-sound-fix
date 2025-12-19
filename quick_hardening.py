# quick_hardening.py — hızlı alternatif (konservatif)
#!/usr/bin/env python3
import time, numpy as np, sounddevice as sd
from evdev import UInput, ecodes
from collections import deque

DEVICE="hw:2,0"
RATE=48000
BLOCKSIZE=128
CALIBRATE_SECONDS=1.9

WINDOW_MS=120
MIN_BURST_BLOCKS=6
REL_FACTOR=13
MIN_ABS_THRESHOLD=9500
RELEASE_FACTOR=0.35
RELEASE_STABLE_MS=120

SUPPRESS_MS=400
PRESS_DELAY=0.04

ui = UInput({ecodes.EV_KEY:[ecodes.KEY_PLAYPAUSE]}, name="headset-quick-hard")

# calibration
cal=[]
def cal_cb(indata, frames, t, status):
    cal.append(np.mean(np.abs(indata[:,0].astype(int))))
with sd.InputStream(device=DEVICE, samplerate=RATE, channels=1,
                    dtype='int16', blocksize=BLOCKSIZE, callback=cal_cb, latency='low'):
    time.sleep(CALIBRATE_SECONDS)

baseline_abs = float(__import__('numpy').median(cal))
sigma_abs = float(__import__('numpy').std(cal))
auto_thr = max(MIN_ABS_THRESHOLD, baseline_abs + REL_FACTOR * max(1.0, sigma_abs))

print("baseline_abs",baseline_abs,"sigma_abs",sigma_abs,"auto_thr",auto_thr)

# minimal state
events=deque(); last_fire=0; suppress_until=0

def emit():
    ui.write(ecodes.EV_KEY, ecodes.KEY_PLAYPAUSE, 1); ui.syn(); time.sleep(PRESS_DELAY)
    ui.write(ecodes.EV_KEY, ecodes.KEY_PLAYPAUSE, 0); ui.syn()

def cb(indata, frames, t, status):
    global last_fire, suppress_until
    block = indata[:,0].astype(int)
    mean_abs = float((abs(block)).mean())
    maxabs = int((abs(block)).max())
    now=time.monotonic()
    if mean_abs > auto_thr or maxabs > 32000:
        events.append(now)
    while events and (now-events[0])*1000.0 > WINDOW_MS:
        events.popleft()
    if now < suppress_until:
        return
    if len(events) >= MIN_BURST_BLOCKS and (now-last_fire)>0.25:
        emit()
        last_fire = now
        suppress_until = now + (SUPPRESS_MS/1000.0)
        events.clear()
        print(time.strftime("[%H:%M:%S]"),"TRIG mean_abs",int(mean_abs),"max",maxabs,"events",len(events))

try:
    with sd.InputStream(device=DEVICE, samplerate=RATE, channels=1, dtype='int16',
                        blocksize=BLOCKSIZE, callback=cb, latency='low'):
        while True: time.sleep(0.2)
except KeyboardInterrupt:
    pass
finally:
    ui.close()
