#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
RAW = ROOT / "raw-material/youtube"


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return value.strip("-")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(line.rstrip() for line in content.splitlines()) + "\n", encoding="utf-8")


def page(title: str, body: str, active: str = "") -> str:
    nav = [
        ("index.html", "Overview", "overview"),
        ("lectures.html", "Lectures", "lectures"),
        ("transcripts.html", "Transcripts", "transcripts"),
        ("concept-seed.html", "Concept Seed", "concepts"),
        ("provenance.html", "Provenance", "provenance"),
    ]
    links = "\n".join(
        f'<a class="{"active" if key == active else ""}" href="{href}">{label}</a>' for href, label, key in nav
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} · Stanford AA203 Control Lab</title>
  <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="index.html">Stanford AA203 Control Lab</a>
    <nav>{links}</nav>
  </header>
  <main>{body}</main>
</body>
</html>
"""


def main() -> int:
    manifest = json.loads((RAW / "course-manifest.json").read_text(encoding="utf-8"))
    index_path = RAW / "transcript-index.json"
    transcript_index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {
        "available_transcripts": 0,
        "videos": len(manifest["videos"]),
        "total_transcript_words": 0,
        "records": [],
    }
    records = transcript_index.get("records", [])
    by_video = {row["video_id"]: row for row in records}

    write(
        SITE / "assets/styles.css",
        """
:root {
  color-scheme: light;
  --ink: #17202a;
  --muted: #5b6773;
  --line: #d9e0e7;
  --paper: #ffffff;
  --wash: #f4f7f9;
  --accent: #0b6b64;
  --accent-2: #8b3f18;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--ink);
  background: var(--wash);
  line-height: 1.55;
}
.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  gap: 24px;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  border-bottom: 1px solid var(--line);
  background: rgba(255,255,255,.96);
}
.brand { color: var(--ink); font-weight: 760; text-decoration: none; }
nav { display: flex; flex-wrap: wrap; gap: 10px; }
nav a { color: var(--muted); text-decoration: none; font-size: 14px; }
nav a.active, nav a:hover { color: var(--accent); }
main { max-width: 1120px; margin: 0 auto; padding: 36px 24px 64px; }
.hero {
  display: grid;
  gap: 18px;
  padding: 28px 0 24px;
  border-bottom: 1px solid var(--line);
}
h1 { max-width: 900px; margin: 0; font-size: clamp(34px, 5vw, 64px); line-height: 1; letter-spacing: 0; }
h2 { margin-top: 36px; font-size: 26px; letter-spacing: 0; }
h3 { margin-bottom: 6px; font-size: 18px; letter-spacing: 0; }
p { max-width: 820px; }
.lede { max-width: 860px; color: var(--muted); font-size: 19px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin: 18px 0; }
.stat, .card {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
  padding: 16px;
}
.stat strong { display: block; font-size: 30px; color: var(--accent); line-height: 1.1; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }
.lecture-list { display: grid; gap: 10px; }
.lecture-row {
  display: grid;
  grid-template-columns: 72px 1fr auto;
  gap: 14px;
  align-items: start;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
}
.tag { color: var(--accent-2); font-size: 13px; font-weight: 700; text-transform: uppercase; }
.muted { color: var(--muted); }
code { background: #eef3f4; padding: 2px 5px; border-radius: 4px; }
@media (max-width: 720px) {
  .topbar { align-items: flex-start; flex-direction: column; }
  .lecture-row { grid-template-columns: 1fr; }
}
""",
    )

    stats = f"""
<section class="stats">
  <div class="stat"><strong>{len(manifest['videos'])}</strong><span>playlist lectures</span></div>
  <div class="stat"><strong>{transcript_index.get('available_transcripts', 0)}</strong><span>local transcripts</span></div>
  <div class="stat"><strong>{transcript_index.get('total_transcript_words', 0):,}</strong><span>transcript words</span></div>
</section>
"""
    spine_cards = [
        ("Optimization", "Choose actions by naming an objective, constraints, and a way to improve the candidate."),
        ("Dynamics", "Respect that today&apos;s action changes tomorrow&apos;s state, so decisions are chained through time."),
        ("Value", "Compress future consequences into a quantity that lets the next decision be compared."),
        ("Feasibility", "Keep planned actions inside real constraints, especially when replanning with MPC."),
        ("Learning", "Use data, demonstrations, or reward feedback when a hand-written model is incomplete."),
    ]
    cards = "\n".join(f"<article class=\"card\"><h3>{name}</h3><p>{text}</p></article>" for name, text in spine_cards)
    write(
        SITE / "index.html",
        page(
            "Overview",
            f"""
<section class="hero">
  <p class="tag">Transcript-backed first-principles starter</p>
  <h1>{esc(manifest['title'])}</h1>
  <p class="lede">This repo turns the AA203 playlist into a control-course research workspace. The first build preserves source material and creates a browsable shell; the next build should deepen the concept atlas, evidence ledger, derivations, drills, and failure-mode pages.</p>
  {stats}
</section>
<h2>Course Throughline</h2>
<p>Optimal and learning-based control studies how to choose actions over time when a system moves, constraints matter, and the future depends on earlier choices. The course starts with optimization and path methods, then moves through dynamic programming, reachability, MPC, imitation learning, reinforcement learning, and model-based RL.</p>
<section class="grid">{cards}</section>
""",
            "overview",
        ),
    )

    lecture_rows = []
    transcript_rows = []
    for video in manifest["videos"]:
        rec = by_video.get(video["id"], {})
        available = bool(rec.get("transcript_available"))
        words = rec.get("word_count", 0)
        label = "transcript captured" if available else "missing transcript"
        lecture_rows.append(
            f"""<div class="lecture-row">
  <strong>Lecture {video['lecture']:02d}</strong>
  <div><h3>{esc(video['title'])}</h3><p class="muted">{esc(label)} · {words:,} words · <a href="https://www.youtube.com/watch?v={esc(video['id'])}">{esc(video['id'])}</a></p></div>
  <span class="tag">{'ready' if available else 'gap'}</span>
</div>"""
        )
        transcript_rows.append(
            f"""<article class="card">
  <h3>Lecture {video['lecture']:02d}: {esc(video['title'])}</h3>
  <p>{esc(label)} · {words:,} words</p>
  <p><code>{esc(rec.get('clean_text', 'not downloaded'))}</code></p>
</article>"""
        )

    write(
        SITE / "lectures.html",
        page("Lectures", f"<h1>Lectures</h1><section class=\"lecture-list\">{''.join(lecture_rows)}</section>", "lectures"),
    )
    write(
        SITE / "transcripts.html",
        page(
            "Transcripts",
            f"<h1>Transcript Index</h1><p class=\"lede\">Local caption extraction state for the AA203 playlist.</p><section class=\"grid\">{''.join(transcript_rows)}</section>",
            "transcripts",
        ),
    )

    seed = (ROOT / "analysis/research-seed.md").read_text(encoding="utf-8")
    seed_html = "".join(f"<p>{esc(line)}</p>" if line and not line.startswith("#") else f"<h2>{esc(line.lstrip('# ').strip())}</h2>" for line in seed.splitlines() if line.strip())
    write(SITE / "concept-seed.html", page("Concept Seed", f"<h1>Concept Seed</h1>{seed_html}", "concepts"))
    write(
        SITE / "provenance.html",
        page(
            "Provenance",
            f"""
<h1>Provenance</h1>
<p>The canonical source is <a href="{esc(manifest['playlist_url'])}">{esc(manifest['playlist_url'])}</a>.</p>
<p>Playlist metadata is stored in <code>raw-material/youtube/playlist.json</code>. Caption files are stored under <code>raw-material/youtube/transcripts/raw-vtt/</code>, cleaned text under <code>raw-material/youtube/transcripts/clean/</code>, and availability in <code>raw-material/youtube/transcript-index.json</code>.</p>
<p>Run <code>python3 scripts/download_youtube_course_transcripts.py</code>, then <code>python3 scripts/build_site.py</code>, then <code>python3 scripts/validate_all.py</code>.</p>
""",
            "provenance",
        ),
    )
    print(f"built {len(list(SITE.rglob('*.html')))} HTML pages in {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

