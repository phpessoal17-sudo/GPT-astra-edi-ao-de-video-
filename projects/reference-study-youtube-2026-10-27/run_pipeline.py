import json
import os
import pathlib
import re
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parent
SOURCES = ROOT / "sources"
ANALYSIS = ROOT / "analysis"
TRANSCRIPTS = ROOT / "transcripts"
YTDLP_DEPS = pathlib.Path("/workspace/.yt-dlp-deps")

for directory in (SOURCES, ANALYSIS, TRANSCRIPTS):
    directory.mkdir(parents=True, exist_ok=True)


def run(command, *, capture=False, check=True, env=None):
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=check,
        env=env,
    )
    return completed.stdout if capture else ""


def ffprobe(path):
    return json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                str(path),
            ],
            capture=True,
        )
    )


def media_for(video_id):
    candidates = []
    for extension in ("mp4", "mkv", "webm", "mov"):
        candidates.extend(SOURCES.glob(f"{video_id}.{extension}"))
    if not candidates:
        raise FileNotFoundError(f"Mídia não encontrada para {video_id}")
    return max(candidates, key=lambda item: item.stat().st_size)


def detect_scene_times(log_text):
    times = []
    for match in re.finditer(r"pts_time:([0-9]+(?:\.[0-9]+)?)", log_text):
        value = round(float(match.group(1)), 3)
        if not times or value - times[-1] >= 0.18:
            times.append(value)
    return times


manifest = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
urls = [entry["url"] for entry in manifest["sources"]]

download_env = os.environ.copy()
download_env["PYTHONPATH"] = str(YTDLP_DEPS)

run(
    [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "--write-info-json",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs",
        "pt.*,en.*",
        "--sub-format",
        "vtt",
        "-f",
        "bv*[height<=1080]+ba/b[height<=1080]",
        "--merge-output-format",
        "mp4",
        "-o",
        str(SOURCES / "%(id)s.%(ext)s"),
        *urls,
    ],
    env=download_env,
)

summary = []
for entry in manifest["sources"]:
    video_id = entry["id"]
    media = media_for(video_id)
    item_dir = ANALYSIS / video_id
    item_dir.mkdir(exist_ok=True)

    probe = ffprobe(media)
    (item_dir / "ffprobe.json").write_text(
        json.dumps(probe, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    duration = float(probe["format"]["duration"])

    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "warning",
            "-i",
            str(media),
            "-vf",
            f"fps=12/{duration},scale=360:-1,tile=4x3:padding=8:margin=8",
            "-frames:v",
            "1",
            str(item_dir / "contact-sheet.jpg"),
        ]
    )

    scene_log = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(media),
            "-filter:v",
            "select='gt(scene,0.22)',showinfo",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture=True,
        check=False,
    )
    (item_dir / "scene-detection.log").write_text(scene_log, encoding="utf-8")
    scene_times = detect_scene_times(scene_log)
    (item_dir / "scene-times.json").write_text(
        json.dumps(scene_times, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    audio_log = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(media),
            "-map",
            "0:a:0?",
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json",
            "-f",
            "null",
            "-",
        ],
        capture=True,
        check=False,
    )
    (item_dir / "audio-analysis.log").write_text(audio_log, encoding="utf-8")

    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(media),
            "-vn",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(TRANSCRIPTS / f"{video_id}.wav"),
        ]
    )

    subtitle_files = sorted(SOURCES.glob(f"{video_id}*.vtt"))
    summary.append(
        {
            "id": video_id,
            "url": entry["url"],
            "media": str(media.relative_to(ROOT)),
            "duration": duration,
            "scene_count_threshold_0_22": len(scene_times),
            "mean_detected_shot_seconds": (
                round(duration / (len(scene_times) + 1), 3) if duration else None
            ),
            "subtitles": [str(path.relative_to(ROOT)) for path in subtitle_files],
        }
    )

(ANALYSIS / "technical-summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
