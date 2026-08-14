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
ANALYSIS = ROOT / "analysis"


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
    concept_path = ANALYSIS / "concepts/concept-atlas.json"
    evidence_path = ANALYSIS / "evidence/evidence-ledger.json"
    evidence_overrides_path = ANALYSIS / "evidence/manual-review-overrides.json"
    primitives_path = ANALYSIS / "throughlines/primitives.json"
    families_path = ANALYSIS / "throughlines/method-families.json"
    teaching_paths = [
        ANALYSIS / "teaching/derivations.json",
        ANALYSIS / "teaching/worked-examples.json",
        ANALYSIS / "teaching/drills.json",
        ANALYSIS / "teaching/weak-claim-repairs.json",
    ]
    quality_audit_path = ANALYSIS / "audits/course-quality-audit.json"
    concepts = []
    evidence = []
    if not concept_path.exists():
        errors.append("missing analysis/concepts/concept-atlas.json; run concept builder")
    else:
        concepts = json.loads(concept_path.read_text(encoding="utf-8"))
        if len(concepts) < 38:
            errors.append(f"concept atlas should contain at least 38 concepts, found {len(concepts)}")
        required_concept_fields = {
            "id",
            "name",
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
            "course_evidence_ids",
        }
        for concept in concepts:
            missing = sorted(field for field in required_concept_fields if not concept.get(field))
            if missing:
                errors.append(f"concept {concept.get('id', '<missing>')} missing fields: {', '.join(missing)}")
    if not evidence_path.exists():
        errors.append("missing analysis/evidence/evidence-ledger.json; run concept builder")
    else:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        evidence_ids = {row.get("id") for row in evidence}
        overrides = json.loads(evidence_overrides_path.read_text(encoding="utf-8")) if evidence_overrides_path.exists() else {}
        for evidence_id in overrides:
            if evidence_id not in evidence_ids:
                errors.append(f"manual review override references missing evidence: {evidence_id}")
        for row in evidence:
            for field in [
                "id",
                "lecture",
                "lecture_title",
                "video_id",
                "url",
                "timestamp_url",
                "timestamp_start",
                "timestamp_end",
                "local_transcript",
                "raw_vtt",
                "local_transcript_window",
                "supports_concepts",
                "what_transcript_supports",
                "synthesis_beyond_transcript",
                "confidence_status",
            ]:
                if not row.get(field):
                    errors.append(f"evidence {row.get('id', '<missing>')} missing field: {field}")
            transcript = ROOT / row.get("local_transcript", "")
            if row.get("local_transcript") and not transcript.exists():
                errors.append(f"evidence {row.get('id')} points to missing transcript: {row.get('local_transcript')}")
            raw_vtt = ROOT / row.get("raw_vtt", "")
            if row.get("raw_vtt") and not raw_vtt.exists():
                errors.append(f"evidence {row.get('id')} points to missing VTT: {row.get('raw_vtt')}")
        for concept in concepts:
            for evidence_id in concept.get("course_evidence_ids", []):
                if evidence_id not in evidence_ids:
                    errors.append(f"concept {concept['id']} references missing evidence: {evidence_id}")
    for path in [primitives_path, families_path]:
        if not path.exists():
            errors.append(f"missing {path.relative_to(ROOT)}; run concept builder")
    for path in teaching_paths:
        if not path.exists():
            errors.append(f"missing {path.relative_to(ROOT)}; run teaching artifact builder")
        else:
            rows = json.loads(path.read_text(encoding="utf-8"))
            if len(rows) < 5:
                errors.append(f"{path.relative_to(ROOT)} should contain at least 5 records")
            if path.name == "derivations.json":
                for row in rows:
                    for field in ["intuition", "common_wrong_turn", "transfer_check"]:
                        if not row.get(field):
                            errors.append(f"{path.relative_to(ROOT)} row {row.get('id')} missing field: {field}")
            if path.name == "worked-examples.json":
                for row in rows:
                    for field in ["decision_pressure", "concrete_run", "method_boundary", "transfer_question"]:
                        if not row.get(field):
                            errors.append(f"{path.relative_to(ROOT)} row {row.get('id')} missing field: {field}")
            if path.name == "drills.json":
                for row in rows:
                    for field in ["setup_hint", "grading_criteria", "solution_walkthrough", "transfer_variant"]:
                        if not row.get(field):
                            errors.append(f"{path.relative_to(ROOT)} row {row.get('id')} missing field: {field}")
            if path.name == "weak-claim-repairs.json":
                for row in rows:
                    for field in ["failure_consequence", "replacement_rule", "transfer_prompt"]:
                        if not row.get(field):
                            errors.append(f"{path.relative_to(ROOT)} row {row.get('weak')} missing field: {field}")
    if not quality_audit_path.exists():
        errors.append("missing analysis/audits/course-quality-audit.json; run quality audit")
    else:
        audit = json.loads(quality_audit_path.read_text(encoding="utf-8"))
        coverage = audit.get("transcript_coverage", {})
        if coverage.get("available") != coverage.get("videos"):
            errors.append("quality audit reports incomplete transcript coverage")
        if audit.get("concepts", {}).get("without_evidence"):
            errors.append("quality audit reports concepts without evidence")
        if audit.get("evidence", {}).get("missing_transcripts"):
            errors.append("quality audit reports evidence pointing to missing transcripts")
    required_pages = [
        SITE / "index.html",
        SITE / "lectures.html",
        SITE / "transcripts.html",
        SITE / "concepts.html",
        SITE / "course-spine.html",
        SITE / "families.html",
        SITE / "primitives.html",
        SITE / "formula-reader.html",
        SITE / "derivations.html",
        SITE / "worked-examples.html",
        SITE / "drills.html",
        SITE / "solutions.html",
        SITE / "misconceptions.html",
        SITE / "evidence.html",
        SITE / "review-guide.html",
        SITE / "quality.html",
        SITE / "completion-audit.html",
        SITE / "provenance.html",
        SITE / "assets/styles.css",
    ]
    required_pages.extend(SITE / "concepts" / f"{concept['id']}.html" for concept in concepts)
    for path in required_pages:
        if not path.exists():
            errors.append(f"missing site artifact: {path.relative_to(ROOT)}")
    evidence_html = (SITE / "evidence.html").read_text(encoding="utf-8") if (SITE / "evidence.html").exists() else ""
    for row in evidence:
        if f'id="{row["id"]}"' not in evidence_html:
            errors.append(f"evidence anchor missing from evidence.html: {row['id']}")
    rendered_checks = {
        "derivations.html": ["How To Read A Derivation", "One Derivation Run", "Derivation Cards", "Failure test", "Formula shape", "First-principles intuition", "Transfer check", "two-part ledger"],
        "worked-examples.html": ["How To Read A Worked Example", "Example Cards", "Method Route", "Failure Signal", "Decision Pressure", "Concrete Run", "Method Boundary", "future burden"],
        "drills.html": ["How To Work A Drill", "Drill Cards", "Setup hint", "Wrong turn to avoid", "What a strong answer must include", "Transfer variant", "recursive feasibility"],
        "solutions.html": ["What Counts As A Strong Solution", "Solution Cards", "Strong answer", "Solution walkthrough", "Transfer variant", "Grading criteria", "distribution shift"],
        "misconceptions.html": ["How To Repair A Weak Claim", "Repair Cards", "Stronger version", "Failure consequence", "Replacement rule", "Transfer prompt", "what the sentence hides"],
        "course-spine.html": ["Handoff:", "If skipped:", "Name the moving situation", "Learn only where written structure runs out", "Same Car, Harder Questions", "future state it creates", "legal braking or steering"],
        "families.html": ["The move:", "Wrong shortcut:", "Boundary test:", "Choosing A Family In One Run", "transfer", "A method family is a response", "drone", "rover", "warehouse robot"],
        "primitives.html": ["reusable pieces", "One Debug Sequence", "Question it answers", "Failure if wrong", "The action is the command", "Constraint says what cannot be crossed"],
        "formula-reader.html": ["A formula is a machine", "One Reading Run", "Three Checks For Any Formula", "Input:", "Output:", "Wrong read:", "where it fails", "rocket", "rover"],
        "lectures.html": ["Lecture Blocks", "How To Use A Lecture Row", "Lecture Route Cross-Checks", "Lecture-By-Lecture Route", "Extract:", "Wrong turn:", "The problem:", "The move:", "Read the playlist as one route", "warehouse robot"],
        "index.html": ["How To Read This Site", "The Route Through The Material", "What This Site Is Not", "First Read Path", "Replan Without Losing Safety", "Learn Where Writing Runs Out", "evidence record"],
        "review-guide.html": ["Reviewer Route", "Reject condition", "Setup Page Test", "Future-Price Page Test", "Replanning Safety Test", "Reference comparison", "richness gates"],
        "quality.html": ["Editorial Tests", "Weak version", "Stronger version", "Pass test", "Start With A Machine", "Keep Learning Inside Control", "This rubric is an editorial test"],
        "transcripts.html": ["source floor", "How To Use A Transcript", "One Transcript Audit Run", "Transcript Red Flags", "What To Record After Review", "Raw VTT captions stay separate", "auditing source coverage"],
        "concepts.html": ["not read these as vocabulary flashcards", "How To Read A Concept", "Family Pressure Map", "Atlas Doors", "distribution shift", "recursive feasibility"],
        "evidence.html": ["guardrail between lecture source and teaching synthesis", "keyword match is not evidence", "lecture argument"],
        "completion-audit.html": ["local proof", "Requirement Evidence", "What This Does Not Prove", "Human Review Still Required", "ordinary pressure first", "source layer is present"],
        "provenance.html": ["source layer separate from synthesis", "Source-To-Page Trail", "Concrete Claim Check", "One Claim From Source To Teaching", "What A Rebuild Protects", "Do Not Trust The Page If", "raw VTT timestamp", "generated output", "recursive feasibility"],
    }
    for filename, needles in rendered_checks.items():
        path = SITE / filename
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        for needle in needles:
            if needle not in text:
                errors.append(f"{filename} missing teaching marker: {needle}")
    forbidden_vague_phrases = [
        "This is important for control",
        "This improves performance",
        "This captures the objective",
        "This is useful in robotics",
        "The method optimizes the system",
        "Start from the ordinary pressure",
        "The mathematical object is",
        "useful behavior",
        "robust closed-loop controller",
        "important fields",
        "particularly useful",
    ]
    for path in SITE.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if path.name == "misconceptions.html":
            text = re.sub(r"Repair:.*?(?=<article|\Z)", "", text, flags=re.S)
        text_without_quotes = re.sub(r"<blockquote>.*?</blockquote>", "", text, flags=re.S)
        for phrase in forbidden_vague_phrases:
            if phrase in text_without_quotes:
                errors.append(f"vague filler phrase in {path.relative_to(ROOT)}: {phrase}")
    minimum_page_words = {
        "course-spine.html": 1500,
        "index.html": 900,
        "lectures.html": 2300,
        "families.html": 1250,
        "primitives.html": 1200,
        "formula-reader.html": 1250,
        "review-guide.html": 850,
        "quality.html": 900,
        "transcripts.html": 1050,
        "concepts.html": 1600,
        "evidence.html": 6600,
        "completion-audit.html": 850,
        "provenance.html": 1150,
        "worked-examples.html": 1450,
        "derivations.html": 2000,
        "drills.html": 1050,
        "solutions.html": 1700,
        "misconceptions.html": 900,
    }
    for filename, minimum in minimum_page_words.items():
        path = SITE / filename
        text = re.sub(r"<[^>]+>", " ", path.read_text(encoding="utf-8")) if path.exists() else ""
        words = re.findall(r"\b\w+\b", text)
        if len(words) < minimum:
            errors.append(f"{filename} below richness word floor: {len(words)} < {minimum}")
    for concept in concepts:
        path = SITE / "concepts" / f"{concept['id']}.html"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        for phrase in [
            "The controller keeps track of",
            "This answers a practical question",
            "The operation is concrete",
            "The tempting shortcut is simple",
            "But that shortcut breaks because",
            "If that boundary is crossed",
            "A reader should be able to replace",
        ]:
            if phrase in text:
                errors.append(f"concept page still has formulaic scaffold phrase: {path.relative_to(ROOT)} -> {phrase}")
        plain = re.sub(r"<[^>]+>", " ", text)
        words = re.findall(r"\b\w+\b", plain)
        if len(words) < 520:
            errors.append(f"concept page below richness word floor: {path.relative_to(ROOT)} has {len(words)} words")
        for marker in ["read it with your hands", "What to inspect first", "The world check", "one concrete run", "the actual math, one level deeper", "Where the idea stops working"]:
            if marker not in text:
                errors.append(f"concept page missing richness marker: {path.relative_to(ROOT)} -> {marker}")
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
