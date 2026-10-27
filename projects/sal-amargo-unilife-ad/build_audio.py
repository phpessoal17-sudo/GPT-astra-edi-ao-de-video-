import math
import pathlib
import wave

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "audio"
OUT.mkdir(exist_ok=True)

SR = 48_000
DURATION = 30.0
SAMPLES = int(SR * DURATION)
T = np.arange(SAMPLES, dtype=np.float64) / SR
RNG = np.random.default_rng(20261027)


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def stereo_pan(signal, pan):
    angle = (pan + 1.0) * math.pi / 4.0
    return np.column_stack((signal * math.cos(angle), signal * math.sin(angle)))


def place(bus, signal, at):
    start = max(0, int(at * SR))
    end = min(SAMPLES, start + len(signal))
    if end > start:
        bus[start:end] += signal[: end - start]


def write_wav(path, stereo):
    peak = max(1.0, float(np.max(np.abs(stereo))) / 0.92)
    pcm = np.clip(stereo / peak, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(pcm.tobytes())


music = np.zeros((SAMPLES, 2), dtype=np.float64)
sfx = np.zeros((SAMPLES, 2), dtype=np.float64)

# Progressão em Lá menor que se abre para Dó maior no CTA.
chords = [
    (0.0, 5.5, (220.00, 261.63, 329.63)),
    (5.5, 10.1, (174.61, 220.00, 261.63)),
    (10.1, 14.4, (196.00, 246.94, 293.66)),
    (14.4, 21.3, (220.00, 261.63, 329.63)),
    (21.3, 25.6, (174.61, 220.00, 261.63)),
    (25.6, 30.0, (261.63, 329.63, 392.00)),
]

for start, end, freqs in chords:
    mask = (T >= start) & (T < end)
    local = T[mask] - start
    length = end - start
    envelope = smoothstep(local / 1.1) * smoothstep((length - local) / 1.2)
    left = np.zeros_like(local)
    right = np.zeros_like(local)
    for index, freq in enumerate(freqs):
        drift = 0.0018 * np.sin(2 * np.pi * (0.08 + index * 0.013) * local)
        phase = 2 * np.pi * freq * local + drift
        left += np.sin(phase + index * 0.45)
        right += np.sin(phase * 1.0007 - index * 0.38)
        left += 0.24 * np.sin(phase * 2.0 + 0.3)
        right += 0.24 * np.sin(phase * 2.0 - 0.2)
    pad = 0.050 * envelope[:, None] * np.column_stack((left, right))
    music[mask] += pad

# Pulso macio e plucks cristalinos que marcam a estrutura sem competir com a voz.
for beat in np.arange(0.25, DURATION, 0.75):
    n = int(0.32 * SR)
    tt = np.arange(n) / SR
    env = np.exp(-tt * 12.0) * smoothstep(tt / 0.012)
    pulse = 0.038 * env * (np.sin(2 * np.pi * 110 * tt) + 0.35 * np.sin(2 * np.pi * 220 * tt))
    place(music, stereo_pan(pulse, -0.18 if int(beat / 0.75) % 2 == 0 else 0.18), beat)

for note_at, freq in [(5.5, 659.25), (10.12, 783.99), (14.4, 880.0), (21.28, 987.77), (25.64, 1046.5), (27.82, 1318.5)]:
    n = int(1.45 * SR)
    tt = np.arange(n) / SR
    env = np.exp(-tt * 3.3) * smoothstep(tt / 0.018)
    pluck = 0.045 * env * (
        np.sin(2 * np.pi * freq * tt)
        + 0.28 * np.sin(2 * np.pi * freq * 2.01 * tt)
        + 0.12 * np.sin(2 * np.pi * freq * 3.0 * tt)
    )
    place(music, stereo_pan(pluck, 0.18), note_at)

# Ar muito discreto para unir as cenas.
air = RNG.normal(0.0, 1.0, SAMPLES)
kernel = np.ones(48) / 48.0
air = np.convolve(air, kernel, mode="same")
air *= 0.006 * (0.35 + 0.65 * smoothstep(T / 4.0))
music += stereo_pan(air, 0.0)

# Whooshes, impactos e confirmação final.
for cue_index, cue_at in enumerate([2.3, 5.5, 10.12, 14.4, 21.28, 25.64]):
    n = int(0.72 * SR)
    tt = np.arange(n) / SR
    noise = RNG.normal(0.0, 1.0, n)
    noise = np.convolve(noise, np.ones(18) / 18.0, mode="same")
    env = np.sin(np.pi * np.clip(tt / 0.72, 0.0, 1.0)) ** 1.7
    sweep = np.sin(2 * np.pi * (170 * tt + 780 * tt * tt))
    whoosh = 0.12 * env * (0.62 * noise + 0.38 * sweep)
    place(sfx, stereo_pan(whoosh, -0.35 if cue_index % 2 == 0 else 0.35), cue_at - 0.34)

    impact_n = int(0.38 * SR)
    impact_t = np.arange(impact_n) / SR
    impact = 0.16 * np.exp(-impact_t * 13.0) * (
        np.sin(2 * np.pi * 72 * impact_t) + 0.42 * np.sin(2 * np.pi * 144 * impact_t)
    )
    place(sfx, stereo_pan(impact, 0.0), cue_at)

for cue_at in [12.0, 13.15, 14.25, 22.1, 23.0, 23.9]:
    n = int(0.28 * SR)
    tt = np.arange(n) / SR
    click = 0.11 * np.exp(-tt * 18.0) * (
        np.sin(2 * np.pi * 620 * tt) + 0.35 * np.sin(2 * np.pi * 1240 * tt)
    )
    place(sfx, stereo_pan(click, -0.2 + 0.4 * ((cue_at * 10) % 2)), cue_at)

n = int(1.5 * SR)
tt = np.arange(n) / SR
chime = 0.10 * np.exp(-tt * 2.8) * (
    np.sin(2 * np.pi * 1046.5 * tt)
    + 0.55 * np.sin(2 * np.pi * 1318.5 * tt)
    + 0.35 * np.sin(2 * np.pi * 1568.0 * tt)
)
place(sfx, stereo_pan(chime, 0.0), 27.82)

write_wav(OUT / "underscore.wav", music)
write_wav(OUT / "sfx.wav", sfx)
print(f"Wrote {OUT / 'underscore.wav'} and {OUT / 'sfx.wav'}")
