#!/usr/bin/env python3
"""Generate the prayer-alert bells (stdlib only): python3 make.py

adhan.wav  rising A4 C#5 E5 A5, the last one left to ring   (~2.6s)
iqama.wav  E5 then A4, a falling "stand up" cue             (~1.9s)

Bell timbre: inharmonic partials with per-partial exponential decay plus a
short bright strike, so it carries across a room without being harsh.
"""
import math
import struct
import wave
from pathlib import Path

RATE = 44100
# (ratio to fundamental, amplitude, decay time constant in s)
PARTIALS = [(0.5, 0.18, 1.6), (1.0, 1.0, 1.2), (2.0, 0.55, 0.8),
            (2.76, 0.35, 0.5), (5.4, 0.18, 0.25), (8.93, 0.10, 0.12)]


def bell(freq, dur):
    n = int(dur * RATE)
    out = [0.0] * n
    for ratio, amp, tau in PARTIALS:
        f = freq * ratio
        if f > RATE / 2:
            continue
        w = 2 * math.pi * f / RATE
        for i in range(n):
            t = i / RATE
            out[i] += amp * math.exp(-t / tau) * math.sin(w * i)
    attack = int(0.004 * RATE)  # 4ms fade-in, no click
    for i in range(attack):
        out[i] *= i / attack
    return out


def render(notes, total, name):
    buf = [0.0] * int(total * RATE)
    for start, freq, dur in notes:
        s = bell(freq, dur)
        o = int(start * RATE)
        for i, v in enumerate(s):
            if o + i < len(buf):
                buf[o + i] += v
    tail = int(0.25 * RATE)  # fade the last 250ms to silence
    for i in range(tail):
        buf[-tail + i] *= 1 - i / tail
    peak = max(abs(v) for v in buf) or 1
    gain = 0.89 / peak  # about -1 dBFS
    path = Path(__file__).with_name(name)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(v * gain * 32767)) for v in buf))
    print(path)


A4, CS5, E5, A5 = 440.0, 554.37, 659.26, 880.0
render([(0.00, A4, 1.2), (0.22, CS5, 1.2), (0.44, E5, 1.4), (0.70, A5, 1.9)], 2.6, "adhan.wav")
render([(0.00, E5, 1.3), (0.40, A4, 1.5)], 1.9, "iqama.wav")
