# Handoff

## Current State

The repository is initialized as a standalone git repo for Stanford AA203 Optimal and Learning-Based Control, Spring 2026.

Completed locally:

- Added `GOAL.md` as the durable end-to-end course-site target.
- Created canonical course manifest for the 19-video Stanford Online playlist.
- Downloaded flat playlist metadata with `yt-dlp`.
- Downloaded and cleaned transcripts for all 19 lectures.
- Captured 207,618 transcript words.
- Built a concept atlas with 38 required concepts.
- Built an evidence ledger with 38 timestamped local transcript-window records.
- Manually deepened all 38 evidence records with timestamp-level anchors.
- Built method-family and primitive throughline artifacts.
- Built structured teaching artifacts for derivations, worked examples, drills, solutions, and weak-claim repairs.
- Built quality audit artifacts under `analysis/audits/`.
- Generated 57 HTML pages, including individual concept pages plus course spine, families, primitives, formula reader, derivations, worked examples, drills, solutions, misconceptions, evidence, review guide, quality rubric, and completion audit.
- Added validation for manifest shape, transcript file references, concept fields, evidence fields, evidence-to-transcript links, teaching artifacts, generated pages, concept pages, evidence anchors, teaching-page markers, and local links.
- Deepened the main route pages so `index.html`, `lectures.html`, and `course-spine.html` teach the playlist as one connected control argument rather than a video index.
- Deepened shared concept-page structure with concrete runs, one-level-deeper math, boundary tests, an inspection layer, and anti-template wording checks.
- Added a learning-specific control-loop section and higher validation floor for the 10 learning concept pages.
- Deepened formula, derivation, worked-example, drill, solution, misconception, provenance, and evidence pages with review protocols and concrete transfer tests.
- Raised validation word floors and required markers across the richest pages, including concept pages, derivations, evidence, provenance, and the course spine.

Important editorial correction:

- The repo is structurally complete and has had multiple depth passes, but final completion still requires a human editorial audit against the strongest local explainers.
- `GOAL.md` now names the stricter target: pages should feel comparable to `http://127.0.0.1:8050/vt-explained.html` and `http://127.0.0.1:8050/the-machine.html`.
- Passing validation is not enough. The validator proves structural and marker coverage; the reviewer still has to judge whether sampled pages read like compact first-principles essays in everyday language.
- The strongest remaining work is page-specific editorial polish: more distinct worked runs on individual concepts, more concrete quantities in examples, and comparison against the local reference pages in a browser.

## Rebuild

All 19 lecture transcripts are present locally. Rebuild the generated artifacts with:

```bash
python3 scripts/build_first_principles_atlas.py
python3 scripts/build_teaching_artifacts.py
python3 scripts/audit_course_quality.py
python3 scripts/build_site.py
python3 scripts/validate_all.py
```

Only run `python3 scripts/download_youtube_course_transcripts.py` when refreshing the source captions or playlist metadata.

To review in a browser:

```bash
cd site
python3 -m http.server 8020 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8020/`.

## Next Deepening Pass

The next phase should follow the stronger course repos:

- Use `GOAL.md` as the acceptance target.
- Treat `vt-explained.html` and `the-machine.html` as the writing reference.
- Sample the rendered course in the browser, especially `course-spine.html`, `lectures.html`, `concepts/state.html`, `concepts/bellman-recursion.html`, `concepts/model-predictive-control.html`, `concepts/behavioral-cloning.html`, `concepts/reward.html`, and `concepts/model-based-rl.html`.
- For each sampled page, ask whether the reader sees the ordinary pressure, tempting wrong move, mathematical object, operation, concrete run, math one level deeper, failure boundary, and transcript evidence.
- Prefer page-specific improvements over broad template changes when a page still sounds too similar to its neighbors.
- Add stricter editorial audits only when they prove a real requirement from `GOAL.md`, not merely a convenient string marker.
