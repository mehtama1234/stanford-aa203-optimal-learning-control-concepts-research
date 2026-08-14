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
        "evidence.html": ["guardrail between lecture source and teaching synthesis", "keyword match is not evidence", "lecture argument", "How To Inspect One Evidence Record", "Two Good Evidence Shapes", "Reject the record", "Synthesis boundary"],
        "completion-audit.html": ["local proof", "Requirement Evidence", "What This Does Not Prove", "Two Proofs Required", "mechanical proof", "editorial proof", "Human Review Still Required", "ordinary pressure first", "source layer is present"],
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
        "evidence.html": 7000,
        "completion-audit.html": 1200,
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
        concept_floor = 740 if concept.get("family") == "learning-based control" else 520
        if len(words) < concept_floor:
            errors.append(f"concept page below richness word floor: {path.relative_to(ROOT)} has {len(words)} words")
        for marker in ["read it with your hands", "What to inspect first", "The world check", "one concrete run", "the actual math, one level deeper", "Where the idea stops working"]:
            if marker not in text:
                errors.append(f"concept page missing richness marker: {path.relative_to(ROOT)} -> {marker}")
        if concept.get("family") == "learning-based control":
            for marker in ["data inside the loop", "What the learner changes next", "What states did the data actually cover", "warehouse drawer"]:
                if marker not in text:
                    errors.append(f"learning concept page missing control-loop marker: {path.relative_to(ROOT)} -> {marker}")
        if concept.get("id") == "optimal-control-problem":
            for marker in ["80 meters above the pad", "18 m/s", "12 seconds of fuel", "dt = 1 second", "x = (height, velocity, fuel)", "u_0 = 18", "u_1 = 8", "velocity changes from -18 to -10 m/s", "height falls to 70 meters", "fuel drops from 12 to -24", "u_0 = 10", "height falls to 62 meters", "44 meters after two seconds", "choose u_0...u_{N-1}", "J = sum_k fuel_cost(u_k) + 100*landing_error^2 + 20*touchdown_speed^2", "x_{k+1}=f(x_k,u_k)", "fuel_k &gt;= 0", "v_{k+1}=v_k + dt*(u_k - 10)", "fuel_{k+1}=fuel_k - 2*u_k"]:
                if marker not in text:
                    errors.append(f"optimal control problem page missing trajectory-chain marker: {marker}")
            if len(words) < 900:
                errors.append(f"optimal control problem page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "action-control-input":
            for marker in ["h = 10 meters", "v = 0.2 m/s", "48 percent above hover", "dt = 0.1 seconds", "a(u)=4.8 m/s^2", "v_next = 0.2 + 0.1*4.8 = 0.68 m/s", "h_next = 10 + 0.1*0.68 = 10.068 meters", "6.8 centimeters", "motors, acceleration, velocity, and only then position", "a(u)=10*u", "-0.3 &lt;= u &lt;= 0.5", "v_next = v + dt * a(u)", "h_next = h + dt * v_next", "u = 0.9", "clips it to u = 0.5", "a=5.0 m/s^2", "x_next = f(x, u)", "action limits are limits on u", "(h_next - 12)^2", "actuator truth", "delay, saturation, dead zones, and rate limits"]:
                if marker not in text:
                    errors.append(f"action concept page missing command-vs-outcome marker: {marker}")
            if len(words) < 900:
                errors.append(f"action concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "dynamics":
            for marker in ["speed 20 m/s", "theta = 0 degrees", "u = 5 degrees", "dt = 0.2 seconds", "yaw_rate = 0.30 rad/s", "theta_next = 0 + 0.2*0.30 = 0.06 rad", "yaw_rate = 0.05 rad/s", "v_y = -1.0 m/s", "theta_next = 0 + 0.2*0.05 = 0.01 rad", "y_next = y + 0.2*(-1.0)", "x_next = f(x,u)", "dx/dt = f(x,u)", "x=[y,theta,v_y,speed]", "f_dry", "f_ice", "model fidelity"]:
                if marker not in text:
                    errors.append(f"dynamics concept page missing state-update marker: {marker}")
            if len(words) < 900:
                errors.append(f"dynamics concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "objective-cost-function":
            for marker in ["Path A reaches the spot in 8 seconds", "Path B takes 12 seconds", "8 is smaller than 12", "steering effort 10", "wall penalty 30", "steering effort 3", "Path A: 8 + 0.5*10 + 30 = 43", "Path B: 12 + 0.5*3 + 0 = 13.5", "written measurement of what counts as better", "J = sum_k stage_cost(x_k,u_k) + terminal_cost(x_N)", "5.0*wall_risk", "stage_0 + stage_1 + stage_2", "0.5*steering_effort", "written score drops from 43 to 8 + 0.5*10 = 13", "problem statement said scraping was free", "free to choose damage", "proxy honesty", "matching a reference signal"]:
                if marker not in text:
                    errors.append(f"objective concept page missing tradeoff marker: {marker}")
            if len(words) < 900:
                errors.append(f"objective concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "horizon":
            for marker in ["60 meters from the pad", "18 percent battery", "full-speed flight uses 2 percent battery", "slow flight uses 1 percent battery", "A three-second horizon sees only the next 24 meters", "crosswind band from 25 meters to 40 meters", "at least 14 percent battery", "distance_3 = 3*8 = 24 meters", "battery_3 = 18 - 3*2 = 12 percent", "distance_3 = 3*4 = 12 meters", "battery_3 = 18 - 3*1 = 15 percent", "battery_at_wind &gt;= 14 percent", "dt = 0.5 seconds", "N = 60", "Too short is blind; too long can be expensive or misleading", "first consequence time"]:
                if marker not in text:
                    errors.append(f"horizon concept page missing delayed-consequence marker: {marker}")
            if len(words) < 900:
                errors.append(f"horizon concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "constraints":
            for marker in ["4 centimeters from the shelf", "12 newton-meters", "t = 0.4 seconds", "3 centimeters from the shelf", "t = 0.6 seconds", "15 newton-meters", "5 centimeters", "11 newton-meters", "3 &lt; 4 and 15 &gt; 12", "g(x,u) &lt;= 0", "g_clear,k = 0.04 - distance_to_shelf(x_k) &lt;= 0", "distance_to_shelf = 0.03", "g_clear = 0.04 - 0.03 = 0.01 &gt; 0", "g_tau,k = abs(tau_k) - 12 &lt;= 0", "g_tau = 15 - 12 = 3 &gt; 0", "g_clear = -0.01", "g_tau = -1", "defect_k = x_{k+1} - f(x_k,u_k) = 0", "shelf flex, cable snag, heat, or human clearance"]:
                if marker not in text:
                    errors.append(f"constraints concept page missing hard-limit marker: {marker}")
            if len(words) < 900:
                errors.append(f"constraints concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "feasibility":
            for marker in ["18 meters behind a stopped truck", "22 m/s", "wet-road braking limit of 6 m/s^2", "v^2/(2a) = 22^2/(2*6) = 40.3 meters", "0.5 meters of side clearance", "safety rule requires 1.5 meters", "concrete barrier is 0.8 meters away", "cheap collision path is not a plan with a high cost", "x_{k+1}=f(x_k,u_k)", "stop_distance &lt;= 18", "40.3 &lt;= 18 is false", "clearance_left &gt;= 1.5", "0.5 &gt;= 1.5 is false", "clearance_right &gt;= 1.5", "0.8 &gt;= 1.5 is false", "F(x_0) = empty set", "correct output is infeasibility", "J = 10,000", "illegal plan with J = 1", "model honesty and horizon length", "forgot a shoulder lane"]:
                if marker not in text:
                    errors.append(f"feasibility concept page missing empty-set marker: {marker}")
            if len(words) < 900:
                errors.append(f"feasibility concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "value-function":
            for marker in ["state S", "state R", "V(R)=18", "state H", "V(H)=7", "1 + 18 = 19", "4 + 7 = 11", "same V(R)=18", "f(S,rocky)=R", "f(S,smooth)=H", "Q(S,rocky)=1+V(R)=1+18=19", "Q(S,smooth)=4+V(H)=4+7=11", "V(S)=11", "V(R)=6", "1 + 6 = 7", "V(x)=min_u [cost(x,u) + V(f(x,u))]", "reward version", "battery heat, wheel damage, traffic, or a locked gate"]:
                if marker not in text:
                    errors.append(f"value-function concept page missing future-price marker: {marker}")
            if len(words) < 900:
                errors.append(f"value-function concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "bellman-recursion":
            for marker in ["state x = J", "V(C)=9", "V(L)=3", "2 + V(C) = 2 + 9 = 11", "5 + V(L) = 5 + 3 = 8", "V(J)=8", "pi(J)=B", "Bellman recursion is the one-step accounting identity", "V(x) = min_u [c(x,u) + V(f(x,u))]", "pi(x) = argmin_u [c(x,u) + V(f(x,u))]", "Q(J,A)=2+V(C)=11", "Q(J,B)=5+V(L)=8", "V(J)=min(11,8)=8", "sum_{x_next} P(x_next|x,u)V(x_next)", "stale map"]:
                if marker not in text:
                    errors.append(f"bellman concept page missing recursion marker: {marker}")
            if len(words) < 900:
                errors.append(f"bellman concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "stochastic-dynamic-programming":
            for marker in ["disturbance W", "probability 0.6", "W = straight", "probability 0.3", "W = slip-left", "probability 0.1", "W = slip-right", "0.6*5 + 0.3*12 + 0.1*20 = 8.6", "1 + 8.6 = 9.6", "4 + 0.9*4 + 0.1*9 = 8.5", "V(x) = min_u [cost(x,u) + E_W V(f(x,u,W))]", "P(x_next|x,u) V(x_next)", "P(straight|x,gravel)=0.6", "P(slip-left|x,gravel)=0.3", "P(slip-right|x,gravel)=0.1", "0.1*20 = 2", "rare catastrophic outcomes"]:
                if marker not in text:
                    errors.append(f"stochastic DP concept page missing expectation marker: {marker}")
            if len(words) < 900:
                errors.append(f"stochastic DP concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "dynamic-programming":
            for marker in ["V(G)=0", "V(A)=1", "V(R)=6", "1 + V(A) = 2", "3 + V(R) = 9", "V(M)=2", "2 + V(M) = 4", "1 + V(R) = 7", "V(S)=4", "V(s) = min_a [c(s,a) + V(next(s,a))]", "pi(M)=right", "pi(S)=east", "closed-loop policies", "100*5*4 = 2,000 state entries", "omits mud depth or battery health"]:
                if marker not in text:
                    errors.append(f"dynamic programming concept page missing backward-update marker: {marker}")
            if len(words) < 900:
                errors.append(f"dynamic programming concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "trajectory-optimization":
            for marker in ["1.2 seconds", "t = 0.0, 0.3, 0.6, 0.9, and 1.2 seconds", "foot height samples are 0.04, 0.18, 0.22, 0.12, and 0.00 meters", "box top is 0.16 meters", "torso lean is 17 degrees", "support limit is 12 degrees", "46 newton-meters", "40 newton-meters", "whole state-action history", "feedback tracker", "x_0...x_N and u_0...u_{N-1}", "J = sum_k [10*foot_error_k^2 + 0.01*torque_k^2]", "x_{k+1}=f(x_k,u_k)", "defect_k = x_{k+1} - f(x_k,u_k)", "defect_k = 0", "torso_lean_2 = 17 degrees", "torso_lean &lt;= 12 degrees", "torque_3 = 46", "torque &lt;= 40", "grid skips the instant", "contact model lies about foot slip"]:
                if marker not in text:
                    errors.append(f"trajectory optimization concept page missing path-history marker: {marker}")
            if len(words) < 900:
                errors.append(f"trajectory optimization concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "direct-transcription":
            for marker in ["0.0 rad to 1.2 rad", "5 newton-meter torque limit", "t = 0.0, 0.2, 0.4, and 0.6 seconds", "q_0=0.0, q_1=0.4, q_2=0.9, q_3=1.2", "tau_1=2 newton-meters", "q_2_pred = 0.6 rad", "q_2 - q_2_pred = 0.9 - 0.6 = 0.3 rad", "tau_1=8", "8 &gt; 5", "middle states and controls together", "x_k=[q_k,v_k]", "u_k=tau_k", "defect_k = x_{k+1} - step(x_k,u_k)", "defect_1 = q_2 - q_2_pred = 0.3 rad", "defect_1 = 0", "defect_k = 0", "-5 &lt;= tau_k &lt;= 5", "q_0=0 and q_3=1.2", "states as variables", "stop those exposed states from lying", "between t = 0.2 and t = 0.4"]:
                if marker not in text:
                    errors.append(f"direct transcription concept page missing defect marker: {marker}")
            if len(words) < 900:
                errors.append(f"direct transcription concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "shooting-methods":
            for marker in ["x = 0 meters", "u_0 = 4 m/s^2", "x_2 = 7 meters", "only u_0 and u_1 are decision variables", "residual r = [x_2 - 10, v_2 - 0]", "gap_1 = x_join - step(x_0,u_0)"]:
                if marker not in text:
                    errors.append(f"shooting methods concept page missing forward-shot marker: {marker}")
            if len(words) < 760:
                errors.append(f"shooting methods concept page below core richness floor: {len(words)} < 760")
        if concept.get("id") == "collocation":
            for marker in ["x = 0.02 meters", "x = 0.18 meters", "t = 0.2 seconds", "x = 0.10 meters", "x = 0.08 to 0.12 meters", "path_derivative_mid = 0.9 m/s", "f(x_mid,u_mid)=0.4 m/s", "local direction does not match the dynamics", "selected interior points to be physically honest", "defect_mid = path_derivative_mid - f(x_mid,u_mid)", "defect_mid = 0.9 - 0.4 = 0.5 m/s", "Driving defect_mid to 0", "clearance_mid &gt;= 0", "x_mid = 0.10 meters", "clearance_mid is negative", "t = 0.1, 0.2, and 0.3 seconds", "sampling and representation", "unmodeled flex, backlash, or contact event"]:
                if marker not in text:
                    errors.append(f"collocation concept page missing midpoint marker: {marker}")
            if len(words) < 900:
                errors.append(f"collocation concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "lqr":
            for marker in ["20 centimeters left", "e_next = e + u", "u = -0.190 meters", "x_{k+1}=A_k x_k + B_k u_k", "J(u)=u^2 + 20*(0.20 + u)^2", "K = 20/21", "actuator saturates"]:
                if marker not in text:
                    errors.append(f"LQR concept page missing feedback-gain marker: {marker}")
            if len(words) < 780:
                errors.append(f"LQR concept page below core richness floor: {len(words)} < 780")
        if concept.get("id") == "local-quadratic-approximation":
            for marker in ["6 centimeters too far left", "delta u = -0.02 meters", "delta u = 0.02 meters", "q(delta u) = c + g*delta u + 0.5*H*delta u^2", "delta u* = -g/H = 0.028 meters", "trust region"]:
                if marker not in text:
                    errors.append(f"local quadratic approximation concept page missing fitted-bowl marker: {marker}")
            if len(words) < 780:
                errors.append(f"local quadratic approximation concept page below core richness floor: {len(words)} < 780")
        if concept.get("id") == "reachability":
            for marker in ["5 meters apart", "0.6 meters per second", "0.4 meters per second", "T_bad = {gap &lt;= 0.3 meters}", "next_gap &lt;= 0.5 + 0.4 - 0.6 = 0.3", "backward avoidance set A_1", "for all disturbances, there must exist a control"]:
                if marker not in text:
                    errors.append(f"reachability concept page missing set-propagation marker: {marker}")
            if len(words) < 800:
                errors.append(f"reachability concept page below core richness floor: {len(words)} < 800")
        if concept.get("id") == "model-predictive-control":
            for marker in ["3.0 meters from a loading mark", "10:00:00", "-0.8 m/s^2", "v_next = v + dt*u", "p_next = p + dt*v_next", "velocity 0.60 m/s and position 3.30 meters", "3.53 meters and 3.70 meters", "old -0.6 and -0.2", "position 3.40 meters and velocity 0.50 m/s", "not the predicted 3.30 meters and 0.60 m/s", "shifted horizon", "10:00:00.5 to 10:00:02.0", "u_0...u_{N-1}", "x_0 = x_measured(k)", "pi_MPC(x_measured(k)) = u_0^*", "x_0 = x_measured(k+1)", "old tail [-0.6, -0.2]", "predicted state (3.30, 0.60)", "measured state (3.40, 0.50)", "solve takes 0.8 seconds", "control period is 0.5 seconds", "no feasible continuation", "Recursive feasibility and stability are extra promises"]:
                if marker not in text:
                    errors.append(f"MPC concept page missing receding-horizon marker: {marker}")
            if len(words) < 900:
                errors.append(f"MPC concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "recursive-feasibility":
            for marker in ["2.0 meters left before the stop line", "speed is below 0.2 m/s", "1.4 m/s with only 1.1 meters left", "handed 10:00.5 an impossible problem", "[u_0^*, u_1^*, u_2^*]", "[u_1^*, u_2^*, v_backup]", "X_F is controlled invariant"]:
                if marker not in text:
                    errors.append(f"recursive feasibility concept page missing shifted-tail marker: {marker}")
            if len(words) < 820:
                errors.append(f"recursive feasibility concept page below core richness floor: {len(words)} < 820")
        if concept.get("id") == "stability-under-replanning":
            for marker in ["1.5 meters left", "E = distance_error^2 + 0.5*sideways_speed^2", "E = 1.5^2 + 0.5*0.8^2 = 2.57", "E = 0.9^2 + 0.5*0.5^2 = 0.935", "1.0 meters right", "sideways speed 0.6 m/s left", "E = 1.0^2 + 0.5*0.6^2 = 1.18", "burden rose from 0.935 to 1.18", "terminal cost, terminal set, or a decrease condition", "x_{k+1}=f_closed(x_k)", "V(f_closed(x)) - V(x) &lt;= -stage_cost(x,pi_MPC(x))", "delta V = 0.935 - 2.57 = -1.635", "delta V = 1.18 - 0.935 = +0.245", "violates a nonincrease test", "Feasibility alone would only say the next optimization exists", "terminal set gives the final predicted state", "cycling, drifting, or amplifying velocity"]:
                if marker not in text:
                    errors.append(f"stability under replanning concept page missing decrease marker: {marker}")
            if len(words) < 900:
                errors.append(f"stability under replanning concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "imitation-learning":
            for marker in ["200 drawer pulls", "handle center x = 0.00 meters", "pull speed 0.04 m/s", "misses the handle by 3 centimeters", "handle may rotate 12 degrees", "sum_i ||pi_theta(x_i) - u_i^expert||^2", "x_{t+1}=f(x_t, pi_theta(x_t))", "x_j^learner"]:
                if marker not in text:
                    errors.append(f"imitation learning concept page missing demonstration-loop marker: {marker}")
            if len(words) < 900:
                errors.append(f"imitation learning concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "behavioral-cloning":
            for marker in ["1,000 centered-lane frames", "steering angle -12 degrees", "steering angle +12 degrees", "average label is 0 degrees", "L(theta)=sum_i ||pi_theta(x_i)-u_i^expert||^2", "50*(a - (-12))^2 + 50*(a - 12)^2", "squared-error optimum is a = 0 degrees", "no built-in exploration or reward signal"]:
                if marker not in text:
                    errors.append(f"behavioral cloning concept page missing supervised-action marker: {marker}")
            if len(words) < 900:
                errors.append(f"behavioral cloning concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "distribution-shift-imitation":
            for marker in ["within 10 centimeters of lane center", "understeers by only 2 centimeters", "second 4", "18 centimeters right", "3 of the 10,000 expert frames", "d_expert(x)", "d_pi(x)", "d_pi(18 cm right) much larger than d_expert(18 cm right)", "collect rollout states from d_pi"]:
                if marker not in text:
                    errors.append(f"distribution shift concept page missing learner-state marker: {marker}")
            if len(words) < 900:
                errors.append(f"distribution shift concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "reinforcement-learning":
            for marker in ["reward -1", "reward +10", "gamma = 0.9", "G_0 = 0 + 0.9*(-1) + 0.9^2*10 = 7.2", "40 newtons", "(x_t,u_t,r_t,x_{t+1})", "E[sum_t gamma^t r_t]", "y = r_t + gamma max_{u&#x27;} Q(x_{t+1},u&#x27;)", "omitting tearing force"]:
                if marker not in text:
                    errors.append(f"reinforcement learning concept page missing rollout-return marker: {marker}")
            if len(words) < 900:
                errors.append(f"reinforcement learning concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "reward":
            for marker in ["10 - 6 = 4", "35 newtons", "10 - 1 = 9", "-0.5 per newton above 8", "-20 if the cup is damaged", "r(x,u,x_next)", "G_0 = sum_t gamma^t r_t", "10 - 1 - 0.5*(35 - 8) - 20 = -24.5", "optimized the written measuring stick"]:
                if marker not in text:
                    errors.append(f"reward concept page missing scalar-loophole marker: {marker}")
            if len(words) < 900:
                errors.append(f"reward concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "policy":
            for marker in ["distance_to_wall = 0.45 meters", "battery = 38 percent", "distance_to_wall &lt; 0.50 meters", "steering = -18 degrees", "pi(slow-left|x) = 0.8", "pi(hard-left|x) = 0.2", "u = pi(x)", "pi(u|x)", "x_{t+1}=f(x_t,u_t)", "omits a needed state variable"]:
                if marker not in text:
                    errors.append(f"policy concept page missing closed-loop-rule marker: {marker}")
            if len(words) < 900:
                errors.append(f"policy concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "state":
            for marker in ["y = 0.20 meters", "v_y = 0.00 m/s", "psi = 0 degrees", "v_y = -1.50 m/s", "psi = -8 degrees", "u = +5 degrees", "dt = 0.2 seconds", "y_next = y + dt*v_y", "0.20 + 0.2*0.00 = 0.20 meters", "0.20 + 0.2*(-1.50) = -0.10 meters", "x_{t+1}=f(x_t,u_t)", "same action distribution over next states", "x=[y]", "x=[y,v_y,psi]", "hidden battery temperature, tire grip, load mass"]:
                if marker not in text:
                    errors.append(f"state concept page missing predictive-memory marker: {marker}")
            if len(words) < 900:
                errors.append(f"state concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "static-optimization":
            for marker in ["one charging power z", "6 kilowatts", "4 kilowatts", "J(z) = (z - 6)^2", "0 &lt;= z &lt;= 4", "J(4) = (4 - 6)^2 = 4", "J(3) = 9", "J(0) = 36", "minimize_z J(z)", "g_i(z) &lt;= 0", "h_j(z) = 0", "dJ/dz = 2*(z - 6) = 0", "active outlet boundary z = 4", "temperature_next = f(temperature,z)"]:
                if marker not in text:
                    errors.append(f"static optimization concept page missing one-shot-decision marker: {marker}")
            if len(words) < 900:
                errors.append(f"static optimization concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "gradient-first-order-condition":
            for marker in ["J(z) = (z - 3)^2 + 0.2*z^2", "dJ/dz = 2*(0 - 3) + 0.4*0 = -6", "delta z = +0.1", "-6*0.1 = -0.6", "z = 2.5", "J(2.4) = (2.4 - 3)^2 + 0.2*2.4^2 = 1.512", "J(2.5) = 1.5", "J(2.6) = 1.512", "steering stop z &lt;= 2.0", "dJ/dz = 2*(2 - 3) + 0.4*2 = -1.2", "delta z = +0.1 is illegal", "boundary with nonzero slope", "rock begins at steering above 2.3 degrees", "J(z + delta z)", "grad J(z)^T delta z &lt; 0", "grad J(z) = 0", "delta z &lt;= 0", "grad J(2.0) = -1.2", "(-1.2)*(-0.1)=+0.12", "downhill move delta z = +0.1 would give -0.12", "constrained local minimum can have a nonzero gradient", "localness and model honesty", "not proof of global optimality"]:
                if marker not in text:
                    errors.append(f"gradient first-order condition page missing local-slope marker: {marker}")
            if len(words) < 900:
                errors.append(f"gradient first-order condition page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "calculus-of-variations":
            for marker in ["1 meter rail in 2 seconds", "u(t) from t = 0 to t = 2", "0.5 m/s", "x(2) = 1 meter", "0.8 m/s", "0.2 m/s", "J[u] = integral_0^2 u(t)^2 dt", "2*(0.5^2) = 0.5", "1*(0.8^2) + 1*(0.2^2) = 0.68", "epsilon*eta(t)", "d/depsilon J[u + epsilon*eta]", "x_dot = u", "integral_0^2 eta(t) dt = 0", "smooth admissible perturbations"]:
                if marker not in text:
                    errors.append(f"calculus of variations concept page missing curve-perturbation marker: {marker}")
            if len(words) < 900:
                errors.append(f"calculus of variations concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "costate-adjoint-variable":
            for marker in ["height 10 meters after two seconds", "x_next = x + u", "100*(x_2 - 10)^2", "100*(0.1^2) = 1", "x_1 = 9.4 meters", "200*(x_1 + u_1 - 10)", "u_1 is 0.5", "final height is 9.9", "derivative is -20", "p(t)", "x_dot = f(x,u)", "lambda_2 = d terminal_cost/dx_2", "lambda_2 = -20", "lambda_1 = lambda_2*1 = -20", "x_2 = 0.5*x_1 + u_1", "lambda_1 = -10", "omitted heat, collision, or actuator wear"]:
                if marker not in text:
                    errors.append(f"costate concept page missing backward-price marker: {marker}")
            if len(words) < 900:
                errors.append(f"costate concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "hamiltonian-optimal-control":
            for marker in ["running cost is 0.5*u^2", "x_dot = u", "p = -20", "H = 0.5*u^2 + p*u", "u = 0: H = 0", "u = 10: H = 50 - 200 = -150", "u = 20: H = 200 - 400 = -200", "u = 30: H = 450 - 600 = -150", "H(x,u,p)=L(x,u)+p*f(x,u)", "H(u)=0.5*u^2 - 20*u", "dH/du = u - 20 = 0", "augment the cost with the constraint", "u &lt;= 12", "omits motor heat"]:
                if marker not in text:
                    errors.append(f"Hamiltonian concept page missing local-accounting marker: {marker}")
            if len(words) < 900:
                errors.append(f"Hamiltonian concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "indirect-methods":
            for marker in ["x(0)=0 meters", "x(2)=1 meter", "x_dot = u", "running cost is 0.5*u^2", "H = 0.5*u^2 + p*u", "dH/du = u + p = 0", "u = -p", "p_dot = 0", "p(0) = -0.3", "x(2)=0.6", "0.4 meters short", "p(0) = -0.7", "x(2)=1.4", "p(0) = -0.5", "u(t)=0.5", "x(t)=0.5*t", "partial H/partial p", "partial H/partial u = 0", "r(p0)=x(2;p0)-1", "wrong derivation"]:
                if marker not in text:
                    errors.append(f"indirect methods concept page missing boundary-value marker: {marker}")
            if len(words) < 900:
                errors.append(f"indirect methods concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "value-based-rl":
            for marker in ["battery 22 percent", "Q(x,turn_left) = 3", "Q(x,turn_right) = 7", "gamma = 0.9", "y = -1 + 0.9*10 = 8", "alpha = 0.5", "7 + 0.5*(8 - 7) = 7.5", "V_pi(x)", "Q_pi(x,u)", "policy evaluation", "policy improvement", "Q(x,u) &lt;- Q(x,u) + alpha*(y - Q(x,u))", "slick floors"]:
                if marker not in text:
                    errors.append(f"value-based RL concept page missing value-update marker: {marker}")
            if len(words) < 900:
                errors.append(f"value-based RL concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "policy-optimization":
            for marker in ["body leaning forward 6 degrees", "right knee bent 20 degrees", "pi_theta(long_step|x) = 0.30", "pi_theta(short_step|x) = 0.70", "return G = 12", "return G = 2", "pi_theta_new(long_step|x) = 0.38", "J(theta)=E_{tau~pi_theta}[G(tau)]", "grad_theta log pi_theta(u_t|x_t) * A_t", "theta_new = theta + eta*g", "surrogate objective", "Noisy returns"]:
                if marker not in text:
                    errors.append(f"policy optimization concept page missing direct-policy-update marker: {marker}")
            if len(words) < 900:
                errors.append(f"policy optimization concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "exploration":
            for marker in ["18 newtons", "0.04 m/s", "7 out of 10 times", "12 degrees with 22 newtons", "60 newtons", "epsilon = 0.10", "10 of 100 attempts", "force &lt;= 25 newtons", "handle_angle &lt;= 15 degrees", "9 out of 10 times", "pi_explore(u|x) = 1 - epsilon", "Q(x,u) + beta*uncertainty(x,u)", "coverage under constraints"]:
                if marker not in text:
                    errors.append(f"exploration concept page missing constrained-coverage marker: {marker}")
            if len(words) < 900:
                errors.append(f"exploration concept page below core richness floor: {len(words)} < 900")
        if concept.get("id") == "model-based-rl":
            for marker in ["0.20 meters before a shelf", "80 real trials", "position 1.40 m", "brake 30 percent", "x_next = (position 1.46 m, velocity 0.48 m/s)", "f_hat(x,u)", "final position 0.08 meters", "final position 0.24 meters", "executes only the first brake command", "x_{t+1}=f_hat(x_t,u_t)", "p_hat(x_{t+1}|x_t,u_t)", "[u_0,u_1,u_2]", "20 possible models", "underestimates braking distance by 0.10 meters"]:
                if marker not in text:
                    errors.append(f"model-based RL concept page missing learned-model-planning marker: {marker}")
            if len(words) < 900:
                errors.append(f"model-based RL concept page below core richness floor: {len(words)} < 900")
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
