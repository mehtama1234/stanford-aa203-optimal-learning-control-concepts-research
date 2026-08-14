#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw-material/youtube"
MANIFEST = RAW / "course-manifest.json"
PLAYLIST_JSON = RAW / "playlist.json"
TRANSCRIPTS = RAW / "transcripts"
RAW_VTT = TRANSCRIPTS / "raw-vtt"
CLEAN = TRANSCRIPTS / "clean"
INDEX = RAW / "transcript-index.json"


def run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout


def clean_vtt(text: str) -> str:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line == "WEBVTT" or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line or re.fullmatch(r"\d+", line):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = line.replace("&amp;", "&").replace("&nbsp;", " ")
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    deduped: list[str] = []
    for line in lines:
        if not deduped or deduped[-1] != line:
            deduped.append(line)
    return "\n".join(deduped).strip() + "\n"


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def main() -> int:
    manifest: dict[str, Any] = json.loads(MANIFEST.read_text(encoding="utf-8"))
    RAW_VTT.mkdir(parents=True, exist_ok=True)
    CLEAN.mkdir(parents=True, exist_ok=True)

    playlist = run(["yt-dlp", "--flat-playlist", "--dump-single-json", manifest["playlist_url"]])
    PLAYLIST_JSON.write_text(playlist, encoding="utf-8")

    rows: list[dict[str, Any]] = []
    for video in manifest["videos"]:
        video_id = video["id"]
        slug = f"lecture-{video['lecture']:02d}-{video_id}"
        url = f"https://www.youtube.com/watch?v={video_id}"
        before = set(RAW_VTT.glob(f"{slug}*.vtt"))
        try:
            run(
                [
                    "yt-dlp",
                    "--skip-download",
                    "--write-subs",
                    "--write-auto-subs",
                    "--sub-langs",
                    "en.*",
                    "--sub-format",
                    "vtt",
                    "-o",
                    str(RAW_VTT / f"{slug}.%(ext)s"),
                    url,
                ]
            )
        except subprocess.CalledProcessError as exc:
            rows.append(
                {
                    "lecture": video["lecture"],
                    "video_id": video_id,
                    "title": video["title"],
                    "url": url,
                    "transcript_available": False,
                    "error": exc.stdout.strip()[-500:],
                }
            )
            continue
        candidates = sorted(set(RAW_VTT.glob(f"{slug}*.vtt")) | before)
        if not candidates:
            rows.append(
                {
                    "lecture": video["lecture"],
                    "video_id": video_id,
                    "title": video["title"],
                    "url": url,
                    "transcript_available": False,
                    "error": "no VTT file downloaded",
                }
            )
            continue
        raw_path = candidates[0]
        clean_text = clean_vtt(raw_path.read_text(encoding="utf-8", errors="ignore"))
        clean_path = CLEAN / f"{slug}.txt"
        clean_path.write_text(clean_text, encoding="utf-8")
        rows.append(
            {
                "lecture": video["lecture"],
                "video_id": video_id,
                "title": video["title"],
                "url": url,
                "transcript_available": True,
                "raw_vtt": str(raw_path.relative_to(ROOT)),
                "clean_text": str(clean_path.relative_to(ROOT)),
                "word_count": word_count(clean_text),
            }
        )

    summary = {
        "course": manifest["title"],
        "playlist_url": manifest["playlist_url"],
        "videos": len(manifest["videos"]),
        "available_transcripts": sum(1 for row in rows if row.get("transcript_available")),
        "total_transcript_words": sum(row.get("word_count", 0) for row in rows),
        "records": rows,
    }
    INDEX.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        f"indexed {summary['available_transcripts']}/{summary['videos']} transcripts "
        f"with {summary['total_transcript_words']} words"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

