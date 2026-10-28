"""Gera uma biblioteca audiovisual original, determinística e sem samples externos."""

from __future__ import annotations

import json
import math
import pathlib
import wave

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "library" / "audio"
SFX = OUT / "sfx"
MUSIC = OUT / "music"
SFX.mkdir(parents=True, exist_ok=True)
MUSIC.mkdir(parents=True, exist_ok=True)

SR = 48_000
RNG = np.random.default_rng(20261028)


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def pan(mono, position=0.0):
    angle = (position + 1.0) * math.pi / 4.0
    return np.column_stack((mono * math.cos(angle), mono * math.sin(angle)))


def soften(signal, size=24):
    return np.convolve(signal, np.ones(size) / size, mode="same")


def write(path, stereo, ceiling=0.92):
    peak = max(float(np.max(np.abs(stereo))), 1e-9)
    stereo = stereo * min(1.0, ceiling / peak)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(pcm.tobytes())


def noise_sweep(duration, start_hz, end_hz, intensity=0.5, reverse=False):
    n = int(duration * SR)
    t = np.arange(n) / SR
    progress = t / duration
    env = np.sin(np.pi * progress) ** 1.6
    if reverse:
        env = smoothstep((duration - t) / duration) * np.exp(-t * 2.0)
    noise = soften(RNG.normal(0, 1, n), 22)
    freq = start_hz + (end_hz - start_hz) * progress
    phase = 2 * np.pi * np.cumsum(freq) / SR
    tonal = np.sin(phase) + 0.25 * np.sin(phase * 2.01)
    return intensity * env * (0.68 * noise + 0.32 * tonal)


def impact(duration=1.1, fundamental=62, soft=False):
    n = int(duration * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * (7.5 if soft else 5.2)) * smoothstep(t / 0.009)
    low = np.sin(2 * np.pi * fundamental * t) + 0.38 * np.sin(2 * np.pi * fundamental * 2 * t)
    crack = soften(RNG.normal(0, 1, n), 7) * np.exp(-t * 18)
    return (0.32 if soft else 0.55) * env * low + (0.08 if soft else 0.18) * crack


def chime(duration, notes, decay=3.0):
    n = int(duration * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for index, freq in enumerate(notes):
        delay = int(index * 0.075 * SR)
        local = t[: n - delay]
        env = np.exp(-local * decay) * smoothstep(local / 0.008)
        tone = np.sin(2 * np.pi * freq * local) + 0.24 * np.sin(2 * np.pi * freq * 2.005 * local)
        out[delay:] += 0.28 * env * tone
    return out


def make_sfx():
    items = []

    def add(name, mono, category, mood, use, stereo=None):
        data = stereo if stereo is not None else pan(mono)
        path = SFX / f"{name}.wav"
        write(path, data)
        items.append({
            "id": name,
            "path": str(path.relative_to(ROOT)),
            "category": category,
            "mood": mood,
            "duration": round(len(data) / SR, 3),
            "recommended_use": use,
        })

    add("whoosh_soft_air", noise_sweep(.78, 160, 1450, .58), "transition", "soft", "focus pull e troca premium", pan(noise_sweep(.78, 160, 1450, .58), -.28))
    add("whoosh_fast_tonal", noise_sweep(.34, 260, 2400, .66), "transition", "fast", "troca rápida ou card")
    add("riser_glass", noise_sweep(1.8, 180, 2900, .48), "riser", "luminous", "antecipar revelação")
    add("downlifter_warm", noise_sweep(1.1, 1700, 120, .52, reverse=True), "downlifter", "warm", "encerrar bloco")
    add("impact_cinematic", impact(1.25, 58, False), "impact", "cinematic", "revelação principal")
    add("impact_soft", impact(.72, 86, True), "impact", "soft", "mudança informativa")

    n = int(1.45 * SR); t = np.arange(n) / SR
    sub = .62 * np.exp(-t * 2.5) * np.sin(2 * np.pi * (86 * t - 21 * t * t))
    add("sub_drop", sub, "sub", "heavy", "dar peso sem cobrir a voz")

    n = int(.22 * SR); t = np.arange(n) / SR
    click = .42 * np.exp(-t * 22) * (np.sin(2*np.pi*680*t) + .30*np.sin(2*np.pi*1360*t))
    add("click_glass", click, "ui", "clean", "chips, números e checklists")

    n = int(.12 * SR); t = np.arange(n) / SR
    tick = .32 * np.exp(-t * 34) * np.sin(2*np.pi*420*t)
    add("tick_soft", tick, "ui", "soft", "microinteração")
    add("confirm_chime", chime(1.25, [783.99, 987.77, 1174.66], 3.1), "confirmation", "positive", "CTA e confirmação")
    add("sparkle_cluster", chime(1.45, [1046.5, 1318.5, 1568.0, 2093.0], 3.8), "sparkle", "bright", "produto e brilho")

    swipe = noise_sweep(.62, 900, 260, .48)
    add("page_swipe", swipe, "transition", "editorial", "virada de página", stereo=pan(swipe, .35))
    bloom = noise_sweep(1.0, 120, 1250, .38) + chime(1.0, [523.25, 783.99], 2.7)
    add("focus_bloom", bloom, "transition", "premium", "foco e luz")
    data = chime(.35, [523.25, 784.0], 9.0)
    add("data_pop", data, "ui", "confident", "entrada de dado")
    iris = noise_sweep(.82, 220, 1800, .44) + .22 * impact(.82, 98, True)
    add("transition_iris", iris, "transition", "organic", "íris circular")
    return items


def synth_music(name, chords, bpm, palette, pulse_hz):
    duration = 30.0
    n = int(duration * SR)
    t = np.arange(n) / SR
    stereo = np.zeros((n, 2), dtype=np.float64)
    segment = duration / len(chords)
    for ci, freqs in enumerate(chords):
        start = ci * segment; end = (ci + 1) * segment
        mask = (t >= start) & (t < end)
        local = t[mask] - start
        env = smoothstep(local / .8) * smoothstep((segment - local) / .9)
        left = np.zeros_like(local); right = np.zeros_like(local)
        for fi, freq in enumerate(freqs):
            phase = 2 * np.pi * freq * local
            left += np.sin(phase + fi*.37) + .16*np.sin(phase*2.006)
            right += np.sin(phase*1.0006 - fi*.29) + .16*np.sin(phase*2.003)
        stereo[mask] += palette[0] * env[:, None] * np.column_stack((left, right))

    beat = 60 / bpm
    for bi, at in enumerate(np.arange(.15, duration, beat)):
        size = int(.28 * SR); tt = np.arange(size) / SR
        env = np.exp(-tt * 13) * smoothstep(tt / .01)
        mono = palette[1] * env * (np.sin(2*np.pi*pulse_hz*tt) + .25*np.sin(2*np.pi*pulse_hz*2*tt))
        start = int(at * SR); end = min(n, start + size)
        stereo[start:end] += pan(mono[:end-start], -.18 if bi % 2 == 0 else .18)

    for at in np.arange(2.0, duration, segment / 2):
        freq = 660 + 110 * int((at / segment) % 4)
        size = int(1.1 * SR); tt = np.arange(size) / SR
        env = np.exp(-tt * 3.5) * smoothstep(tt / .015)
        mono = palette[2] * env * (np.sin(2*np.pi*freq*tt) + .22*np.sin(2*np.pi*freq*2.01*tt))
        start = int(at * SR); end = min(n, start + size)
        stereo[start:end] += pan(mono[:end-start], .22)

    air = soften(RNG.normal(0, 1, n), 72) * palette[3]
    stereo += pan(air)
    path = MUSIC / f"{name}.wav"
    write(path, stereo, .88)
    return path


def make_music():
    definitions = [
        ("wellness_luxe_30s", [(146.83,174.61,220.0),(116.54,146.83,174.61),(130.81,164.81,196.0),(174.61,220.0,261.63)], 82, (.042,.038,.034,.0048), 92, "warm premium wellness"),
        ("editorial_pulse_30s", [(196.0,246.94,293.66),(220.0,261.63,329.63),(174.61,220.0,261.63),(261.63,329.63,392.0)], 104, (.034,.052,.042,.0042), 112, "modern editorial information"),
        ("cinematic_clarity_30s", [(110.0,164.81,220.0),(98.0,146.83,196.0),(130.81,174.61,261.63),(174.61,220.0,329.63)], 76, (.048,.042,.038,.0052), 74, "cinematic reveal and resolution"),
    ]
    items = []
    for name, chords, bpm, palette, pulse, mood in definitions:
        path = synth_music(name, chords, bpm, palette, pulse)
        items.append({
            "id": name,
            "path": str(path.relative_to(ROOT)),
            "category": "background_music",
            "mood": mood,
            "duration": 30.0,
            "bpm": bpm,
            "recommended_use": "anúncio vertical com voz e ducking",
        })
    return items


def main():
    catalog = {
        "version": "1.1.0",
        "sample_rate": SR,
        "license": "Síntese procedural original, sem samples externos; disponível para os projetos do usuário.",
        "deterministic_seed": 20261028,
        "assets": make_sfx() + make_music(),
    }
    (ROOT / "library" / "audio-catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Generated {len(catalog['assets'])} assets in {OUT}")


if __name__ == "__main__":
    main()
