import json
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, "/workspace/.asr-deps")

import numpy as np
import sherpa_onnx

ROOT = pathlib.Path(__file__).resolve().parent
MODEL = pathlib.Path("/workspace/models/sherpa-onnx-whisper-small")
SOURCE = ROOT / "narration.wav"

recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
    encoder=str(MODEL / "small-encoder.int8.onnx"),
    decoder=str(MODEL / "small-decoder.int8.onnx"),
    tokens=str(MODEL / "small-tokens.txt"),
    language="pt",
    task="transcribe",
    num_threads=4,
    enable_token_timestamps=True,
    enable_segment_timestamps=True,
)

audio = np.frombuffer(
    subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(SOURCE),
            "-vn",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-f",
            "f32le",
            "-",
        ]
    ),
    np.float32,
)

stream = recognizer.create_stream()
stream.accept_waveform(16000, audio)
started = time.time()
recognizer.decode_stream(stream)
result = json.loads(str(stream.result))
result.update(
    {
        "duration": len(audio) / 16000,
        "elapsed": time.time() - started,
        "engine": "Sherpa-ONNX 2.0.1 / Whisper small multilingual int8",
        "language": "pt",
    }
)
(ROOT / "transcript-raw.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(result, ensure_ascii=False, indent=2))
