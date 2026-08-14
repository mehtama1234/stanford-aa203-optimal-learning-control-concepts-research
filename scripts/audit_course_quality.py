#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw-material/youtube"
ANALYSIS = ROOT / "analysis"
AUDITS = ANALYSIS / "audits"
REPORT_JSON = AUDITS / "course-quality-audit.json"
REPORT_MD = AUDITS / "course-quality-audit.md"


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def concept_depth_text(concept: dict[str, Any]) -> str:
    fields = [
        "plain_language_definition",
        "ordinary_problem",
        "naive_approach",
        "why_naive_fails",
        "mathematical_object",
        "operation",
        "worked_example",
        "assumption_boundary",
        "failure_mode",
        "recognition_test",
    ]
    return " ".join(str(concept.get(field, "")) for field in fields)


def main() -> int:
    AUDITS.mkdir(parents=True, exist_ok=True)
    transcript_index = json.loads((RAW / "transcript-index.json").read_text(encoding="utf-8"))
    concepts = json.loads((ANALYSIS / "concepts/concept-atlas.json").read_text(encoding="utf-8"))
    evidence = json.loads((ANALYSIS / "evidence/evidence-ledger.json").read_text(encoding="utf-8"))
    derivations = json.loads((ANALYSIS / "teaching/derivations.json").read_text(encoding="utf-8"))
    examples = json.loads((ANALYSIS / "teaching/worked-examples.json").read_text(encoding="utf-8"))
    drills = json.loads((ANALYSIS / "teaching/drills.json").read_text(encoding="utf-8"))
    repairs = json.loads((ANALYSIS / "teaching/weak-claim-repairs.json").read_text(encoding="utf-8"))

    transcript_gaps = [row for row in transcript_index["records"] if not row.get("transcript_available")]
    status_counts = Counter(row.get("confidence_status", "missing") for row in evidence)
    evidence_by_concept: dict[str, list[str]] = defaultdict(list)
    short_windows: list[str] = []
    missing_transcripts: list[str] = []
    missing_timestamps: list[str] = []
    for row in evidence:
        for concept_id in row.get("supports_concepts", []):
            evidence_by_concept[concept_id].append(row["id"])
        if word_count(row.get("local_transcript_window", "")) < 35:
            short_windows.append(row["id"])
        transcript = ROOT / row.get("local_transcript", "")
        if not transcript.exists():
            missing_transcripts.append(row["id"])
        if not row.get("timestamp_start") or not row.get("timestamp_end") or not row.get("timestamp_url"):
            missing_timestamps.append(row["id"])

    concepts_without_evidence = [concept["id"] for concept in concepts if not evidence_by_concept.get(concept["id"])]
    shallow_concepts = [
        {"id": concept["id"], "words": word_count(concept_depth_text(concept))}
        for concept in concepts
        if word_count(concept_depth_text(concept)) < 95
    ]
    teaching_counts = {
        "derivations": len(derivations),
        "worked_examples": len(examples),
        "drills": len(drills),
        "weak_claim_repairs": len(repairs),
    }
    audit = {
        "transcript_coverage": {
            "available": transcript_index["available_transcripts"],
            "videos": transcript_index["videos"],
            "total_words": transcript_index["total_transcript_words"],
            "gaps": transcript_gaps,
        },
        "concepts": {
            "count": len(concepts),
            "without_evidence": concepts_without_evidence,
            "shallow_concepts": shallow_concepts,
        },
        "evidence": {
            "count": len(evidence),
            "confidence_status_counts": dict(status_counts),
            "short_windows": short_windows,
            "missing_transcripts": missing_transcripts,
            "missing_timestamps": missing_timestamps,
            "manual_review_remaining": status_counts.get("needs_review", 0),
        },
        "teaching": teaching_counts,
        "completion_readiness": {
            "locally_reproducible": not transcript_gaps and not concepts_without_evidence and not missing_transcripts,
            "teaching_grade_complete": status_counts.get("needs_review", 0) == 0 and not shallow_concepts,
            "remaining_blockers": [
                "manual timestamp-level evidence review" if status_counts.get("needs_review", 0) else "",
                "concept prose expansion below teaching-grade threshold" if shallow_concepts else "",
            ],
        },
    }
    audit["completion_readiness"]["remaining_blockers"] = [
        item for item in audit["completion_readiness"]["remaining_blockers"] if item
    ]
    REPORT_JSON.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Course Quality Audit",
        "",
        "This audit records local evidence for progress toward `GOAL.md`. It does not declare the course complete while evidence records remain in `needs_review` status.",
        "",
        "## Source Coverage",
        "",
        f"- Transcripts: {transcript_index['available_transcripts']}/{transcript_index['videos']}",
        f"- Transcript words: {transcript_index['total_transcript_words']:,}",
        f"- Transcript gaps: {len(transcript_gaps)}",
        "",
        "## Concept And Evidence Coverage",
        "",
        f"- Concepts: {len(concepts)}",
        f"- Evidence records: {len(evidence)}",
        f"- Concepts without evidence: {len(concepts_without_evidence)}",
        f"- Evidence records still needing manual review: {status_counts.get('needs_review', 0)}",
        f"- Evidence records with short windows: {len(short_windows)}",
        f"- Evidence records missing timestamps: {len(missing_timestamps)}",
        "",
        "## Teaching Artifacts",
        "",
        f"- Derivations: {len(derivations)}",
        f"- Worked examples: {len(examples)}",
        f"- Drills: {len(drills)}",
        f"- Weak-claim repairs: {len(repairs)}",
        "",
        "## Remaining Work",
        "",
    ]
    blockers = audit["completion_readiness"]["remaining_blockers"]
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- No audit blockers found.")
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"audited {len(concepts)} concepts, {len(evidence)} evidence records, "
        f"{transcript_index['available_transcripts']}/{transcript_index['videos']} transcripts"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
