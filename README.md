# Stanford AA203 Optimal and Learning-Based Control Concepts Research

Transcript-backed first-principles course workspace for Stanford AA203 Optimal and Learning-Based Control, Spring 2026.

Source playlist:
https://www.youtube.com/watch?v=R4_fHzTo0IM&list=PLa9dmHsLK9dg

The goal is to build this in the same style as the strongest course companions in `/home/manishmehta/projects`: raw transcript evidence stays separate from synthesis, HTML pages explain the course from first principles, and concept pages make the math necessary before naming it.

The durable end-to-end target is written in `GOAL.md`.

Current evidence review state: all 38 evidence records are manually deepened with timestamp-level anchors.

## Initial Source Scope

- Channel: Stanford Online
- Playlist: AA203 Optimal and Learning-Based Control | Spring 2026
- Playlist id: `PLa9dmHsLK9dg`
- Videos discovered: 19
- Course arc: optimization theory, calculus of variations, indirect and direct methods, dynamic programming, LQR-style algorithms, reachability, MPC, imitation learning, reinforcement learning, and model-based RL.

## Layout

- `raw-material/youtube/course-manifest.json`: canonical playlist and lecture list
- `raw-material/youtube/playlist.json`: yt-dlp flat playlist metadata
- `raw-material/youtube/transcripts/raw-vtt/`: downloaded caption files
- `raw-material/youtube/transcripts/clean/`: cleaned transcript text
- `raw-material/youtube/transcript-index.json`: machine-readable transcript availability and word counts
- `analysis/research-seed.md`: first course spine and concept seed
- `analysis/concepts/concept-atlas.json`: first-pass required concept atlas
- `analysis/evidence/evidence-ledger.json`: timestamped transcript-window evidence records
- `analysis/throughlines/`: method families and mathematical primitives
- `analysis/teaching/`: derivations, worked examples, drills, and weak-claim repairs
- `analysis/audits/`: local quality and completion audit artifacts
- `GOAL.md`: meaty end-to-end build target for the full course site
- `site/`: generated static HTML starter site
- `scripts/download_youtube_course_transcripts.py`: refresh playlist metadata and captions
- `scripts/build_first_principles_atlas.py`: build the first-pass concept and evidence artifacts
- `scripts/build_teaching_artifacts.py`: build the deeper teaching/practice artifacts
- `scripts/audit_course_quality.py`: audit transcript, concept, evidence, and teaching coverage
- `scripts/build_site.py`: build the starter HTML site from local artifacts
- `scripts/validate_all.py`: validate source files and generated pages

## Workflow

```bash
python3 scripts/download_youtube_course_transcripts.py
python3 scripts/build_first_principles_atlas.py
python3 scripts/build_teaching_artifacts.py
python3 scripts/audit_course_quality.py
python3 scripts/build_site.py
python3 scripts/validate_all.py
```

Open:

```text
site/index.html
```

## Quality Standard

Each future concept page should answer:

1. What ordinary control problem forces this idea to exist?
2. What state, action, cost, constraint, or uncertainty does the idea track?
3. What mathematical object is introduced?
4. What operation is performed on that object?
5. What breaks if the assumption is false?
6. Which lecture transcript supports the explanation?
