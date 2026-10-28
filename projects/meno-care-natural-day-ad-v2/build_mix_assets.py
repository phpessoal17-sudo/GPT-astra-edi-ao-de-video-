import pathlib
import wave

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent
SR = 48_000
DURATION = 30.0
N = int(SR * DURATION)


def read(path):
    with wave.open(str(path), "rb") as h:
        if h.getframerate() != SR or h.getnchannels() != 2 or h.getsampwidth() != 2:
            raise ValueError(f"Unsupported WAV: {path}")
        return np.frombuffer(h.readframes(h.getnframes()), dtype="<i2").reshape(-1, 2) / 32768.0


def place(bus, clip, at, gain=1.0):
    start = int(at * SR)
    end = min(N, start + len(clip))
    if end > start:
        bus[start:end] += clip[:end-start] * gain


bus = np.zeros((N, 2), dtype=np.float64)
cues = [
    (0.05, "impact_soft.wav", .72),
    (2.12, "page_swipe.wav", .72),
    (4.38, "focus_bloom.wav", .62),
    (6.76, "transition_iris.wav", .76),
    (9.36, "sparkle_cluster.wav", .52),
    (11.78, "data_pop.wav", .82),
    (14.08, "impact_soft.wav", .68),
    (16.38, "click_glass.wav", .72),
    (17.08, "click_glass.wav", .64),
    (17.78, "click_glass.wav", .58),
    (18.76, "tick_soft.wav", .76),
    (19.46, "tick_soft.wav", .70),
    (21.24, "whoosh_soft_air.wav", .62),
    (24.36, "downlifter_warm.wav", .58),
    (26.76, "impact_cinematic.wav", .58),
    (27.10, "confirm_chime.wav", .62),
]
for at, name, gain in cues:
    place(bus, read(ROOT / "audio" / name), at, gain)

peak = max(1.0, float(np.max(np.abs(bus))) / .92)
pcm = (np.clip(bus / peak, -1, 1) * 32767).astype("<i2")
with wave.open(str(ROOT / "audio" / "sfx-timeline.wav"), "wb") as h:
    h.setnchannels(2); h.setsampwidth(2); h.setframerate(SR); h.writeframes(pcm.tobytes())
print("Wrote audio/sfx-timeline.wav")
