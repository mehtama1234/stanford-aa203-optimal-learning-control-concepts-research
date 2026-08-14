#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lecture", type=int, action="append", help="download only this lecture number; may be repeated")
    parser.add_argument("--only-missing", action="store_true", help="only retry lectures missing from transcript-index.json")
    parser.add_argument("--skip-playlist-refresh", action="store_true", help="reuse the existing playlist metadata file")
    return parser.parse_args()


def load_existing_records() -> dict[int, dict[str, Any]]:
    if not INDEX.exists():
        return {}
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    return {int(row["lecture"]): row for row in data.get("records", [])}


def record_from_local_vtt(video: dict[str, Any], slug: str, url: str) -> dict[str, Any] | None:
    candidates = sorted(RAW_VTT.glob(f"{slug}*.vtt"))
    if not candidates:
        return None
    raw_path = candidates[0]
    clean_text = clean_vtt(raw_path.read_text(encoding="utf-8", errors="ignore"))
    clean_path = CLEAN / f"{slug}.txt"
    clean_path.write_text(clean_text, encoding="utf-8")
    return {
        "lecture": video["lecture"],
        "video_id": video["id"],
        "title": video["title"],
        "url": url,
        "transcript_available": True,
        "raw_vtt": str(raw_path.relative_to(ROOT)),
        "clean_text": str(clean_path.relative_to(ROOT)),
        "word_count": word_count(clean_text),
    }


def main() -> int:
    args = parse_args()
    manifest: dict[str, Any] = json.loads(MANIFEST.read_text(encoding="utf-8"))
    existing = load_existing_records()
    requested_lectures = set(args.lecture or [])
    RAW_VTT.mkdir(parents=True, exist_ok=True)
    CLEAN.mkdir(parents=True, exist_ok=True)

    if not args.skip_playlist_refresh:
        playlist = run(["yt-dlp", "--flat-playlist", "--dump-single-json", manifest["playlist_url"]])
        PLAYLIST_JSON.write_text(playlist, encoding="utf-8")

    rows: list[dict[str, Any]] = []
    for video in manifest["videos"]:
        video_id = video["id"]
        lecture = int(video["lecture"])
        slug = f"lecture-{video['lecture']:02d}-{video_id}"
        url = f"https://www.youtube.com/watch?v={video_id}"
        existing_row = existing.get(lecture)
        if requested_lectures and lecture not in requested_lectures:
            if existing_row:
                rows.append(existing_row)
                continue
        if args.only_missing and existing_row and existing_row.get("transcript_available"):
            rows.append(existing_row)
            continue
        local_row = record_from_local_vtt(video, slug, url)
        if local_row and not requested_lectures and not args.only_missing:
            rows.append(local_row)
            continue
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
            retry_local_row = record_from_local_vtt(video, slug, url)
            if retry_local_row:
                rows.append(retry_local_row)
            elif existing_row and existing_row.get("transcript_available"):
                rows.append(existing_row)
            else:
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
        downloaded_row = record_from_local_vtt(video, slug, url)
        if not downloaded_row:
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
        rows.append(downloaded_row)

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
