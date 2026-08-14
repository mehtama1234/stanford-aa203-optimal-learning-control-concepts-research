#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
RAW = ROOT / "raw-material/youtube"
ANALYSIS = ROOT / "analysis"


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(line.rstrip() for line in content.splitlines()) + "\n", encoding="utf-8")


def load_json(path: Path, fallback: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback


def page(title: str, body: str, active: str = "", depth: int = 0) -> str:
    prefix = "../" * depth
    nav = [
        ("index.html", "Overview", "overview"),
        ("lectures.html", "Lectures", "lectures"),
        ("transcripts.html", "Transcripts", "transcripts"),
        ("concepts.html", "Concepts", "concepts"),
        ("course-spine.html", "Spine", "spine"),
        ("families.html", "Families", "families"),
        ("primitives.html", "Primitives", "primitives"),
        ("formula-reader.html", "Formulas", "formulas"),
        ("derivations.html", "Derivations", "derivations"),
        ("drills.html", "Drills", "drills"),
        ("evidence.html", "Evidence", "evidence"),
        ("review-guide.html", "Review", "review"),
    ]
    links = "\n".join(
        f'<a class="{"active" if key == active else ""}" href="{prefix}{href}">{label}</a>' for href, label, key in nav
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} · Stanford AA203 Control Lab</title>
  <link rel="stylesheet" href="{prefix}assets/styles.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="{prefix}index.html">Stanford AA203 Control Lab</a>
    <nav>{links}</nav>
  </header>
  <main>{body}</main>
</body>
</html>
"""


def card(title: str, body: str, extra_class: str = "") -> str:
    return f'<article class="card {extra_class}"><h3>{esc(title)}</h3>{body}</article>'


def section_list(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


def concept_link(concept: dict[str, Any], depth: int = 0) -> str:
    prefix = "../" * depth
    return f'<a href="{prefix}concepts/{esc(concept["id"])}.html">{esc(concept["name"])}</a>'


def evidence_by_id(evidence: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in evidence}


def evidence_card(row: dict[str, Any], depth: int = 0) -> str:
    prefix = "../" * depth
    timestamp = ""
    if row.get("timestamp_start"):
        timestamp = f' · <a href="{esc(row.get("timestamp_url", row["url"]))}">{esc(row["timestamp_start"])}-{esc(row.get("timestamp_end", ""))}</a>'
    return f"""<article class="evidence-card" id="{esc(row['id'])}">
  <h3>{esc(row['id'])}: Lecture {esc(row['lecture'])} · {esc(row['lecture_title'])}</h3>
  <p class="muted"><a href="{esc(row['url'])}">{esc(row['video_id'])}</a>{timestamp} · <code>{esc(row['local_transcript'])}</code> · {esc(row['confidence_status'])}</p>
  <blockquote>{esc(row['local_transcript_window'])}</blockquote>
  <p><strong>Transcript supports:</strong> {esc(row['what_transcript_supports'])}</p>
  <p><strong>Synthesis boundary:</strong> {esc(row['synthesis_beyond_transcript'])}</p>
  <p><a href="{prefix}evidence.html#{esc(row['id'])}">Open evidence record</a></p>
</article>"""


def main() -> int:
    manifest = load_json(RAW / "course-manifest.json", {"videos": []})
    transcript_index = load_json(
        RAW / "transcript-index.json",
        {"available_transcripts": 0, "videos": len(manifest["videos"]), "total_transcript_words": 0, "records": []},
    )
    concepts = load_json(ANALYSIS / "concepts/concept-atlas.json", [])
    evidence = load_json(ANALYSIS / "evidence/evidence-ledger.json", [])
    primitives = load_json(ANALYSIS / "throughlines/primitives.json", [])
    families = load_json(ANALYSIS / "throughlines/method-families.json", [])
    derivations = load_json(ANALYSIS / "teaching/derivations.json", [])
    worked_examples = load_json(ANALYSIS / "teaching/worked-examples.json", [])
    drills = load_json(ANALYSIS / "teaching/drills.json", [])
    weak_claim_repairs = load_json(ANALYSIS / "teaching/weak-claim-repairs.json", [])
    quality_audit = load_json(ANALYSIS / "audits/course-quality-audit.json", {})
    ev_by_id = evidence_by_id(evidence)
    concepts_by_id = {concept["id"]: concept for concept in concepts}
    by_video = {row["video_id"]: row for row in transcript_index.get("records", [])}
    concepts_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for concept in concepts:
        concepts_by_family[concept["family"]].append(concept)

    write(
        SITE / "assets/styles.css",
        """
:root {
  color-scheme: light;
  --ink: #17202a;
  --muted: #5d6875;
  --line: #d7e0e6;
  --paper: #ffffff;
  --wash: #f4f7f9;
  --accent: #0b6b64;
  --accent-2: #8b3f18;
  --soft: #e8f2f0;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--ink);
  background: var(--wash);
  line-height: 1.56;
}
.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  gap: 22px;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  border-bottom: 1px solid var(--line);
  background: rgba(255,255,255,.97);
}
.brand { color: var(--ink); font-weight: 760; text-decoration: none; white-space: nowrap; }
nav { display: flex; flex-wrap: wrap; gap: 10px 12px; }
nav a { color: var(--muted); text-decoration: none; font-size: 13px; }
nav a.active, nav a:hover { color: var(--accent); }
main { max-width: 1160px; margin: 0 auto; padding: 36px 24px 72px; }
.hero {
  display: grid;
  gap: 18px;
  padding: 30px 0 26px;
  border-bottom: 1px solid var(--line);
}
h1 { max-width: 940px; margin: 0; font-size: clamp(34px, 5vw, 62px); line-height: 1; letter-spacing: 0; }
h2 { margin-top: 38px; font-size: 27px; letter-spacing: 0; }
h3 { margin: 0 0 7px; font-size: 18px; letter-spacing: 0; }
p { max-width: 860px; }
a { color: var(--accent); }
.lede { max-width: 900px; color: var(--muted); font-size: 19px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin: 18px 0; }
.stat, .card, .evidence-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
  padding: 16px;
}
.stat strong { display: block; font-size: 30px; color: var(--accent); line-height: 1.1; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(265px, 1fr)); gap: 14px; }
.wide-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 14px; }
.stack { display: grid; gap: 14px; }
.lecture-list { display: grid; gap: 10px; }
.lecture-row {
  display: grid;
  grid-template-columns: 72px 1fr auto;
  gap: 14px;
  align-items: start;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
}
.tag { color: var(--accent-2); font-size: 13px; font-weight: 760; text-transform: uppercase; }
.pill { display: inline-block; margin: 0 6px 6px 0; padding: 3px 8px; border-radius: 999px; background: var(--soft); color: var(--accent); font-size: 13px; }
.muted { color: var(--muted); }
code { background: #eef3f4; padding: 2px 5px; border-radius: 4px; white-space: normal; }
blockquote {
  margin: 12px 0;
  padding: 12px 14px;
  border-left: 4px solid var(--accent);
  background: #f7faf9;
  color: #2c3a40;
}
table { width: 100%; border-collapse: collapse; background: var(--paper); border: 1px solid var(--line); }
th, td { padding: 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
th { color: var(--muted); font-size: 13px; text-transform: uppercase; }
@media (max-width: 780px) {
  .topbar { align-items: flex-start; flex-direction: column; }
  .lecture-row { grid-template-columns: 1fr; }
  main { padding: 28px 18px 56px; }
}
""",
    )

    stats = f"""
<section class="stats">
  <div class="stat"><strong>{len(manifest['videos'])}</strong><span>playlist lectures</span></div>
  <div class="stat"><strong>{transcript_index.get('available_transcripts', 0)}</strong><span>local transcripts</span></div>
  <div class="stat"><strong>{transcript_index.get('total_transcript_words', 0):,}</strong><span>transcript words</span></div>
  <div class="stat"><strong>{len(concepts)}</strong><span>concept pages</span></div>
  <div class="stat"><strong>{len(evidence)}</strong><span>evidence records</span></div>
</section>
"""
    entry_cards = [
        ("Course Spine", "Read one coherent route from state and action through Bellman recursion, MPC, imitation learning, and model-based RL.", "course-spine.html"),
        ("Concept Atlas", "Study every required concept with problem, naive failure, math object, operation, example, boundary, and evidence.", "concepts.html"),
        ("Formula Reader", "Translate formulas into what is being controlled, what object carries the burden, and what operation is performed.", "formula-reader.html"),
        ("Drills", "Practice setup, method choice, Bellman recognition, MPC feasibility, reward diagnosis, and repair.", "drills.html"),
    ]
    entries = "".join(card(title, f"<p>{body}</p><p><a href=\"{href}\">Open</a></p>") for title, body, href in entry_cards)
    write(
        SITE / "index.html",
        page(
            "Overview",
            f"""
<section class="hero">
  <p class="tag">Transcript-backed first-principles course companion</p>
  <h1>{esc(manifest['title'])}</h1>
  <p class="lede">Optimal control is the discipline of choosing actions whose consequences unfold through time. Learning-based control extends that discipline when the model, cost, environment, or feedback signal cannot be fully written down in advance.</p>
  {stats}
</section>
<h2>Strongest Entry Points</h2>
<section class="grid">{entries}</section>
<h2>Current Build State</h2>
<p>This is the first deepening pass beyond the transcript scaffold. Concept prose is present for the full minimum atlas, and evidence records point into local transcript windows with <code>needs_review</code> status until a manual timestamp pass deepens them.</p>
""",
            "overview",
        ),
    )

    lecture_rows = []
    for video in manifest["videos"]:
        rec = by_video.get(video["id"], {})
        available = bool(rec.get("transcript_available"))
        label = "transcript captured" if available else "missing transcript"
        lecture_concepts = [c for c in concepts if c.get("lecture") == video["lecture"]]
        links = " ".join(f'<span class="pill">{concept_link(c)}</span>' for c in lecture_concepts[:6])
        if len(lecture_concepts) > 6:
            links += f' <span class="muted">+{len(lecture_concepts)-6} more</span>'
        lecture_rows.append(
            f"""<div class="lecture-row">
  <strong>Lecture {video['lecture']:02d}</strong>
  <div><h3>{esc(video['title'])}</h3><p class="muted">{esc(label)} · {rec.get('word_count', 0):,} words · <a href="https://www.youtube.com/watch?v={esc(video['id'])}">{esc(video['id'])}</a></p><p>{links or '<span class="muted">No primary concept assigned yet.</span>'}</p></div>
  <span class="tag">{'ready' if available else 'gap'}</span>
</div>"""
        )
    write(SITE / "lectures.html", page("Lectures", f"<h1>Lectures</h1><section class=\"lecture-list\">{''.join(lecture_rows)}</section>", "lectures"))

    transcript_cards = []
    for video in manifest["videos"]:
        rec = by_video.get(video["id"], {})
        transcript_cards.append(
            card(
                f"Lecture {video['lecture']:02d}: {video['title']}",
                f"<p>{'transcript captured' if rec.get('transcript_available') else 'missing transcript'} · {rec.get('word_count', 0):,} words</p><p><code>{esc(rec.get('clean_text', 'not downloaded'))}</code></p>",
            )
        )
    write(SITE / "transcripts.html", page("Transcripts", f"<h1>Transcript Index</h1><section class=\"grid\">{''.join(transcript_cards)}</section>", "transcripts"))

    family_sections = []
    for family in families:
        rows = concepts_by_family.get(family["id"].replace("-", " "), []) or [concepts_by_id[cid] for cid in family["concepts"] if cid in concepts_by_id]
        concept_cards = "".join(card(c["name"], f"<p>{esc(c['plain_language_definition'])}</p><p>{concept_link(c)}</p>") for c in rows)
        family_sections.append(f"<h2>{esc(family['name'])}</h2><p>{esc(family['problem'])}</p><section class=\"grid\">{concept_cards}</section>")
    concept_cards = "".join(
        card(c["name"], f"<p>{esc(c['plain_language_definition'])}</p><p><span class=\"tag\">{esc(c['family'])}</span></p><p>{concept_link(c)}</p>")
        for c in concepts
    )
    write(SITE / "concepts.html", page("Concepts", f"<h1>Concept Atlas</h1><p class=\"lede\">The full minimum concept list from <code>GOAL.md</code>, now rendered as individual first-principles pages.</p><section class=\"grid\">{concept_cards}</section>", "concepts"))

    for concept in concepts:
        ev_cards = "".join(evidence_card(ev_by_id[eid], depth=1) for eid in concept.get("course_evidence_ids", []) if eid in ev_by_id)
        related = [c for c in concepts if c["family"] == concept["family"] and c["id"] != concept["id"]][:6]
        body = f"""
<p><a href="../concepts.html">Back to concept atlas</a></p>
<h1>{esc(concept['name'])}</h1>
<p class="lede">{esc(concept['plain_language_definition'])}</p>
<section class="wide-grid">
  {card("Ordinary Problem", f"<p>{esc(concept['ordinary_problem'])}</p>")}
  {card("Naive Approach", f"<p>{esc(concept['naive_approach'])}</p><p><strong>Why it fails:</strong> {esc(concept['why_naive_fails'])}</p>")}
  {card("Mathematical Object", f"<p>{esc(concept['mathematical_object'])}</p>")}
  {card("Operation", f"<p>{esc(concept['operation'])}</p>")}
</section>
<h2>Worked Example</h2>
<p>{esc(concept['worked_example'])}</p>
<h2>Boundary And Failure</h2>
<section class="wide-grid">
  {card("Assumption Boundary", f"<p>{esc(concept['assumption_boundary'])}</p>")}
  {card("Failure Mode", f"<p>{esc(concept['failure_mode'])}</p>")}
  {card("Recognize It", f"<p>{esc(concept['recognition_test'])}</p>")}
</section>
<h2>Transcript Evidence</h2>
<section class="stack">{ev_cards or '<p class="muted">No evidence record yet.</p>'}</section>
<h2>Nearby Concepts</h2>
<p>{' '.join(f'<span class="pill">{concept_link(item, depth=1)}</span>' for item in related)}</p>
"""
        write(SITE / "concepts" / f"{concept['id']}.html", page(concept["name"], body, "concepts", depth=1))

    spine_items = [
        ("Name the control problem", "State, action, dynamics, cost, horizon, constraints, and feasibility define what counts as a legal future."),
        ("Move from snapshots to paths", "Calculus of variations, indirect methods, direct transcription, shooting, collocation, and trajectory optimization make the whole path the object."),
        ("Compress future consequence", "Dynamic programming, value functions, Bellman recursion, and stochastic DP turn future planning into state-indexed accounting."),
        ("Exploit local structure", "LQR and local quadratic approximations make fast feedback possible when deviations stay near a nominal plan."),
        ("Replan safely", "Reachability, MPC, recursive feasibility, and stability under replanning keep finite-horizon decisions from painting the system into a corner."),
        ("Learn when structure is incomplete", "Imitation learning, behavioral cloning, RL, reward, policies, value-based RL, policy optimization, exploration, and model-based RL add data-driven control."),
    ]
    write(SITE / "course-spine.html", page("Course Spine", f"<h1>Course Spine</h1><section class=\"stack\">{''.join(card(a,b) for a,b in spine_items)}</section>", "spine"))

    family_cards = "".join(
        card(family["name"], f"<p>{esc(family['problem'])}</p><p>{' '.join(f'<span class=\"pill\">{concept_link(concepts_by_id[cid])}</span>' for cid in family['concepts'] if cid in concepts_by_id)}</p>")
        for family in families
    )
    write(SITE / "families.html", page("Method Families", f"<h1>Method Families</h1><section class=\"stack\">{family_cards}</section>", "families"))

    primitive_cards = "".join(
        card(p["name"], f"<p>{esc(p['plain_language'])}</p><p>{' '.join(f'<span class=\"pill\">{concept_link(concepts_by_id[cid])}</span>' for cid in p['used_by'] if cid in concepts_by_id)}</p>")
        for p in primitives
    )
    write(SITE / "primitives.html", page("Primitives", f"<h1>Mathematical Primitives</h1><section class=\"grid\">{primitive_cards}</section>", "primitives"))

    formula_rows = [
        ("Dynamics", "x next equals f of state and action", "State transition", "Propagate consequence forward", "Wrong model, wrong future"),
        ("Objective", "sum of stage costs plus terminal cost", "Cost functional", "Compare whole futures", "Proxy cost misses real task"),
        ("Bellman Recursion", "value equals min over action of cost plus next value", "Value function", "Split now from future", "State is incomplete"),
        ("Hamiltonian", "stage cost plus costate times dynamics", "Local future-price package", "Price action by immediate and downstream effect", "Only necessary, not global"),
        ("MPC", "solve finite horizon, apply first action, repeat", "Receding-horizon problem", "Turn planning into feedback", "Future infeasibility"),
        ("Policy Gradient", "change policy parameters toward higher return", "Parameterized policy", "Improve the action rule directly", "Noisy or unsafe exploration"),
    ]
    formula_table = "<table><tr><th>Formula Shape</th><th>Plain Reading</th><th>Object</th><th>Operation</th><th>Failure Test</th></tr>" + "".join(
        f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td><td>{esc(e)}</td></tr>" for a, b, c, d, e in formula_rows
    ) + "</table>"
    write(SITE / "formula-reader.html", page("Formula Reader", f"<h1>Formula Reader</h1>{formula_table}", "formulas"))

    derivation_cards = []
    for item in derivations:
        linked = " ".join(f'<span class="pill">{concept_link(concepts_by_id[cid])}</span>' for cid in item.get("linked_concepts", []) if cid in concepts_by_id)
        body = f"""
<p><strong>Problem:</strong> {esc(item['problem'])}</p>
<p><strong>Starting point:</strong> {esc(item['starting_point'])}</p>
<ol>{''.join(f'<li>{esc(step)}</li>' for step in item['steps'])}</ol>
<p><strong>Formula shape:</strong> {esc(item['formula_shape'])}</p>
<p><strong>Why it works:</strong> {esc(item['why_it_works'])}</p>
<p><strong>Failure test:</strong> {esc(item['failure_test'])}</p>
<p>{linked}</p>
"""
        derivation_cards.append(card(item["title"], body))
    write(SITE / "derivations.html", page("Derivations", f"<h1>Derivation Walkthroughs</h1><p class=\"lede\">Slow, problem-first derivations that explain why the formula shape exists before asking the learner to manipulate symbols.</p><section class=\"stack\">{''.join(derivation_cards)}</section>", "derivations"))

    example_cards = []
    for item in worked_examples:
        linked = " ".join(f'<span class="pill">{concept_link(concepts_by_id[cid])}</span>' for cid in item.get("linked_concepts", []) if cid in concepts_by_id)
        body = f"""
<p>{esc(item['setup'])}</p>
<table>
  <tr><th>State</th><td>{esc(item['state'])}</td></tr>
  <tr><th>Action</th><td>{esc(item['action'])}</td></tr>
  <tr><th>Cost</th><td>{esc(item['cost'])}</td></tr>
  <tr><th>Constraints</th><td>{esc(item['constraints'])}</td></tr>
  <tr><th>Method Route</th><td>{esc(item['method_route'])}</td></tr>
  <tr><th>Failure Signal</th><td>{esc(item['failure_signal'])}</td></tr>
</table>
<p>{linked}</p>
"""
        example_cards.append(card(item["title"], body))
    write(SITE / "worked-examples.html", page("Worked Examples", f"<h1>Worked Examples</h1><p class=\"lede\">Concrete setups that force the learner to name state, action, cost, constraints, method route, and failure signal.</p><section class=\"stack\">{''.join(example_cards)}</section>", "derivations"))

    drill_cards = []
    solution_cards = []
    for item in drills:
        linked = " ".join(f'<span class="pill">{concept_link(concepts_by_id[cid])}</span>' for cid in item.get("linked_concepts", []) if cid in concepts_by_id)
        drill_cards.append(
            card(
                item["title"],
                f"<p>{esc(item['prompt'])}</p><p><strong>Wrong turn to avoid:</strong> {esc(item['wrong_turn'])}</p><p>{linked}</p>",
            )
        )
        solution_cards.append(
            card(
                f"{item['title']} Solution",
                f"<p><strong>Prompt:</strong> {esc(item['prompt'])}</p><p><strong>Wrong turn:</strong> {esc(item['wrong_turn'])}</p><p><strong>Strong answer:</strong> {esc(item['strong_answer'])}</p><p>{linked}</p>",
            )
        )
    write(SITE / "drills.html", page("Drills", f"<h1>Drills</h1><p class=\"lede\">Practice prompts that train setup, method choice, future-cost recognition, feasibility diagnosis, reward repair, and approximation boundaries.</p><section class=\"stack\">{''.join(drill_cards)}</section>", "drills"))
    write(SITE / "solutions.html", page("Solutions", f"<h1>Solutions</h1><p class=\"lede\">Full solution notes that name the common wrong turn before giving the stronger control explanation.</p><section class=\"stack\">{''.join(solution_cards)}</section>", "drills"))

    base_misconceptions = [
        ("Optimal means globally best", "Many methods produce local candidates or model-conditioned optima, not universal guarantees."),
        ("MPC automatically stabilizes", "Repeated short-horizon solves need terminal structure or other conditions to protect long-run behavior."),
        ("Model-based RL is safe because it plans", "Planning through a learned model can exploit model errors."),
    ]
    misconception_cards = [card(a, f"<p>{esc(b)}</p>") for a, b in base_misconceptions]
    for item in weak_claim_repairs:
        misconception_cards.append(
            card(
                f"Repair: {item['weak']}",
                f"<p><strong>Diagnosis:</strong> {esc(item['diagnosis'])}</p><p><strong>Stronger version:</strong> {esc(item['strong'])}</p>",
            )
        )
    write(SITE / "misconceptions.html", page("Misconceptions", f"<h1>Misconceptions And Weak-Claim Repairs</h1><section class=\"grid\">{''.join(misconception_cards)}</section>", "review"))

    evidence_html = "".join(evidence_card(row) for row in evidence)
    write(SITE / "evidence.html", page("Evidence", f"<h1>Evidence Ledger</h1><p class=\"lede\">Each record points to a local transcript window and marks the first-pass confidence state.</p><section class=\"stack\">{evidence_html}</section>", "evidence"))

    review = [
        ("First-principles depth", "Open a setup concept, a dynamic-programming concept, an MPC concept, and a learning concept. Check that each starts from the control pressure before formulas."),
        ("Evidence discipline", "Open evidence records and verify that local transcript windows support the concept vocabulary without pretending to prove the whole synthesis."),
        ("Practice usefulness", "Run the drills and verify the solutions name wrong turns, not just final answers."),
        ("Known risk", "Lecture 13 is still missing due to the YouTube 429 caption gap. Evidence is first-pass and needs manual timestamp review."),
    ]
    write(SITE / "review-guide.html", page("Review Guide", f"<h1>Review Guide</h1><section class=\"stack\">{''.join(card(a,b) for a,b in review)}</section>", "review"))

    quality = [
        ("First principles", "Start from state, action, consequence, constraint, and future cost before naming the method."),
        ("Plain language", "Translate formal objects without flattening the mathematical job they perform."),
        ("Failure boundary", "State where the method breaks: model mismatch, infeasibility, approximation error, distribution shift, unsafe exploration, or reward hacking."),
        ("Evidence honesty", "Separate what the transcript directly supports from synthesis beyond the transcript."),
    ]
    write(SITE / "quality.html", page("Quality", f"<h1>Quality Rubric</h1><section class=\"grid\">{''.join(card(a,b) for a,b in quality)}</section>", "review"))

    audit_rows = [
        ("Required pages", "present", f"{len(list(SITE.rglob('*.html')))} HTML files generated before this audit page is written"),
        ("Transcript coverage", "partial", f"{transcript_index.get('available_transcripts', 0)}/{transcript_index.get('videos', 0)} transcripts; Lecture 13 remains a source gap"),
        ("Concept atlas", "present", f"{len(concepts)} concepts generated"),
        ("Evidence ledger", "first pass", f"{len(evidence)} evidence records with needs_review status"),
        ("Teaching artifacts", "present", f"{len(derivations)} derivations, {len(worked_examples)} examples, {len(drills)} drills, and {len(weak_claim_repairs)} repair cases generated from analysis/teaching"),
        ("Manual review", "remaining", "timestamp-level evidence deepening and prose polish remain"),
    ]
    if quality_audit:
        transcript_gaps = len(quality_audit.get("transcript_coverage", {}).get("gaps", []))
        manual_review = quality_audit.get("evidence", {}).get("manual_review_remaining", len(evidence))
        audit_rows[1] = (
            "Transcript coverage",
            "complete" if transcript_gaps == 0 else "partial",
            f"{transcript_index.get('available_transcripts', 0)}/{transcript_index.get('videos', 0)} transcripts; audit gaps: {transcript_gaps}",
        )
        audit_rows[3] = (
            "Evidence ledger",
            "first pass" if manual_review else "reviewed",
            f"{len(evidence)} evidence records; {manual_review} still need manual review",
        )
        audit_rows.append(
            (
                "Quality audit",
                "present",
                "analysis/audits/course-quality-audit.json and analysis/audits/course-quality-audit.md generated",
            )
        )
    audit_table = "<table><tr><th>Requirement</th><th>Status</th><th>Evidence</th></tr>" + "".join(
        f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in audit_rows
    ) + "</table>"
    write(SITE / "completion-audit.html", page("Completion Audit", f"<h1>Completion Audit</h1>{audit_table}", "review"))

    write(
        SITE / "provenance.html",
        page(
            "Provenance",
            f"""
<h1>Provenance</h1>
<p>The canonical source is <a href="{esc(manifest['playlist_url'])}">{esc(manifest['playlist_url'])}</a>.</p>
<p>Playlist metadata is stored in <code>raw-material/youtube/playlist.json</code>. Caption files are stored under <code>raw-material/youtube/transcripts/raw-vtt/</code>, cleaned text under <code>raw-material/youtube/transcripts/clean/</code>, and availability in <code>raw-material/youtube/transcript-index.json</code>.</p>
<p>Analysis artifacts live in <code>analysis/concepts/</code>, <code>analysis/evidence/</code>, and <code>analysis/throughlines/</code>.</p>
<p>Run <code>python3 scripts/build_first_principles_atlas.py</code>, then <code>python3 scripts/build_site.py</code>, then <code>python3 scripts/validate_all.py</code>.</p>
""",
            "provenance",
        ),
    )
    print(f"built {len(list(SITE.rglob('*.html')))} HTML pages in {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
