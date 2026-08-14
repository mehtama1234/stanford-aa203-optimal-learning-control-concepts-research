#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urldefrag

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw-material/youtube"
SITE = ROOT / "site"


def main() -> int:
    errors: list[str] = []
    manifest_path = RAW / "course-manifest.json"
    index_path = RAW / "transcript-index.json"
    if not manifest_path.exists():
        errors.append("missing raw-material/youtube/course-manifest.json")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if len(manifest.get("videos", [])) != 19:
            errors.append("course manifest should contain 19 videos")
    if not index_path.exists():
        errors.append("missing raw-material/youtube/transcript-index.json; run downloader")
    else:
        index = json.loads(index_path.read_text(encoding="utf-8"))
        if index.get("videos") != 19:
            errors.append("transcript index should report 19 videos")
        for row in index.get("records", []):
            if row.get("transcript_available"):
                path = ROOT / row.get("clean_text", "")
                if not path.exists():
                    errors.append(f"missing clean transcript: {row.get('clean_text')}")
    required_pages = [
        SITE / "index.html",
        SITE / "lectures.html",
        SITE / "transcripts.html",
        SITE / "concept-seed.html",
        SITE / "provenance.html",
        SITE / "assets/styles.css",
    ]
    for path in required_pages:
        if not path.exists():
            errors.append(f"missing site artifact: {path.relative_to(ROOT)}")
    for path in SITE.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if "<main>" not in text or "</main>" not in text:
            errors.append(f"missing main element: {path.relative_to(ROOT)}")
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            href_path, frag = urldefrag(href)
            target = (path.parent / href_path).resolve() if href_path else path.resolve()
            try:
                target.relative_to(SITE.resolve())
            except ValueError:
                errors.append(f"link escapes site: {path.relative_to(ROOT)} -> {href}")
                continue
            if href_path and not target.exists():
                errors.append(f"broken link: {path.relative_to(ROOT)} -> {href}")
            if frag and target.exists() and f'id="{frag}"' not in target.read_text(encoding="utf-8"):
                errors.append(f"missing anchor: {path.relative_to(ROOT)} -> {href}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

