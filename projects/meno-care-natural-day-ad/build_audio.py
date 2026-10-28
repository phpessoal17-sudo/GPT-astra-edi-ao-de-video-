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
    peak = max(1.0, float(np.max(np.abs(stereo))) / 0.93)
    pcm = np.clip(stereo / peak, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(pcm.tobytes())


music = np.zeros((SAMPLES, 2), dtype=np.float64)
sfx = np.zeros((SAMPLES, 2), dtype=np.float64)

# Harmonia em Ré menor, abrindo para Fá maior no CTA: editorial e acolhedora.
chords = [
    (0.0, 7.0, (146.83, 174.61, 220.00)),
    (7.0, 11.8, (116.54, 146.83, 174.61)),
    (11.8, 18.1, (130.81, 164.81, 196.00)),
    (18.1, 24.2, (146.83, 174.61, 220.00)),
    (24.2, 30.0, (174.61, 220.00, 261.63)),
]

for start, end, freqs in chords:
    mask = (T >= start) & (T < end)
    local = T[mask] - start
    length = end - start
    env = smoothstep(local / 0.9) * smoothstep((length - local) / 1.0)
    left = np.zeros_like(local)
    right = np.zeros_like(local)
    for i, freq in enumerate(freqs):
        phase = 2 * np.pi * freq * local
        left += np.sin(phase + i * 0.42) + 0.18 * np.sin(phase * 2.01)
        right += np.sin(phase * 1.0006 - i * 0.31) + 0.18 * np.sin(phase * 2.008)
    music[mask] += 0.044 * env[:, None] * np.column_stack((left, right))

# Pulso orgânico e plucks de vidro.
for beat_index, beat in enumerate(np.arange(0.35, DURATION, 0.72)):
    n = int(0.30 * SR)
    tt = np.arange(n) / SR
    env = np.exp(-tt * 13.5) * smoothstep(tt / 0.014)
    pulse = 0.042 * env * (np.sin(2 * np.pi * 92 * tt) + 0.30 * np.sin(2 * np.pi * 184 * tt))
    place(music, stereo_pan(pulse, -0.16 if beat_index % 2 == 0 else 0.16), beat)

for at, freq, pan in [
    (3.0, 698.46, -0.18), (7.0, 783.99, 0.22), (11.8, 880.0, -0.12),
    (14.2, 1046.5, 0.20), (18.1, 987.77, -0.20), (24.2, 1174.66, 0.15),
    (27.2, 1396.91, 0.0),
]:
    n = int(1.35 * SR)
    tt = np.arange(n) / SR
    env = np.exp(-tt * 3.4) * smoothstep(tt / 0.018)
    pluck = 0.046 * env * (
        np.sin(2 * np.pi * freq * tt)
        + 0.26 * np.sin(2 * np.pi * freq * 2.005 * tt)
        + 0.10 * np.sin(2 * np.pi * freq * 3.01 * tt)
    )
    place(music, stereo_pan(pluck, pan), at)

# Ar filtrado: textura contínua de baixo custo e sem licença externa.
air = RNG.normal(0.0, 1.0, SAMPLES)
air = np.convolve(air, np.ones(64) / 64.0, mode="same")
air *= 0.0058 * (0.25 + 0.75 * smoothstep(T / 3.0))
music += stereo_pan(air, 0.0)

# Transições narrativas e feedback dos dados.
for cue_index, cue_at in enumerate([3.0, 7.0, 11.8, 18.1, 24.2]):
    n = int(0.78 * SR)
    tt = np.arange(n) / SR
    noise = RNG.normal(0.0, 1.0, n)
    noise = np.convolve(noise, np.ones(20) / 20.0, mode="same")
    env = np.sin(np.pi * np.clip(tt / 0.78, 0.0, 1.0)) ** 1.6
    sweep = np.sin(2 * np.pi * (120 * tt + 820 * tt * tt))
    whoosh = 0.115 * env * (0.66 * noise + 0.34 * sweep)
    place(sfx, stereo_pan(whoosh, -0.32 if cue_index % 2 == 0 else 0.32), cue_at - 0.38)

    impact_n = int(0.42 * SR)
    impact_t = np.arange(impact_n) / SR
    impact = 0.15 * np.exp(-impact_t * 12.0) * (
        np.sin(2 * np.pi * 67 * impact_t) + 0.35 * np.sin(2 * np.pi * 134 * impact_t)
    )
    place(sfx, stereo_pan(impact, 0.0), cue_at)

for cue_at in [12.9, 13.8, 14.7, 15.6, 19.2, 20.2, 21.2]:
    n = int(0.22 * SR)
    tt = np.arange(n) / SR
    click = 0.095 * np.exp(-tt * 20.0) * (
        np.sin(2 * np.pi * 560 * tt) + 0.33 * np.sin(2 * np.pi * 1120 * tt)
    )
    place(sfx, stereo_pan(click, -0.22 + 0.44 * ((int(cue_at * 10)) % 2)), cue_at)

n = int(1.65 * SR)
tt = np.arange(n) / SR
chime = 0.105 * np.exp(-tt * 2.7) * (
    np.sin(2 * np.pi * 1046.5 * tt)
    + 0.52 * np.sin(2 * np.pi * 1318.5 * tt)
    + 0.28 * np.sin(2 * np.pi * 1568.0 * tt)
)
place(sfx, stereo_pan(chime, 0.0), 27.0)

write_wav(OUT / "underscore.wav", music)
write_wav(OUT / "sfx.wav", sfx)
print(f"Wrote {OUT / 'underscore.wav'} and {OUT / 'sfx.wav'}")
