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
            for marker in ["80 meters above the pad", "18 m/s", "12 seconds of fuel", "dt = 1 second", "x = (height, velocity, fuel)", "u_0 = 18", "u_1 = 8", "velocity changes from -18 to -10 m/s", "height falls to 70 meters", "fuel drops from 12 to -24", "u_0 = 4", "u_1 = 2", "velocity is -32 m/s", "height is 24 meters", "fuel is 0", "legal on fuel but headed for a hard crash", "u_0 = 3", "u_1 = 3", "h_2 = 23 meters", "v_2 = -32 m/s", "A is rejected before scoring", "2*u_0 + 2*u_1 &lt;= 12", "u_0 + u_1 &lt;= 6", "gravity subtracts 20 m/s", "v_2 = -18 + 6 - 20 = -32 m/s", "not inside this written problem", "choose u_0...u_{N-1}", "J = sum_k fuel_cost(u_k) + 100*landing_error^2 + 20*touchdown_speed^2", "x_{k+1}=f(x_k,u_k)", "fuel_k &gt;= 0", "v_{k+1}=v_k + dt*(u_k - 10)", "h_{k+1}=h_k + dt*v_{k+1}", "fuel_{k+1}=fuel_k - 2*u_k", "12 - 2*4 - 2*2 = 0", "100*(24 - 0)^2 + 20*(-32)^2 = 78,080", "12 - 2*3 - 2*3 = 0", "100*(23 - 0)^2 + 20*(-32)^2 = 73,380", "feasibility check is separate from the ranking check", "sum_u = u_0 + u_1 &lt;= 6", "v_2 = -18 + sum_u - 20", "every legal sequence has v_2 &lt;= -32", "|v_2| &lt;= 2", "feasible set is empty", "not to tune weights harder", "add fuel, lengthen the horizon"]:
                if marker not in text:
                    errors.append(f"optimal control problem page missing trajectory-chain marker: {marker}")
            if len(words) < 1160:
                errors.append(f"optimal control problem page below core richness floor: {len(words)} < 1160")
        if concept.get("id") == "action-control-input":
            for marker in ["h = 10 meters", "v = 0.2 m/s", "48 percent above hover", "dt = 0.1 seconds", "a(u)=4.8 m/s^2", "v_next = 0.2 + 0.1*4.8 = 0.68 m/s", "h_next = 10 + 0.1*0.68 = 10.068 meters", "6.8 centimeters", "u = 0.9, meaning 90 percent above hover", "u_sent = 0.5", "0.2 + 0.1*5.0 = 0.70 m/s", "next height is 10.070 meters", "u_prev = 0.10", "change thrust by only 0.20 per tick", "u_rate = 0.30", "a(u_rate)=3.0 m/s^2", "v_next = 0.2 + 0.1*3.0 = 0.50 m/s", "h_next = 10 + 0.1*0.50 = 10.050 meters", "battery_temp = 46 C", "safe set may shrink to u &lt;= 0.25", "u_hot = 0.25", "a(u_hot)=2.5 m/s^2", "next height is only 10.045 meters", "north, south, east, west is discrete", "u = 0.37 is continuous", "limits, rate changes, motors, acceleration, velocity, and only then position", "a(u)=10*u", "-0.3 &lt;= u &lt;= 0.5", "v_next = v + dt * a(u)", "h_next = h + dt * v_next", "u_clipped = min(0.9,0.5) = 0.5", "a=5.0 m/s^2", "v_next = 0.2 + 0.1*5.0 = 0.70", "h_next = 10 + 0.1*0.70 = 10.070", "|u - u_prev| &lt;= 0.20", "u_rate = 0.30 for this tick", "a(u_rate)=3.0", "v_next = 0.2 + 0.1*3.0 = 0.50", "h_next = 10 + 0.1*0.50 = 10.050", "U(x)", "U(x_hot) = [-0.3, 0.25]", "u_safe = min(0.48,0.25) = 0.25", "h_next = 10 + 0.1*(0.2 + 0.1*2.5) = 10.045", "if |u| &lt; 0.05, then a(u)=0", "u = 0.03", "h_next = 10.020", "x_next = f(x, u_rate)", "command that actually reaches the plant", "(h_next - 12)^2", "actuator truth", "delay, saturation, dead zones, state-dependent safe sets, and rate limits"]:
                if marker not in text:
                    errors.append(f"action concept page missing command-vs-outcome marker: {marker}")
            if len(words) < 1220:
                errors.append(f"action concept page below core richness floor: {len(words)} < 1220")
        if concept.get("id") == "dynamics":
            for marker in ["speed 20 m/s", "theta = 0 degrees", "u = 5 degrees", "dt = 0.2 seconds", "yaw_rate = 0.30 rad/s", "theta_next = 0 + 0.2*0.30 = 0.06 rad", "yaw_rate = 0.05 rad/s", "v_y = -1.0 m/s", "theta_next = 0 + 0.2*0.05 = 0.01 rad", "y_next = y + 0.2*(-1.0)", "three ticks", "theta = 0.18 rad after 0.6 seconds", "theta = 0.03 rad", "y = -0.6 meters", "u_now = 5 degrees", "u_prev = 0 degrees", "first yaw rate is 0.00 rad/s", "theta_next stays 0.00 rad", "following tick, not this one", "shower example from the lecture", "hot_command = 44 C", "water at the shower head is 36 C", "pipe wall is 30 C", "water_next = water + 0.4*(pipe - water) + 0.2*(hot_command - water)", "pipe_next = pipe + 0.3*(hot_command - pipe)", "water_next = 36 + 0.4*(30-36) + 0.2*(44-36) = 35.2 C", "pipe_next = 30 + 0.3*(44-30) = 34.2 C", "water_next2 = 35.2 + 0.4*(34.2-35.2) + 0.2*(44-35.2) = 36.56 C", "water_next = hot_command", "real water is still around 35 C", "heat storage", "x_next = f(x,u)", "dx/dt = f(x,u)", "x=[y,theta,v_y,speed]", "f_dry", "f_ice", "theta_3 = 3*0.2*0.30 = 0.18 rad", "theta_3 = 3*0.2*0.05 = 0.03 rad", "y_3 = 3*0.2*(-1.0) = -0.6 meters", "u_applied = u_prev", "theta_next = theta + dt*yaw_rate(x,u_prev,grip)", "yaw_rate = 0.00 rad/s", "theta_next = 0 + 0.2*0.00 = 0.00 rad", "u_now = 5 degrees has just been requested", "carry u_now forward as the future u_prev", "one-tick delay", "x=[water_temp,pipe_temp]", "u=hot_command", "water_{k+1}=water_k + 0.4*(pipe_k-water_k) + 0.2*(u_k-water_k)", "pipe_{k+1}=pipe_k + 0.3*(u_k-pipe_k)", "x_0=[36,30]", "water_1=35.2 and pipe_1=34.2", "water_2=36.56", "state were only x=[water_temp]", "pipe temperatures 30 C and 42 C", "water_next = 36 + 0.4*(42-36) + 0.2*(44-36) = 40.0 C", "same water reading and handle command", "no pipe state while the shower has heat storage", "model fidelity"]:
                if marker not in text:
                    errors.append(f"dynamics concept page missing state-update marker: {marker}")
            if len(words) < 1320:
                errors.append(f"dynamics concept page below core richness floor: {len(words)} < 1320")
        if concept.get("id") == "objective-cost-function":
            for marker in ["Path A reaches the spot in 8 seconds", "Path B takes 12 seconds", "8 is smaller than 12", "steering effort 10", "wall risk 30", "steering effort 3", "Path A: 8 + 0.5*10 + 1.0*30 = 43", "Path B: 12 + 0.5*3 + 1.0*0 = 13.5", "wall weight 0", "Path A scores 13 and beats 13.5", "clearance must be at least 10 centimeters", "Path A is illegal because 6 &lt; 10", "soft wall penalty trades wall risk against time", "hard wall constraint refuses the trade", "thermostat from the course overview", "room target is 70 F", "temperatures 69, 70, 71", "uses 3 heater units", "Plan B keeps 67, 68, 70", "uses 1 heater unit", "temperature_error^2 + 0.2*heat", "total 2.6", "total 13.2", "energy weight rises to 5.0", "Plan A adds 15 and scores 17", "Plan B adds 5 and scores 18", "terminal cost pays 20*(final_error)^2", "B wins despite worse early tracking", "68 &lt;= temp &lt;= 72", "Plan B starts at 67 F", "rejected before scoring", "written measurement of what counts as better", "J = sum_k stage_cost(x_k,u_k) + terminal_cost(x_N)", "w_wall*wall_risk", "stage_0 + stage_1 + stage_2", "0.5*steering_effort", "A has base score 8 + 0.5*10 = 13", "B has 12 + 0.5*3 = 13.5", "30*w_wall", "13 + 30*w_wall &lt; 13.5", "w_wall &lt; 0.5/30 = 0.0167", "Any wall weight above 0.0167 flips the written choice to B", "clearance_A = 0.06 meters", "clearance_min = 0.10 meters", "clearance_A - clearance_min = -0.04 meters", "A is infeasible before J is compared", "stage_cost_k=(temp_k - 70)^2 + alpha*heat_k", "terminal_cost=beta*(temp_3 - 70)^2", "alpha=0.2 and beta=0", "J_A=(1+0+1)+0.2*3=2.6", "J_B=(9+4+0)+0.2*1=13.2", "alpha=5 and beta=0", "J_A=2+15=17", "J_B=13+5=18", "alpha=5 and beta=20", "J_A=17+20*(1^2)=37", "J_B=18+20*(0^2)=18", "67 - 68 = -1", "B is infeasible even though its terminal value is good", "written exchange rates and written constraints changed", "follows the score and the feasibility rules", "proxy honesty"]:
                if marker not in text:
                    errors.append(f"objective concept page missing tradeoff marker: {marker}")
            if len(words) < 1260:
                errors.append(f"objective concept page below core richness floor: {len(words)} < 1260")
        if concept.get("id") == "horizon":
            for marker in ["60 meters from the pad", "18 percent battery", "full-speed flight uses 2 percent battery", "slow flight uses 1 percent battery", "A three-second horizon sees only the next 24 meters", "crosswind band from 25 meters to 40 meters", "at least 14 percent battery", "five-second horizon", "distance_5 = 5*8 = 40 meters", "battery_5 = 18 - 5*2 = 8 percent", "violates the 14 percent reserve rule", "ten-second horizon", "Full speed would travel 80 meters", "overshooting the 60 meter pad by 20 meters", "slow speed would be only 40 meters", "neither simple plan is acceptable", "shaped speed plan", "charging stop, or a different route", "120-second horizon", "guessed storm cell after landing", "50 percent battery penalty", "not useful for the first 5 seconds of flight", "weak far-future story", "price a story instead of the flight", "distance_3 = 3*8 = 24 meters", "battery_3 = 18 - 3*2 = 12 percent", "distance_3 = 3*4 = 12 meters", "battery_3 = 18 - 3*1 = 15 percent", "At 5 seconds", "distance_5 = 40 meters", "battery_5 = 8 percent", "battery_at_wind = 8 &lt; 14", "At 10 seconds", "distance_10 = 10*8 = 80 meters", "overshoot_10 = 80 - 60 = 20 meters", "distance_10 = 10*4 = 40 meters", "battery_10 = 18 - 10*1 = 8 percent", "battery_at_wind &gt;= 14 percent", "dt = 0.5 seconds", "N = 60", "t_event = 25/8 = 3.125 seconds", "3 &lt; 3.125", "5 &gt;= 3.125", "band exit at 40/8 = 5 seconds", "added model is trusted", "storm_penalty = 0.5*50 = 25 expected battery points", "swamp the near wind reserve", "Too short is blind; too long can be expensive or misleading", "first consequence time", "first action still leaves a legal future"]:
                if marker not in text:
                    errors.append(f"horizon concept page missing delayed-consequence marker: {marker}")
            if len(words) < 1340:
                errors.append(f"horizon concept page below core richness floor: {len(words)} < 1340")
        if concept.get("id") == "constraints":
            for marker in ["4 centimeters from the shelf", "12 newton-meters", "t = 0.4 seconds", "3 centimeters from the shelf", "t = 0.6 seconds", "15 newton-meters", "5 centimeters", "11 newton-meters", "3 &lt; 4 and 15 &gt; 12", "2 points per missing centimeter", "Candidate C uses only 4 energy points", "2 centimeters from the shelf", "4 + 2*(4 - 2) = 8", "8 &lt; 11", "Candidate C must still be rejected", "wrist would like torque 14", "minimizes (tau - 14)^2", "tau = 14 illegal", "best legal torque is tau = 12", "upper torque constraint is active", "tau = 10", "2 newton-meters of slack", "From tau = 12", "move upward", "leaves the feasible interval", "both small upward and downward changes are still legal", "Constraints also have addresses in time", "Candidate D stays 5 centimeters", "never asks for more than 10 newton-meters", "camera 6 centimeters away", "final_pose_error &lt;= 1 centimeter", "middle path limits passed", "clean endpoint cannot forgive an illegal middle", "clean middle cannot forgive a missed endpoint", "initial_clearance = 2 centimeters", "initial_clearance &gt;= 4 centimeters", "illegal before the first command", "g(x,u) &lt;= 0", "g_clear,k = 0.04 - distance_to_shelf(x_k) &lt;= 0", "distance_to_shelf = 0.03", "g_clear = 0.04 - 0.03 = 0.01 &gt; 0", "g_tau,k = abs(tau_k) - 12 &lt;= 0", "g_tau = 15 - 12 = 3 &gt; 0", "g_clear = -0.01", "g_tau = -1", "Candidate C has distance 0.02", "g_clear = 0.04 - 0.02 = 0.02 &gt; 0", "rho*max(0,g_clear)", "100*0.02 = 2", "not the same statement as g_clear &lt;= 0", "J(tau)=(tau - 14)^2", "-12 &lt;= tau &lt;= 12", "unconstrained minimizer is tau = 14", "violates tau &lt;= 12", "g_upper(tau)=tau - 12 = 0", "upper bound is active", "g_upper(tau)=10 - 12 = -2", "bound is inactive", "defect_k = x_{k+1} - f(x_k,u_k) = 0", "h_0(x_0)=0", "g_k(x_k,u_k) &lt;= 0 for every k", "h_N(x_N)=0", "|pose_error_N| &lt;= 0.01", "pose_error_N = 0.06 meters", "pose_error_N - 0.01 = 0.05 &gt; 0", "0.04 - initial_clearance = 0.02 &gt; 0", "shelf flex, cable snag, heat, or human clearance"]:
                if marker not in text:
                    errors.append(f"constraints concept page missing hard-limit marker: {marker}")
            if len(words) < 1320:
                errors.append(f"constraints concept page below core richness floor: {len(words)} < 1320")
        if concept.get("id") == "feasibility":
            for marker in ["18 meters behind a stopped truck", "22 m/s", "wet-road braking limit of 6 m/s^2", "v^2/(2a) = 22^2/(2*6) = 40.3 meters", "0.5 meters of side clearance", "safety rule requires 1.5 meters", "concrete barrier is 0.8 meters away", "45 meters behind the truck", "40.3 &lt;= 45 is true", "4.7 meters of stopping margin", "feasible set is not empty", "cheap collision path is not a plan with a high cost", "legal shoulder opening 12 meters ahead", "did not include the shoulder lane as an action family", "two-step escape", "brake hard for 0.5 seconds", "dropping speed from 22 to 19 m/s", "using about 10 meters", "2.0 meters of side clearance", "wait 0.2 seconds before braking", "travel about 4.4 meters", "18 - 4.4 - 10.25 = 3.35 meters", "needs 4.0 meters to merge", "residual is 4.0 - 3.35 = 0.65 meters", "Close is not feasible", "old empty set was true for the old model", "richer action set", "x_{k+1}=f(x_k,u_k)", "stop_distance &lt;= 18", "40.3 &lt;= 18 is false", "clearance_left &gt;= 1.5", "0.5 &gt;= 1.5 is false", "clearance_right &gt;= 1.5", "0.8 &gt;= 1.5 is false", "F_old(x_0) = empty set", "every allowed family has at least one failed row", "not merely that the cheapest sampled row failed", "x_safe with truck_distance = 45 meters", "stop_distance &lt;= 45", "F(x_safe) contains at least the full-brake plan", "u_shoulder", "v_1 = 22 - 6*0.5 = 19 m/s", "d_used = 0.5*(22 + 19)*0.5 = 10.25 meters", "18 - 10.25 = 7.75 meters", "shoulder certificate has three rows", "braking acceleration -6 &gt;= -6 passes", "shoulder clearance 2.0 &gt;= 1.5 passes", "merge_distance_needed 4.0 &lt;= 7.75 passes", "u_shoulder belongs to F_new(x_0)", "One passing certificate is enough to prove F_new(x_0) is not empty", "proving emptiness requires ruling out every allowed certificate", "d_wait = 22*0.2 = 4.4 meters", "remaining gap is 3.35 meters", "4.0 &lt;= 3.35, false", "positive residuals", "legal candidate to compare", "J = 10,000", "illegal plan with J = 1", "model honesty and horizon length", "forgot a shoulder lane"]:
                if marker not in text:
                    errors.append(f"feasibility concept page missing empty-set marker: {marker}")
            if len(words) < 1320:
                errors.append(f"feasibility concept page below core richness floor: {len(words)} < 1320")
        if concept.get("id") == "value-function":
            for marker in ["state S", "state R", "V(R)=18", "state H", "V(H)=7", "1 + 18 = 19", "4 + 7 = 11", "same V(R)=18", "V_repaired(R)=9", "1 + 9 = 10", "beats smooth 11", "different road also reaches R", "bridge after R closes at noon", "bridge_open=true", "V_open(R)=9", "bridge_open=false", "V_closed(R)=24", "keep using 9 after the bridge closes", "true cost is 1 + 24 = 25", "stale or attached to an incomplete state", "state facts and model facts match", "f(S,rocky)=R", "f(S,smooth)=H", "Q(S,rocky)=1+V(R)=1+18=19", "Q(S,smooth)=4+V(H)=4+7=11", "V(S)=11", "Q(S,rocky)=1+9=10", "V(S)=10", "V(R)=6", "1 + 6 = 7", "x_R_open=(R,bridge_open=true)", "V(x_R_open)=9", "x_R_closed=(R,bridge_open=false)", "V(x_R_closed)=24", "one number to price two different futures", "Q_old(S,rocky)=1+V_old(R)=1+9=10", "Q_closed(S,rocky)=1+V(x_R_closed)=1+24=25", "action flips back to smooth", "V(x)=min_u [cost(x,u) + V(f(x,u))]", "reward version", "battery heat, wheel damage, traffic, bridge_open, or a locked gate", "repair station, cost, or allowed policy changes"]:
                if marker not in text:
                    errors.append(f"value-function concept page missing future-price marker: {marker}")
            if len(words) < 1320:
                errors.append(f"value-function concept page below core richness floor: {len(words)} < 1320")
        if concept.get("id") == "bellman-recursion":
            for marker in ["state x = J", "V(C)=9", "V(L)=3", "2 + V(C) = 2 + 9 = 11", "5 + V(L) = 5 + 3 = 8", "V(J)=8", "pi(J)=B", "V(L)=14", "B to 5 + 14 = 19", "junction switches to A", "time t=1", "shelf state S", "V_2(goal)=0", "V_2(wrong_shelf)=40", "4 + 0 = 4", "1 + 40 = 41", "V_1(S)=4", "pi_1(S)=slow_scan", "cyclic hallway", "V_old(P)=10", "V_old(Q)=1", "min(6, 1 + V_old(Q)) = min(6,2) = 2", "P was overpriced by 8", "min(4, 1 + V_new(P)) = min(4,3) = 3", "Q was underpriced by 2", "min(6, 1 + V_new(Q)) = min(6,4) = 4", "table and the backups stop disagreeing", "stored numbers are consistent", "Bellman recursion is the one-step accounting identity", "V(x) = min_u [c(x,u) + V(f(x,u))]", "pi(x) = argmin_u [c(x,u) + V(f(x,u))]", "Q(J,A)=2+V(C)=11", "Q(J,B)=5+V(L)=8", "V(J)=min(11,8)=8", "Q(J,B)=5+14=19", "V(J)=min(11,19)=11", "pi(J)=A", "consistency equation", "V(goal)=0", "V_k(x)=min_u [c_k(x,u)+V_{k+1}(f_k(x,u))]", "Q_1(S,slow_scan)=4+V_2(goal)=4", "Q_1(S,rush)=1+V_2(wrong_shelf)=41", "V_1(S)=min(4,41)=4", "time may need to be part of the state", "forgot the deadline", "left side V(x) and the right side min expression agree", "Bellman_rhs(P;V_old)=min(6,1+V_old(Q))=2", "residual_P = V_old(P) - Bellman_rhs = 10 - 2 = 8", "Bellman_rhs(Q;V_new)=min(4,1+V_new(P))=3", "residual_Q = V_old(Q) - 3 = -2", "Bellman_rhs(P;V_new)=min(6,1+V_new(Q))=4", "earlier P repair to 2 is no longer consistent", "V(P)=min(6,1+V(Q))", "V(Q)=min(4,1+V(P))", "sum_{x_next} P(x_next|x,u)V(x_next)", "stale map"]:
                if marker not in text:
                    errors.append(f"bellman concept page missing recursion marker: {marker}")
            if len(words) < 1320:
                errors.append(f"bellman concept page below core richness floor: {len(words)} < 1320")
        if concept.get("id") == "stochastic-dynamic-programming":
            for marker in ["disturbance W", "probability 0.6", "W = straight", "probability 0.3", "W = slip-left", "probability 0.1", "W = slip-right", "probabilities must add to 1.0", "0.6*5 + 0.3*12 + 0.1*20 = 8.6", "1 + 8.6 = 9.6", "4 + 0.9*4 + 0.1*9 = 8.5", "slip-right is serious but not enormous, say value 60", "1 + 0.6*5 + 0.3*12 + 0.1*60 = 13.6", "broken axle with repair cost 200", "1 + 0.6*5 + 0.3*12 + 0.1*200 = 27.6", "P(straight)=0.68", "P(slip-left)=0.30", "P(slip-right)=0.02", "1 + 0.68*5 + 0.30*12 + 0.02*20 = 8.4", "50 gravel crossings", "24/50 = 0.48", "18/50 = 0.36", "8/50 = 0.16", "1 + 0.48*5 + 0.36*12 + 0.16*20 = 10.92", "detour wins again", "weather flag", "92 straight, 48 slip-left, and 10 slip-right out of 150", "P_mix(slip-right)=10/150=0.0667", "1 + (92/150)*5 + (48/150)*12 + (10/150)*20 = 9.24", "wrong for both jobs", "A good state label separates facts", "averages unlike situations", "V(x) = min_u [cost(x,u) + E_W V(f(x,u,W))]", "P(x_next|x,u) V(x_next)", "P(straight|x,gravel)=0.6", "P(slip-left|x,gravel)=0.3", "P(slip-right|x,gravel)=0.1", "P(straight|x,gravel)+P(slip-left|x,gravel)+P(slip-right|x,gravel)=1.0", "0.1*20 = 2", "0.1*60 = 6", "0.1*200 = 20", "Q_dry(x,gravel)=1+0.68*5+0.30*12+0.02*20=8.4", "P_hat(straight)=24/50=0.48", "P_hat(slip-left)=18/50=0.36", "P_hat(slip-right)=8/50=0.16", "Q_wet(x,gravel)=1+0.48*5+0.36*12+0.16*20=10.92", "transition model changed", "wet gravel and dry gravel share one state label", "P(W_k|X_k,U_k)", "not on X_{k-1}, X_{k-2}", "x = (location=gravel, weather=wet)", "separate transition rows", "Costs can also be random", "0.6*(1+5) + 0.3*(1+3+12) + 0.1*(1+7+20) = 11.2", "branch costs are averaged with the branch futures", "rare catastrophic outcomes", "With slip-right value 60, expectation ranks gravel at 13.6 minutes", "P(broken_axle) &lt;= 0", "reject gravel regardless of its average", "hard safety constraint or a risk measure"]:
                if marker not in text:
                    errors.append(f"stochastic DP concept page missing expectation marker: {marker}")
            if len(words) < 1340:
                errors.append(f"stochastic DP concept page below core richness floor: {len(words)} < 1340")
        if concept.get("id") == "dynamic-programming":
            for marker in ["V(G)=0", "V(A)=1", "V(R)=6", "1 + V(A) = 2", "3 + V(R) = 9", "V(M)=2", "2 + V(M) = 4", "1 + V(R) = 7", "V(S)=4", "S-east-M-right-A-goal", "S-south-R-slow-goal", "does not reopen M", "another earlier cell T", "4 + V(M) = 6", "2 + V(R) = 8", "S and T both borrow the same V(M)=2", "M-right-A-goal", "feedback table", "V_new(R)=2", "3 + V_new(R) = 5", "1 + V_new(R) = 3", "V_new(S)=3", "pi_new(S)=south", "west now costs 2 + V_new(R) = 4", "pi_new(T)=west", "flip one earlier decision while leaving another alone", "changed future price travels backward", "V(s) = min_a [c(s,a) + V(next(s,a))]", "pi(M)=right", "pi(S)=east", "closed-loop policies", "V(T)=min(4+V(M), 2+V(R)) = min(6,8) = 6", "pi(T)=north", "min(1+V(A), 3+V_new(R)) = min(2,5) = 2", "V_new(M)=2", "pi_new(M)=right", "min(2+V_new(M), 1+V_new(R)) = min(4,3) = 3", "min(4+V_new(M), 2+V_new(R)) = min(6,4) = 4", "V_new(T)=4", "local value change be propagated", "100*5*4 = 2,000 state entries", "100*5*4*20*10 = 400,000 entries", "3 legal actions per state", "400,000*3 = 1,200,000 action branches", "50 sweeps", "60,000,000 branch checks", "computationally intensive", "omits mud depth or battery health", "one number V(R) falsely prices two different futures", "honest and small enough to cover"]:
                if marker not in text:
                    errors.append(f"dynamic programming concept page missing backward-update marker: {marker}")
            if len(words) < 1240:
                errors.append(f"dynamic programming concept page below core richness floor: {len(words)} < 1240")
        if concept.get("id") == "trajectory-optimization":
            for marker in ["1.2 seconds", "t = 0.0, 0.3, 0.6, 0.9, and 1.2 seconds", "foot height samples are 0.04, 0.18, 0.22, 0.12, and 0.00 meters", "box top is 0.16 meters", "torso lean is 17 degrees", "support limit is 12 degrees", "46 newton-meters", "40 newton-meters", "samples 0.04, 0.20, 0.26, 0.16, 0.00", "torso lean peaks at 11 degrees", "knee torque peaks at 38 newton-meters", "whole motion is legal", "Candidate B", "0.26 to 0.21 meters", "38 to 34 newton-meters", "38^2 - 34^2 = 288", "t = 0.45 seconds", "foot height 0.155 meters", "0.155 - 0.16 = -0.005 meters", "cheaper candidate clips the box", "whole state-action history", "feedback tracker", "torso_2 = 11 degrees", "foot_height_2 = 0.26 meters", "measured state torso_2 = 14 degrees", "foot_height_2 = 0.23 meters", "adding knee torque +6 newton-meters", "requested 44 newton-meters violates the 40 limit", "adds only +2 newton-meters", "torque 40", "torso_3 = 10 degrees instead of 9", "recovers more slowly but stays legal", "x_0...x_N and u_0...u_{N-1}", "J = sum_k [10*foot_error_k^2 + 0.01*torque_k^2]", "x_{k+1}=f(x_k,u_k)", "defect_k = x_{k+1} - f(x_k,u_k)", "defect_k = 0", "torso_lean_2 = 17 degrees", "torso_lean &lt;= 12 degrees", "torque_3 = 46", "torque &lt;= 40", "torso_lean_2 = 11 degrees", "torque_3 = 38", "0.26 meters is higher than needed", "Delta J_effort = 0.01*(34^2 - 38^2) = -2.88", "clearance_mid = foot_height_mid - box_height &gt;= 0", "clearance_mid = 0.155 - 0.16 = -0.005", "constraint residual is negative", "foot_height_mid = 0.175", "clearance_mid = 0.015", "36 newton-meters", "Delta J_effort = 0.01*(36^2 - 38^2) = -1.48", "less savings, but legal", "nominal trajectory x_bar,k,u_bar,k should itself be feasible", "realized trajectory x_real,k may deviate", "e_k = x_real,k - x_bar,k", "e_torso,2 = 14 - 11 = 3 degrees", "e_foot,2 = 0.23 - 0.26 = -0.03 meters", "u_track = u_bar + delta u", "delta u = +6 gives 38 + 6 = 44", "torque_residual = 44 - 40 = 4 &gt; 0", "delta u = +2", "torque_residual = 0", "remaining torso error is 10 - 9 = 1 degree", "enough actuator room for correction", "trade a slightly higher foot path for lower torque or better balance", "grid skips the instant", "contact model lies about foot slip", "nominal torques sit too close to the actuator limit"]:
                if marker not in text:
                    errors.append(f"trajectory optimization concept page missing path-history marker: {marker}")
            if len(words) < 1360:
                errors.append(f"trajectory optimization concept page below core richness floor: {len(words)} < 1360")
        if concept.get("id") == "direct-transcription":
            for marker in ["0.0 rad to 1.2 rad", "5 newton-meter torque limit", "t = 0.0, 0.2, 0.4, and 0.6 seconds", "q_0=0.0, q_1=0.4, q_2=0.9, q_3=1.2", "tau_1=2 newton-meters", "q_2_pred = 0.6 rad", "q_2 - q_2_pred = 0.9 - 0.6 = 0.3 rad", "tau_1=8", "8 &gt; 5", "legal repair", "q_2=0.6 while keeping tau_1=2", "q_2 - q_2_pred = 0.6 - 0.6 = 0", "tau_1=5 predicts q_2_pred = 0.75", "Moving q_2 from 0.9 to 0.75", "zero defect and still obeys the torque bound", "Keeping q_2=0.9 would need tau_1=8", "fixes dynamics on paper but breaks the actuator limit", "fixture requires q &lt;= 0.80 at t = 0.4", "false q_2=0.9 violates the path bound", "q_2=0.75", "both the defect and the path bound pass", "endpoint q_3=1.2 did not excuse a false middle point", "checks the route, not only the finish", "middle states and controls together", "finite list of numbers", "neighboring pair could really follow from the model", "x_k=[q_k,v_k]", "u_k=tau_k", "h = 0.2 seconds", "zero-order hold", "tau(t)=tau_k for t_k &lt;= t &lt; t_{k+1}", "x_{k+1} = x_k + h*f(x_k,u_k)", "defect_k = x_{k+1} - step(x_k,u_k)", "step(x_k,u_k)=x_k + h*f(x_k,u_k)", "defect_1 = q_2 - q_2_pred = 0.3 rad", "illegal torque repair has tau_1=8", "-5 &lt;= tau_k &lt;= 5", "state repair has q_2=0.6", "defect_1 = 0.6 - 0.6 = 0", "tau_1 remains inside the torque bound", "mixed repair", "tau_1=5 gives q_2_pred=0.75", "choosing q_2=0.75 gives defect_1 = 0.75 - 0.75 = 0", "active torque boundary", "q_2=0.9 with the same legal tau_1=5", "defect_1 = 0.9 - 0.75 = 0.15", "grid state still lies", "If only q_0=0 and q_3=1.2 were checked", "false middle value q_2=0.9 could survive", "q_2 &lt;= 0.80", "path_residual = q_2 - 0.80 = 0.10", "path_residual = -0.05", "0.05 rad of margin", "written proof that the middle step came from the model", "defect_k = 0", "q_0=0 and q_3=1.2", "states as variables", "stop those exposed states from lying", "between t = 0.2 and t = 0.4"]:
                if marker not in text:
                    errors.append(f"direct transcription concept page missing defect marker: {marker}")
            if len(words) < 1260:
                errors.append(f"direct transcription concept page below core richness floor: {len(words)} < 1260")
        if concept.get("id") == "shooting-methods":
            for marker in ["x = 0 meters", "u_0 = 4 m/s^2", "u_1 = -1 m/s^2", "x_2 = 7 meters", "3 meters short and still moving", "u_0 = 6 m/s^2", "u_1 = -2 m/s^2", "v_1 = 6", "x_1 = 6", "v_2 = 4", "x_2 = 10", "fails the stop condition", "corrected shot is u_0 = 10 m/s^2 and u_1 = -10 m/s^2", "v_1 = 10", "x_1 = 10", "v_2 = 0", "both endpoint errors are zero", "not automatically best", "|u_k| &lt;= 8", "both position and speed", "camera cable between x = 5.0 and x = 5.5 meters", "endpoint-perfect shot crosses x_1 = 10", "v_mid = 5 m/s", "x_mid = 2.5 meters", "crossing happens between t = 0.5 and t = 1.0", "another sample or a continuous collision check", "u_0 = 8 and u_1 = -6", "v_1 = 8", "x_1 = 8", "v_2 = 2", "still crosses the cable interval", "only u_0 and u_1 are decision variables", "v_{k+1}=v_k + dt*u_k", "x_{k+1}=x_k + dt*v_{k+1}", "residual r = [x_2 - 10, v_2 - 0]", "r = [7 - 10, 3 - 0] = [-3, 3]", "r = [10 - 10, 4 - 0] = [0, 4]", "u=[10,-10]", "r=[10 - 10, 0 - 0]=[0,0]", "J_u = u_0^2 + u_1^2", "10^2 + (-10)^2 = 200", "6^2 + (-2)^2 = 40", "misses the stop condition", "successful endpoint shot is illegal", "r is zero", "State constraints are harder in shooting", "outputs of the rollout", "g_cable(x)=min(x-5.0, 5.5-x)", "at x=5.25 it is positive violation", "endpoint residual r=[0,0] does not prove the path avoided the cable", "v_k &lt;= 6", "v_1 - 6 = 4 &gt; 0", "hits the endpoint and violates the path rule", "every path residual", "respecting bounds", "gap_1 = x_join - step(x_0,u_0)", "u_0=4 then step(x_0,u_0) gives x_1=4 and v_1=4", "x_join=(5,4)", "join gap is [5 - 4, 4 - 4] = [1,0]", "two pieces do not connect", "x_join=(4,4)", "join gap is [0,0]", "state the first piece actually reaches"]:
                if marker not in text:
                    errors.append(f"shooting methods concept page missing forward-shot marker: {marker}")
            if len(words) < 1340:
                errors.append(f"shooting methods concept page below core richness floor: {len(words)} < 1340")
        if concept.get("id") == "collocation":
            for marker in ["x = 0.02 meters", "x = 0.18 meters", "t = 0.2 seconds", "x = 0.10 meters", "x = 0.08 to 0.12 meters", "path_derivative_mid = 0.9 m/s", "f(x_mid,u_mid)=0.4 m/s", "curve is trying to pass through", "x_mid = 0.14 meters", "outside the fixture", "f(x_mid,u_mid)=0.6 m/s", "curve slope is 0.6 m/s", "passes both checks", "one honest midpoint is not a free pass", "t = 0.3 seconds", "x_3 = 0.16 meters", "clearance_3 = 0.16 - 0.12 = 0.04 meters", "defect_3 = 0.5 - 0.5 = 0", "x_3 = 0.11 meters", "fixture collision has merely moved later", "Between t = 0.2 and t = 0.4", "dt = 0.2 seconds", "x_2 = 0.14 and x_4 = 0.18", "x_4 - x_2 = 0.04 meters", "0.2*(0.6 + 0.2)/2 = 0.08 meters", "interval defect is 0.04 - 0.08 = -0.04 meters", "Changing x_4 to 0.22", "wall limit x &lt;= 0.20", "clearance, dynamics, actuator bounds, and endpoint goals", "selected interior points and intervals to be physically honest", "defect_mid = path_derivative_mid - f(x_mid,u_mid)", "defect_mid = 0.9 - 0.4 = 0.5 m/s", "driving defect_mid to 0", "clearance_mid &gt;= 0", "x_mid = 0.10 meters", "clearance_mid is negative", "clearance_mid = 0.14 - 0.12 = 0.02 meters", "defect_mid = 0.6 - 0.6 = 0", "clearance_3 = x_3 - 0.12", "defect_3 = path_derivative_3 - f(x_3,u_3)", "clearance_3 = 0.04", "clearance_3 = -0.01", "candidate fails even if the midpoint looked repaired", "defect_interval = (x_{k+1} - x_k) - dt*(f_k + f_{k+1})/2", "defect_interval = (0.18 - 0.14) - 0.2*(0.6 + 0.2)/2 = -0.04 meters", "Setting x_4=0.22", "(0.22 - 0.14) - 0.08 = 0", "x_4 &lt;= 0.20 rejects it", "move the right amount over each checked interval", "t = 0.1, 0.2, and 0.3 seconds", "sampling and representation", "unmodeled flex, backlash, or contact event"]:
                if marker not in text:
                    errors.append(f"collocation concept page missing midpoint marker: {marker}")
            if len(words) < 1220:
                errors.append(f"collocation concept page below core richness floor: {len(words)} < 1220")
        if concept.get("id") == "lqr":
            for marker in ["20 centimeters left", "e_next = e + u", "u = -0.190 meters", "e = 0.05", "u = -(20/21)*0.05 = -0.0476 meters", "e = -0.20", "u = +0.190 meters", "measure the deviation, multiply by a gain", "4*u^2", "u = -0.1667 meters", "e_next = 0.0333 meters", "0.25*u^2", "u = -0.1975 meters", "e_next = 0.0025 meters", "x = [lane_error, heading_error] = [0.20, 0.10]", "u = -0.8*lane_error - 0.4*heading_error", "u = -0.8*0.20 - 0.4*0.10 = -0.20 meters", "x = [0.00, 0.10]", "u = -0.04 meters", "before lane error appears", "spends actuator effort now or tolerates more remaining error", "x_{k+1}=A_k x_k + B_k u_k", "J(u)=u^2 + 20*(0.20 + u)^2", "2u + 40*(e + u)=0", "u = -(20/21)*e", "K = 20/21", "R = 4", "4u^2 + 20*(e+u)^2", "8u + 40*(e+u)=0", "u = -(5/6)*e", "K = 5/6", "R = 0.25", "0.5u + 40*(e+u)=0", "u = -(40/40.5)*e", "u_k = -K_k x_k", "K = [0.8, 0.4]", "u = -[0.8,0.4]*[0.20,0.10] = -0.20", "same gain on x = [0.00,0.10] gives u = -0.04", "|u| &lt;= 0.10 meters", "plain LQR asks for u = -0.190", "actuator can only deliver u = -0.10", "e_next = 0.10", "not the predicted 0.010", "|e_next| &lt;= 0.05", "0.10 &gt; 0.05", "actuator saturates"]:
                if marker not in text:
                    errors.append(f"LQR concept page missing feedback-gain marker: {marker}")
            if len(words) < 1220:
                errors.append(f"LQR concept page below core richness floor: {len(words)} < 1220")
        if concept.get("id") == "local-quadratic-approximation":
            for marker in ["6 centimeters too far left", "delta u = -0.02 meters", "delta u = 0.02 meters", "jump 12 centimeters right", "2.8 centimeter suggested step", "slightly outside the tested band", "clip the first move to delta u = 0.02 meters", "real score is measured as 3.15", "predicted 3.1", "extra nudges -0.01, 0, and +0.01 meters", "3.40, 3.15, and 3.05", "another 1.2 centimeter move", "x_bar = 0.06 meters", "u_bar = 0.00", "delta x_next = 0.7*delta x + 1.5*delta u", "delta x = -0.02", "delta x_next = 0.7*(-0.02) + 1.5*0.02 = 0.016 meters", "real rollout measures 0.024 meters", "centered at the measured point", "fit nearby, step guardedly, measure again", "delta x = x - x_bar", "delta u = u - u_bar", "q(delta u) = c + g*delta u + 0.5*H*delta u^2", "delta u* = -g/H = 0.028 meters", "q(0.028)=4.0 - 70*0.028 + 0.5*2500*0.028^2 = 3.02", "-0.02 &lt;= delta u &lt;= 0.02", "trust region with radius 0.02", "delta u_clipped = 0.02", "q(0.02)=4.0 - 1.4 + 0.5 = 3.1", "remeasure and refit", "c2 = 3.15", "g2 = -10", "H2 = 833", "g2 + H2*delta u = 0", "delta u2* = 10/833 = 0.012 meters", "center of the approximation moved", "linearize the dynamics", "quadratize the cost or Q function", "delta x_next = A*delta x + B*delta u", "A = 0.7 and B = 1.5", "predicted next deviation is 0.7*(-0.02) + 1.5*0.02 = 0.016", "prediction error is 0.024 - 0.016 = 0.008 meters", "relinearize around the new measured trajectory", "u_bar + delta u", "new rollout", "trust region"]:
                if marker not in text:
                    errors.append(f"local quadratic approximation concept page missing fitted-bowl marker: {marker}")
            if len(words) < 1260:
                errors.append(f"local quadratic approximation concept page below core richness floor: {len(words)} < 1260")
        if concept.get("id") == "reachability":
            for marker in ["5 meters apart", "0.6 meters per second", "0.4 meters per second", "current lateral gap is 0.5 meters", "0.5 + 0.4 - 0.6 = 0.3", "current gap is 0.4 meters", "best escape leaves 0.2 meters", "gap to 1.0 meters", "step backward one more second", "0.7 + 0.4 - 0.6 = 0.5", "0.5 is already in the one-step danger set", "0.7 is unsafe over a two-second horizon", "0.8 meter gap", "0.8 remains outside this two-step danger map", "T_good = [3.0, 3.4]", "u between 0 and 0.8 meters", "headwind disturbance w can subtract between 0 and 0.2 meters", "p = 1.8", "p_2 = 1.8 + (0.8 - 0.2) + (0.8 - 0.2) = 3.0", "best-case p_2 = 1.8 + 0.8 + 0.8 = 3.4", "every disturbance lands inside the bay", "p = 1.6", "worst-case p_2 = 2.8", "bay is not guaranteed reachable", "p = 1.8 is inside the two-step reach set", "T_bad = {gap &lt;= 0.3 meters}", "exists a disturbance w", "for every legal control u", "The order matters", "next_gap &lt;= 0.5 + 0.4 - 0.6 = 0.3", "backward avoidance set A_1", "next_gap &lt;= 0.4 + 0.4 - 0.6 = 0.2", "strictly inside T_bad", "A_2 contains states whose worst-case next state lands in A_1", "A_1 begins at gap &lt;= 0.5", "gap = 0.7 enters A_2", "gap = 0.8 does not enter A_2", "backward part of backward reachability", "repeatedly ask which earlier states can be forced into the set", "for all disturbances, there must exist a control", "R_2 contains p = 1.8", "disturbed interval [3.0,3.4] sit inside T_good", "does not contain p = 1.6", "worst endpoint 2.8 is below the target", "single point p = 3.2", "different disturbances produce different endpoints"]:
                if marker not in text:
                    errors.append(f"reachability concept page missing set-propagation marker: {marker}")
            if len(words) < 1340:
                errors.append(f"reachability concept page below core richness floor: {len(words)} < 1340")
        if concept.get("id") == "model-predictive-control":
            for marker in ["3.0 meters from a loading mark", "10:00:00", "-0.8 m/s^2", "v_next = v + dt*u", "p_next = p + dt*v_next", "velocity 0.60 m/s and position 3.30 meters", "3.53 meters and 3.70 meters", "old -0.6 and -0.2", "position 3.40 meters and velocity 0.50 m/s", "not the predicted 3.30 meters and 0.60 m/s", "old next brake -0.6", "v_next = 0.50 + 0.5*(-0.6) = 0.20 m/s", "p_next = 3.40 + 0.5*0.20 = 3.50 meters", "leaving the cart too far short", "[-0.4, -0.3, -0.1]", "v_next = 0.50 + 0.5*(-0.4) = 0.30 m/s", "p_next = 3.40 + 0.5*0.30 = 3.55 meters", "3.625 meters and 3.675 meters", "closer to the mark while still below the stop line", "tempting lazy plan", "[-0.1, -0.1, -0.1]", "p_1 = 3.625 with v_1 = 0.45", "p_2 = 3.825 with v_2 = 0.40", "p_3 = 4.000 with v_3 = 0.35", "final speed must be at most 0.10 m/s", "rejected before its first command", "10:00:01.3", "p_late = 3.40 + 0.8*0.50 = 3.80 meters", "arrives when the cart is near (3.80, 0.50)", "u_0...u_{N-1}", "x_0 = x_measured(k)", "pi_MPC(x_measured(k)) = u_0^*", "x_0 = x_measured(k+1)", "old tail [-0.6, -0.2]", "predicted state (3.30, 0.60)", "measured state (3.40, 0.50)", "chooses new tail [-0.4, -0.3, -0.1]", "applied control is therefore -0.4, not the old -0.6", "using old -0.6 gives predicted state (3.50, 0.20)", "Using new -0.4 gives predicted state (3.55, 0.30)", "new three-step rollout ends at (3.675, 0.10)", "old one-step position error is 4.0 - 3.50 = 0.50 meters", "new one-step position error is 4.0 - 3.55 = 0.45 meters", "old tail is not sacred", "candidate tail [-0.1, -0.1, -0.1]", "v_1=0.45, p_1=3.625", "v_2=0.40, p_2=3.825", "v_3=0.35, p_3=4.000", "p_3 &lt;= 4.0", "terminal speed 0.35 &gt; 0.10", "terminal margin 4.0 - 4.000 = 0.000", "t_solve = 0.8 seconds", "dt_control = 0.5 seconds", "t_solve &gt; dt_control", "0.40 meters away from the state used in the solve", "solve takes 0.8 seconds", "control period is 0.5 seconds", "no feasible continuation", "Recursive feasibility and stability are extra promises"]:
                if marker not in text:
                    errors.append(f"MPC concept page missing receding-horizon marker: {marker}")
            if len(words) < 1280:
                errors.append(f"MPC concept page below core richness floor: {len(words)} < 1280")
        if concept.get("id") == "recursive-feasibility":
            for marker in ["2.0 meters left before the stop line", "speed is below 0.2 m/s", "1.4 m/s with only 1.1 meters left", "maximum braking 0.8 m/s^2", "v^2/(2a)=1.4^2/(2*0.8)=1.225 meters", "more than the 1.1 meters left", "handed 10:00.5 an impossible problem", "speed 1.0 m/s with 1.2 meters left", "1.0^2/(2*0.8)=0.625 meters", "0.575 meters of margin", "handoff certificate", "enough room to use maximum braking", "measured successor is worse than planned", "speed 1.1 m/s with 1.15 meters left", "1.1^2/(2*0.8)=0.756 meters", "leaving 0.394 meters", "below the required 0.4 meter terminal margin", "measured handoff failed by 0.006 meters", "feasible continuation", "every applied move preserves at least one future plan", "[u_0^*, u_1^*, u_2^*]", "x_3 lies in a terminal set X_F", "x_{k+1}=f(x_k,u_0^*) = x_1", "[u_1^*, u_2^*, v_backup]", "X_F is controlled invariant", "f(x_3,v_backup) in X_F", "speed &lt;= 0.2 m/s", "stopping_distance_remaining &gt;= 0.4 meters", "X_0 is the set of states", "keep x_{k+1} in X_0", "x_1 = (1.2 meters left, 1.0 m/s)", "v_backup = maximum brake", "reserve = 1.2 - 0.625 = 0.575 meters", "Since 0.575 &gt;= 0.4", "outside the safe handoff set", "even maximum braking needs 1.225 meters", "stopping_distance = 0.625 meters", "stopping_distance_remaining - stopping_distance = 1.2 - 0.625 = 0.575 meters", "still has a continuation", "stopping_distance = 1.1^2/(2*0.8)=0.756 meters", "stopping_distance_remaining - stopping_distance = 1.15 - 0.756 = 0.394 meters", "0.394 &lt; 0.4", "measured state is outside X_F", "planned x_1 was inside", "x_measured = (1.15 meters left, 1.1 m/s)", "shifted sequence [u_1^*, u_2^*, v_backup] is no longer certified", "not invariant", "not yet a promise that the cart reaches the doorway smoothly or quickly"]:
                if marker not in text:
                    errors.append(f"recursive feasibility concept page missing shifted-tail marker: {marker}")
            if len(words) < 1220:
                errors.append(f"recursive feasibility concept page below core richness floor: {len(words)} < 1220")
        if concept.get("id") == "stability-under-replanning":
            for marker in ["1.5 meters left", "E = distance_error^2 + 0.5*sideways_speed^2", "E = 1.5^2 + 0.5*0.8^2 = 2.57", "E = 0.9^2 + 0.5*0.5^2 = 0.935", "0.5 meters left with sideways speed 0.3 m/s right", "E = 0.5^2 + 0.5*0.3^2 = 0.295", "burden keeps falling", "1.0 meters right", "sideways speed 0.6 m/s left", "E = 1.0^2 + 0.5*0.6^2 = 1.18", "burden rose from 0.935 to 1.18", "one-step horizon", "tiny brake", "leaves E = 0.90", "leave E = 0.88", "loading dock requires E &lt;= 0.20 within three seconds", "not spending error fast enough", "terminal condition E_terminal &lt;= 0.20", "terminal cost 6*E_terminal", "predicted terminal E_N=0.18", "terminal set E &lt;= 0.20", "local lane-centering controller K", "E_next &lt;= 0.18 - 0.05 = 0.13", "real measured end of the horizon is E=0.24", "outside the terminal set", "old plan is only a receipt", "new measured state is the bill", "microscopic progress", "terminal cost, terminal set, or a decrease condition", "x_{k+1}=f_closed(x_k)", "V(f_closed(x)) - V(x) &lt;= -stage_cost(x,pi_MPC(x))", "delta V = 0.935 - 2.57 = -1.635", "delta V = 0.295 - 0.935 = -0.640", "delta V = 1.18 - 0.935 = +0.245", "violates a nonincrease test", "stage cost for the second state were 0.10", "delta V &lt;= -0.10", "accept -0.640 and reject +0.245", "nonincrease alone may be too weak", "E_0=0.935", "E_1=0.90", "E_2=0.88", "E_{k+1} &lt;= E_k", "miss the required E_3 &lt;= 0.20 target", "terminal constraint writes E_N &lt;= 0.20", "sum stage_cost + 6*E_N", "E_N=0.88 adds 5.28 points", "E_N=0.18 adds 1.08 points", "measured-state check is stricter", "V_now=0.295", "stage_cost=0.10", "required next bound is V_next &lt;= 0.295 - 0.10 = 0.195", "V_next=0.18 passes", "V_next=0.24 fails", "0.24 &gt; 0.195", "feasible but not certified stable", "Feasibility alone would only say the next optimization exists", "terminal set gives the final predicted state", "old proof has nothing to stand on", "cycling, drifting, delaying, or amplifying velocity"]:
                if marker not in text:
                    errors.append(f"stability under replanning concept page missing decrease marker: {marker}")
            if len(words) < 1320:
                errors.append(f"stability under replanning concept page below core richness floor: {len(words)} < 1320")
        if concept.get("id") == "imitation-learning":
            for marker in ["200 drawer pulls", "handle center x = 0.00 meters", "pull speed 0.04 m/s", "160 rows are centered pulls", "30 rows show a careful left-hook style", "gripper angle -14 degrees", "10 rows show a right-hook style", "gripper angle +16 degrees", "averaging them gives about -4 degrees", "misses the handle by 3 centimeters", "handle may rotate 12 degrees", "only 2 rows with handle angle 12 degrees", "gripper angle 1 degree", "scraping the handle for 0.4 seconds", "gripper angle -18 degrees", "50 drawer attempts", "17 off-center states", "add those 17 labeled states", "L(theta)=sum_i ||pi_theta(x_i) - u_i^expert||^2", "30*(a - (-14))^2 + 10*(a - 16)^2", "80a + 520", "a = -6.5 degrees", "pi_theta(u|x)", "left_hook or right_hook", "x_{t+1}=f(x_t, pi_theta(x_t))", "2/200 = 0.01", "17/50 = 0.34", "x_j^learner", "D_1 = D_0 union {(x_j^learner,u_j^expert)}", "17 recovery labels"]:
                if marker not in text:
                    errors.append(f"imitation learning concept page missing demonstration-loop marker: {marker}")
            if len(words) < 1160:
                errors.append(f"imitation learning concept page below core richness floor: {len(words)} < 1160")
        if concept.get("id") == "behavioral-cloning":
            for marker in ["1,000 centered-lane frames", "steering angle -12 degrees", "steering angle +12 degrees", "average label is 0 degrees", "1 degree right bias over 20 frames", "0.25 meters toward the lane edge", "expert would steer -8 degrees left", "200 such frames", "37 off-center frames", "add those 37 pairs to the dataset", "good test error on expert states can hide bad closed-loop recovery", "L(theta)=sum_i ||pi_theta(x_i)-u_i^expert||^2", "50*(a - (-12))^2 + 50*(a - 12)^2", "squared-error optimum is a = 0 degrees", "d_expert(x)", "d_pi_theta(x)", "x_{t+1}=f(x_t,pi_theta(x_t))", "37 off-center frames out of 200", "D_1 = D_0 union {(x_j^learner,u_j^expert)}", "no built-in exploration or reward signal"]:
                if marker not in text:
                    errors.append(f"behavioral cloning concept page missing supervised-action marker: {marker}")
            if len(words) < 1160:
                errors.append(f"behavioral cloning concept page below core richness floor: {len(words)} < 1160")
        if concept.get("id") == "distribution-shift-imitation":
            for marker in ["within 10 centimeters of lane center", "understeers by only 2 centimeters", "second 4", "18 centimeters right", "3 of the 10,000 expert frames", "98 percent of expert frames", "steering error below 1 degree", "steer -14 degrees left", "0.5 m/s", "steers -3 degrees left", "0.9 m/s", "24 centimeters right", "300 seconds", "42 frames", "more than 15 centimeters off center", "d_expert(x)", "d_pi(x)", "d_expert(|offset| &gt; 15 cm) = 3/10000 = 0.0003", "d_pi(|offset| &gt; 15 cm) = 42/300 = 0.14", "d_pi(18 cm right) much larger than d_expert(18 cm right)", "epsilon = 0.02", "T^2*epsilon = 50^2*0.02 = 50", "collect rollout states from d_pi", "D_1 = D_0 union {(x_j^pi_1,u_j^expert)}", "x = 18 cm right maps to u^expert = -14 degrees and 0.5 m/s", "expert can label the learner&#x27;s states"]:
                if marker not in text:
                    errors.append(f"distribution shift concept page missing learner-state marker: {marker}")
            if len(words) < 1160:
                errors.append(f"distribution shift concept page below core richness floor: {len(words)} < 1160")
        if concept.get("id") == "reinforcement-learning":
            for marker in ["12 newtons", "tilts the wrist by 15 degrees", "18 newtons", "reward -1", "reward +10", "gamma = 0.9", "G_0 = 0 + 0.9*(-1) + 0.9^2*10 = 7.2", "30 newtons", "G_0(tear) = 2 + 0.9*(-12) = -8.8", "credit assignment", "40 newtons", "force &gt; 25 newtons", "(x_t,u_t,r_t,x_{t+1})", "tau = [(x_0,light_grip,0,x_1),(x_1,tilt,-1,x_2),(x_2,lift,+10,x_3)]", "G_t = r_t + gamma*r_{t+1} + gamma^2*r_{t+2} + ...", "G_1 = -1 + 0.9*10 = 8", "E[sum_t gamma^t r_t]", "7.2, 6.1, 8.0, -8.8, and 7.5", "(7.2 + 6.1 + 8.0 - 8.8 + 7.5)/5 = 4.0", "empirical mean", "y = r_t + gamma max_{u&#x27;} Q(x_{t+1},u&#x27;)", "Q(x,light_grip)=3.0", "max_{u&#x27;} Q(x_next,u&#x27;)=8", "y = 0 + 0.9*8 = 7.2", "alpha = 0.5", "Q_new = 3.0 + 0.5*(7.2 - 3.0) = 5.1", "omitting tearing force"]:
                if marker not in text:
                    errors.append(f"reinforcement learning concept page missing rollout-return marker: {marker}")
            if len(words) < 1160:
                errors.append(f"reinforcement learning concept page below core richness floor: {len(words)} < 1160")
        if concept.get("id") == "reward":
            for marker in ["10 - 6 = 4", "35 newtons", "10 - 1 = 9", "-0.5 per newton above 8", "-20 if the cup is damaged", "delayed reward", "rewards 0, 0, +10", "get +4 now", "receive -6 next", "gentle return is 10", "yank return is -2", "gamma = 0.5", "0 + 0.5*0 + 0.5^2*10 = 2.5", "4 + 0.5*(-6) = 1", "returns 10, 10, 8, 10, and -2", "(10 + 10 + 8 + 10 - 2)/5 = 7.2", "returns -2, 4, -6, -2, and 4", "(-2 + 4 - 6 - 2 + 4)/5 = -0.4", "single lucky yank", "rollout distribution decides how often each consequence appears", "how much patience the learner can afford", "r(x,u,x_next)", "G_0 = sum_t gamma^t r_t", "10 - 1 - 0.5*(35 - 8) - 20 = -24.5", "rewards [0,0,10]", "G_0(gentle; gamma=1)=10", "G_0(gentle; gamma=0.5)=0+0.5*0+0.25*10=2.5", "rewards [4,-6]", "G_0(yank; gamma=1)=-2", "G_0(yank; gamma=0.5)=4+0.5*(-6)=1", "later rewards count less", "J(pi)=E_{tau~p_pi(tau)}[sum_t gamma^t r_t]", "expected return under the trajectory distribution", "estimate E[G] as 7.2", "estimate E[G] as -0.4", "random transition outcomes", "scalar reward says what is counted", "trajectory distribution says how often each counted event happens", "optimized the written measuring stick", "patience"]:
                if marker not in text:
                    errors.append(f"reward concept page missing scalar-loophole marker: {marker}")
            if len(words) < 1360:
                errors.append(f"reward concept page below core richness floor: {len(words)} < 1360")
        if concept.get("id") == "policy":
            for marker in ["distance_to_wall = 0.45 meters", "battery = 38 percent", "distance_to_wall &lt; 0.50 meters", "steering = -18 degrees", "pi(slow-left|x) = 0.8", "pi(hard-left|x) = 0.2", "fixed two-command script", "first slow-left, then slow-left again", "0.62 meters from the wall", "drift to 0.90 meters", "if distance_to_wall &gt; 0.60 meters", "steer = +10 degrees", "second command is different because the measured state is different", "epsilon-greedy behavior policy", "probability 0.90", "random legal action with probability 0.10", "x_near=(0.45,0.8,38)", "hard-left at 25 degrees", "x_bad=(0.92,0.75,37)", "never learned what 0.92 means", "if distance_to_wall &gt; 0.85 meters", "steer = +22 degrees", "speed_command = 0.2 m/s", "next distance back to 0.70 meters", "states created by its own earlier choices", "u = pi(x)", "pi(u|x)", "x_{t+1}=f(x_t,u_t)", "x_0=(0.45, 0.8, 38)", "u_0=(-18 degrees, 0.4 m/s)", "x_1=(0.62, 0.35, 37)", "u_1=(-18 degrees, 0.4 m/s) again", "u_1=pi(x_1)=(+10 degrees, 0.5 m/s)", "difference between a list of actions and a rule", "pi_b(u|x)=0.90*pi_safe(u|x)+0.10*pi_random(u|x)", "five legal actions", "0.10/5 = 0.02", "x_bad=f(x_near,hard-left)=(0.92,0.75,37)", "pi_recover(x_bad)=(+22 degrees,0.2 m/s)", "pi_brittle(x_bad)=(-18 degrees,0.4 m/s)", "agree at x_near and disagree at x_bad", "first-frame action is weak evidence", "omits a needed state variable"]:
                if marker not in text:
                    errors.append(f"policy concept page missing closed-loop-rule marker: {marker}")
            if len(words) < 1320:
                errors.append(f"policy concept page below core richness floor: {len(words)} < 1320")
        if concept.get("id") == "state":
            for marker in ["y = 0.20 meters", "v_y = 0.00 m/s", "psi = 0 degrees", "v_y = -1.50 m/s", "psi = -8 degrees", "u = +5 degrees", "dt = 0.2 seconds", "y_next = y + dt*v_y", "0.20 + 0.2*0.00 = 0.20 meters", "0.20 + 0.2*(-1.50) = -0.10 meters", "single camera frame", "y was 0.50 meters left 0.2 seconds ago", "v_y_est = (0.20 - 0.50)/0.2 = -1.50 m/s", "battery_temp = 32 C", "battery_temp = 46 C", "48 C heat limit", "future constraint almost active", "battery heat", "p = 1.80 meters", "v = 0.60 m/s", "stop line at p = 2.00 meters", "a_cmd = -2.0 m/s^2", "floor_grip = 1.0", "a_actual = -2.0", "v_next = 0.60 + 0.2*(-2.0) = 0.20 m/s", "p_next = 1.80 + 0.2*0.20 = 1.84 meters", "floor_grip = 0.25", "a_actual = -0.5", "v_next = 0.50 m/s and p_next = 1.90 meters", "p_next2 = 1.90 + 0.2*0.40 = 1.98 meters", "different floor mode, different safe action", "floor grip", "x_{t+1}=f(x_t,u_t)", "same action distribution over next states", "x=[y]", "x=[y,v_y,psi]", "observation o_t", "camera_frame_t", "x_t = [y_t, (y_t-y_{t-1})/dt, psi_t]", "(0.20 - 0.50)/0.2 = -1.50", "sliding Car B from steady Car A", "x=[position,velocity]", "better state includes battery_temp", "battery_temp_next = battery_temp + heat_gain(u)", "heat_gain(climb)=3 C", "32 C to 35 C", "46 C to 49 C", "violates the heat constraint", "x=[p,v] only", "dry and wet carts both look like x=[1.80,0.60]", "x=[p,v,floor_grip]", "a_actual=floor_grip*a_cmd", "a_actual=1.0*(-2.0)=-2.0", "a_actual=0.25*(-2.0)=-0.5", "estimated state, a belief over grip, or a conservative constraint", "hidden battery temperature, tire grip, load mass"]:
                if marker not in text:
                    errors.append(f"state concept page missing predictive-memory marker: {marker}")
            if len(words) < 1300:
                errors.append(f"state concept page below core richness floor: {len(words)} < 1300")
        if concept.get("id") == "static-optimization":
            for marker in ["one charging power z", "6 kilowatts", "4 kilowatts", "J(z) = (z - 6)^2", "0 &lt;= z &lt;= 4", "J(4) = (4 - 6)^2 = 4", "J(3) = 9", "J(0) = 36", "after 20 minutes at z = 4", "temperature rises from 30 C to 46 C", "above a 45 C limit", "z = 3 keeps it at 42 C", "fixed cooling fan", "precompute temperature_after_20_min(z)", "z = 3.5 end at 44 C", "J(3.5)=6.25", "z = 4 still fails heat", "z = 3 has score 9", "z = 3.5 has score 6.25", "best legal static choice becomes 3.5 kilowatts", "change power after 10 minutes", "next temperature becomes a state", "two 10-minute blocks", "fixed static plan z = 3.5 for both blocks", "temperature 44 C after block one and 45 C after block two", "sensor reads 41 C, not 44 C", "z_1 = 4.0", "temperature_next = temperature + 0.8*(z - 3)", "41 + 0.8*(4.0 - 3) = 41.8 C", "one-shot static decision could not use that new information", "minimize_z J(z)", "g_i(z) &lt;= 0", "h_j(z) = 0", "dJ/dz = 2*(z - 6) = 0", "active outlet boundary z = 4", "g_heat(z)=temperature_after_20_min(z)-45 &lt;= 0", "g_heat(4)=46-45=1 &gt; 0", "z = 3 can become the best legal point", "g_heat(3.5)=44-45=-1 &lt;= 0", "z = 3.5 is legal", "closer to the desired 6 kilowatts", "not a second decision", "baked into the fixed map", "temperature_after_20_min(z) is a fixed map", "choose z_0 now", "observe temperature_1", "then choose z_1", "one number reused twice", "temperature_{k+1}=temperature_k + 0.8*(z_k - 3)", "second decision is allowed to depend on measured temperature_1", "temperature_2 = 41 + 0.8*(4.0 - 3) = 41.8", "z_1 = pi(temperature_1)", "temperature_next = f(temperature,z)", "change power after each 10 minute interval"]:
                if marker not in text:
                    errors.append(f"static optimization concept page missing one-shot-decision marker: {marker}")
            if len(words) < 1280:
                errors.append(f"static optimization concept page below core richness floor: {len(words)} < 1280")
        if concept.get("id") == "gradient-first-order-condition":
            for marker in ["J(z) = (z - 3)^2 + 0.2*z^2", "dJ/dz = 2*(0 - 3) + 0.4*0 = -6", "delta z = +0.1", "-6*0.1 = -0.6", "z = 2.5", "J(2.4) = (2.4 - 3)^2 + 0.2*2.4^2 = 1.512", "J(2.5) = 1.5", "J(2.6) = 1.512", "steering stop z &lt;= 2.0", "dJ/dz = 2*(2 - 3) + 0.4*2 = -1.2", "delta z = +0.1 is illegal", "boundary with nonzero slope", "K(z)=-(z - 2)^2 + 5", "K(1.9)=4.99", "K(2)=5.0", "local maximum", "zero first derivative found a candidate", "grad J = [-2, 4]", "delta = [0.1, -0.1]", "-2*0.1 + 4*(-0.1) = -0.6", "predicted downhill", "delta = [0.1, 0.1]", "-2*0.1 + 4*0.1 = +0.2", "predicted uphill", "S(z,s)=z^2 - s^2", "grad S(0,0)=[0,0]", "delta=[0,0.1]", "about -0.01", "delta=[0.1,0]", "about +0.01", "second-order shape decides", "rock begins at steering above 2.3 degrees", "J(z + delta z)", "grad J(z)^T delta z &lt; 0", "grad J(z) = 0", "delta z &lt;= 0", "grad J(2.0) = -1.2", "(-1.2)*(-0.1)=+0.12", "downhill move delta z = +0.1 would give -0.12", "constrained local minimum can have a nonzero gradient", "d^2J/dz^2 = 2 + 0.4 = 2.4", "stationary point is a local bowl", "d^2K/dz^2 = -2", "hilltop for minimization", "gradient is a price list for tiny changes", "grad J^T delta = -0.6", "grad J^T delta = +0.2", "sign of the dot product", "Hessian has one positive and one negative direction", "S(0,0.1)=-0.01", "S(0.1,0)=+0.01", "localness and model honesty", "not proof of global optimality"]:
                if marker not in text:
                    errors.append(f"gradient first-order condition page missing local-slope marker: {marker}")
            if len(words) < 1260:
                errors.append(f"gradient first-order condition page below core richness floor: {len(words)} < 1260")
        if concept.get("id") == "calculus-of-variations":
            for marker in ["1 meter rail in 2 seconds", "u(t) from t = 0 to t = 2", "0.5 m/s", "x(2) = 1 meter", "0.8 m/s", "0.2 m/s", "J[u] = integral_0^2 u(t)^2 dt", "2*(0.5^2) = 0.5", "1*(0.8^2) + 1*(0.2^2) = 0.68", "reduce the first-second speed by 0.1 m/s", "-0.1*1 + 0.1*1 = 0", "1*(0.7^2) + 1*(0.3^2) = 0.58", "speed limit u(t) &lt;= 0.75 m/s", "original surge at 0.8 m/s was never admissible", "0.75 m/s for the first second and 0.25 m/s for the second", "1*(0.75^2) + 1*(0.25^2) = 0.625", "0.65 and 0.35", "1*(0.65^2) + 1*(0.35^2) = 0.545", "every small shape eta(t)", "narrow bump", "t = 0.4 to t = 0.5", "t = 1.4 to t = 1.5", "-0.1*0.1 + 0.1*0.1 = 0", "2*0.8*(-0.1)*0.1 + 2*0.2*(+0.1)*0.1 = -0.012", "0.1*(0.8^2) + 0.1*(0.2^2) = 0.068", "0.1*(0.7^2) + 0.1*(0.3^2) = 0.058", "local bump is not a local best curve", "epsilon*eta(t)", "d/depsilon J[u + epsilon*eta]", "integral_0^2 2*u(t)*eta(t) dt", "x_dot = u", "integral_0^2 eta(t) dt = 0", "integral_0^2 2*0.5*eta(t) dt", "eta(t)=-1 on the first second", "eta(t)=+1 on the second", "first variation is 2*0.8*(-1)*1 + 2*0.2*(+1)*1 = -1.2", "0.68 down to 0.58", "eta=-1 on [0.4,0.5]", "eta=+1 on [1.4,1.5]", "integral eta dt = -1*0.1 + 1*0.1 = 0", "first variation is 2*0.8*(-1)*0.1 + 2*0.2*(+1)*0.1 = -0.12", "predicted first-order cost drop is -0.012", "exact two-window cost drop is 0.068 - 0.058 = 0.010", "fundamental lemma", "h(t)*eta(t)", "h(t) must be zero across the open interval", "Euler equation", "With the speed bound u(t) &lt;= 0.75", "0.8/0.2 curve is outside the legal set", "0.75/0.25 curve has cost 0.625", "epsilon = 0.1 gives 0.65/0.35", "endpoint change (-0.1)*1 + (+0.1)*1 = 0", "cost 0.545", "perturbation must preserve the endpoint and stay inside path limits", "smooth admissible perturbations"]:
                if marker not in text:
                    errors.append(f"calculus of variations concept page missing curve-perturbation marker: {marker}")
            if len(words) < 1300:
                errors.append(f"calculus of variations concept page below core richness floor: {len(words)} < 1300")
        if concept.get("id") == "costate-adjoint-variable":
            for marker in ["height 10 meters after two seconds", "x_next = x + u", "100*(x_2 - 10)^2", "100*(0.1^2) = 1", "x_1 = 9.4 meters", "200*(x_1 + u_1 - 10)", "u_1 is 0.5", "final height is 9.9", "derivative is -20", "running penalty 5*(x_1 - 9.5)^2", "10*(9.4 - 9.5) = -1", "total price at time 1 becomes -21", "two state coordinates", "height h and velocity v", "h_1=9.4", "v_1=0.2", "a_1=0.3", "h_2=h_1+v_1+0.5*a_1=9.75", "v_2=v_1+a_1=0.5", "50*(h_2-10)^2 + 5*v_2^2", "height price is -25", "velocity price is 5", "lambda_h1=-25", "lambda_v1=-20", "0.5 meters per 1 m/s^2", "1.0 m/s per 1 m/s^2", "-25*0.5 + 5*1.0 = -7.5", "downstream cost wants more acceleration", "effort cost is 2*a_1^2", "4*0.3 = 1.2", "1.2 + (-7.5) = -6.3", "small increase in acceleration lowers the written cost", "missing derivative of +10", "1.2 - 7.5 + 10 = +3.7", "more acceleration would no longer look good", "velocity affects both next height and next velocity", "time-1 running cost and the final cost", "p(t)", "x_dot = f(x,u)", "lambda_2 = d terminal_cost/dx_2", "lambda_2 = -20", "previous future price is lambda_2*1 = -20", "lambda_1 = -20", "l_1(x_1)=5*(x_1 - 9.5)^2", "dl_1/dx_1 = 10*(9.4 - 9.5) = -1", "lambda_1 = -20 + (-1) = -21", "x_2 = 0.5*x_1 + u_1", "lambda_2*0.5 = -10", "x=[h,v]", "terminal_cost=50*(h_2-10)^2 + 5*v_2^2", "h_2=9.75 and v_2=0.5", "lambda_2=[100*(9.75-10), 10*0.5]=[-25, 5]", "Jacobian", "[[1,1],[0,1]]", "lambda_1 = [[1,0],[1,1]]*[-25,5] = [-25,-20]", "partial x_2/partial a_1 = [0.5,1]", "lambda_2^T partial x_2/partial a_1 = [-25,5]*[0.5,1] = -7.5", "d(2*a_1^2)/da_1 = 4*a_1 = 1.2", "local derivative with respect to acceleration is -7.5 + 1.2 = -6.3", "Hamiltonian control derivative", "omitted motor heat would contribute +10", "derivative becomes -7.5 + 1.2 + 10 = +3.7", "one meter per second of extra velocity", "changes both final height and final velocity", "omitted heat, collision, or actuator wear"]:
                if marker not in text:
                    errors.append(f"costate concept page missing backward-price marker: {marker}")
            if len(words) < 1320:
                errors.append(f"costate concept page below core richness floor: {len(words)} < 1320")
        if concept.get("id") == "hamiltonian-optimal-control":
            for marker in ["running cost is 0.5*u^2", "x_dot = u", "p = -20", "H = 0.5*u^2 + p*u", "u = 0: H = 0", "u = 10: H = 50 - 200 = -150", "u = 20: H = 200 - 400 = -200", "u = 30: H = 450 - 600 = -150", "motor cap u &lt;= 12", "H(12)=0.5*12^2 - 20*12 = 72 - 240 = -168", "illegal H(20)=-200", "legal H(10)=-150", "constrained local choice sits at u = 12", "p = -4", "H(u)=0.5*u^2 - 4*u", "unconstrained balance is u = 4", "H(4)=8-16=-8", "H(12)=72-48=24", "cap is legal but no longer attractive", "p = +6", "every positive thrust raises the local account", "best local choice is u = 0", "same motor and the same running cost", "Only the backward price changed", "H(x,u,p)=L(x,u)+p*f(x,u)", "H(u)=0.5*u^2 - 20*u", "dH/du = u - 20 = 0", "dH/du at u=12 = 12 - 20 = -8", "increasing u is forbidden", "active boundary u^* = 12", "dH/du = u - 4", "stationarity gives u=4", "0 &lt;= 4 &lt;= 12", "cap is inactive", "dH/du = u + 6", "minimum over 0 &lt;= u &lt;= 12 is the lower boundary u=0", "local in time", "costate came from the rest of the trajectory", "target, obstacle, or terminal penalty changes", "augment the cost with the constraint", "omits motor heat", "derivative-zero answer can be illegal", "not proved the whole path is best"]:
                if marker not in text:
                    errors.append(f"Hamiltonian concept page missing local-accounting marker: {marker}")
            if len(words) < 1160:
                errors.append(f"Hamiltonian concept page below core richness floor: {len(words)} < 1160")
        if concept.get("id") == "indirect-methods":
            for marker in ["x(0)=0 meters", "x(2)=1 meter", "x_dot = u", "running cost is 0.5*u^2", "H = 0.5*u^2 + p*u", "dH/du = u + p = 0", "u = -p", "p_dot = 0", "initial costate", "p(0) = -0.3", "x(2)=0.6", "0.4 meters short", "p(0) = -0.7", "x(2)=1.4", "correct shot between -0.3 and -0.7", "p(0) = -0.5", "x(2)=1.0 exactly", "x(t)=0.5*t", "final position is free", "phi(x(2))=10*(x(2)-1)^2", "p(2)=dphi/dx=20*(x(2)-1)", "p0 = 20*(-2*p0 - 1)", "41*p0 = -20", "p0=-20/41=-0.488", "x(2)=40/41=0.976", "trades effort against final error", "ceiling rail at x(t) &lt;= 0.8 until t = 1.5 seconds", "x(1.8)=0.9", "violates the ceiling", "use u=0.8 for the first second", "reach x=0.8", "u=0 from t=1.0 to t=1.5", "u=0.4 for the last half second", "effort is 0.5*(0.8^2)*1.0 + 0.5*(0^2)*0.5 + 0.5*(0.4^2)*0.5 = 0.36", "smooth shot&#x27;s 0.25", "new arc or multiplier", "terminal miss", "partial H/partial p", "partial H/partial u = 0", "r(p0)=x(2;p0)-1", "r=-0.4", "r=+0.4", "sign change", "x(2;p0)=-2*p0", "r(p0)=-2*p0-1", "shooting method", "b(p0)=p(2)-20*(x(2)-1)", "b(p0)=p0-20*(-2*p0-1)=41*p0+20", "marginal effort price and marginal miss price balance", "x_unconstrained(t)=0.5*t", "x_unconstrained(1.8)=0.9", "g(t)=x(t)-0.8", "g(1.8)=0.1 &gt; 0", "active path constraint", "x(1.0)=0.8", "1.0 &lt;= t &lt;= 1.5", "x(2)=1.0", "effort is 0.32 + 0 + 0.04 = 0.36", "unconstrained effort is 0.5*(0.5^2)*2 = 0.25", "path limit such as x(t) &lt;= 0.8", "active arc and its boundary conditions", "wrong sign"]:
                if marker not in text:
                    errors.append(f"indirect methods concept page missing boundary-value marker: {marker}")
            if len(words) < 1320:
                errors.append(f"indirect methods concept page below core richness floor: {len(words)} < 1320")
        if concept.get("id") == "value-based-rl":
            for marker in ["battery 22 percent", "Q(x,turn_left) = 3", "Q(x,turn_right) = 7", "gamma = 0.9", "y = -1 + 0.9*10 = 8", "alpha = 0.5", "7 + 0.5*(8 - 7) = 7.5", "Q(x_next,charge_now)=10", "Q(x_next,inspect_box)=4", "epsilon-greedy behavior policy", "slow charger line", "y_SARSA = -1 + 0.9*4 = 2.6", "7 + 0.5*(2.6 - 7) = 4.8", "y_Q = -1 + 0.9*10 = 8", "Same first transition, different target", "V_pi(x)", "Q_pi(x,u)", "policy evaluation", "policy improvement", "Q(x,u) &lt;- Q(x,u) + alpha*(y - Q(x,u))", "max_a Q(x_next,a)=10", "behavior policy is the rule that collected the sample", "target policy is the rule used inside the update", "SARSA uses y_SARSA = r + gamma Q(x_next,u_next)", "Q-learning uses y_Q = r + gamma max_a Q(x_next,a)", "SARSA learns the value of behaving with exploration still present", "Q-learning learns toward the greedy policy", "slick floors"]:
                if marker not in text:
                    errors.append(f"value-based RL concept page missing value-update marker: {marker}")
            if len(words) < 1140:
                errors.append(f"value-based RL concept page below core richness floor: {len(words)} < 1140")
        if concept.get("id") == "policy-optimization":
            for marker in ["body leaning forward 6 degrees", "right knee bent 20 degrees", "pi_theta(long_step|x) = 0.30", "pi_theta(short_step|x) = 0.70", "return G = 12", "return G = 2", "baseline b(x)=7", "A_long = 12 - 7 = +5", "A_short = 2 - 7 = -5", "pi_theta_new(long_step|x) = 0.38", "probability shift is earned by advantage", "J(theta)=E_{tau~pi_theta}[G(tau)]", "grad_theta log pi_theta(u_t|x_t) * A_t", "theta_new = theta + eta*g", "eta = 0.04", "Delta score_long = 0.04*5 = 0.20", "Delta score_short = 0.04*(-5) = -0.20", "surrogate objective", "tile floor", "return G = -8", "A_tile = -8 - 7 = -15", "eta = 0.20", "Delta score = 0.20*(-15) = -3.0", "rubber mat and tile floor are different states", "erase a useful rubber-mat action", "Noisy returns"]:
                if marker not in text:
                    errors.append(f"policy optimization concept page missing direct-policy-update marker: {marker}")
            if len(words) < 1040:
                errors.append(f"policy optimization concept page below core richness floor: {len(words)} < 1040")
        if concept.get("id") == "exploration":
            for marker in ["18 newtons", "0.04 m/s", "7 out of 10 times", "12 degrees with 22 newtons", "60 newtons", "epsilon = 0.10", "10 of 100 attempts", "force &lt;= 25 newtons", "handle_angle &lt;= 15 degrees", "known pull has 7/10 = 0.70", "10 shallow-handle trials", "9 successes and 1 slip", "4 deep-handle trials", "1 success and 3 scrapes", "0.90 - 0.70 = 0.20", "20 more successful pulls per 100 shallow handles", "pi_explore(u|x) = 1 - epsilon", "A_safe(x) = {force &lt;= 25, handle_angle &lt;= 15}", "force = 60 is outside A_safe(x)", "Q(x,u) + beta*uncertainty(x,u)", "Q(x,straight)=0.70", "uncertainty(straight)=0.05", "Q(x,angled)=0.60", "uncertainty(angled)=0.40", "beta = 0.5", "0.70 + 0.5*0.05 = 0.725", "0.60 + 0.5*0.40 = 0.80", "score makes angled worth a safe trial", "uncertainty drops to 0.10", "not a blind gamble", "do not justify using it on deep handles", "coverage under constraints"]:
                if marker not in text:
                    errors.append(f"exploration concept page missing constrained-coverage marker: {marker}")
            if len(words) < 1160:
                errors.append(f"exploration concept page below core richness floor: {len(words)} < 1160")
        if concept.get("id") == "model-based-rl":
            for marker in ["0.20 meters before a shelf", "80 real trials", "position 1.40 m", "brake 30 percent", "x_next = (position 1.46 m, velocity 0.48 m/s)", "f_hat(x,u)", "final position 0.08 meters", "final position 0.24 meters", "Sequence C brakes 60 percent", "only 3 transitions with brake above 50 percent on dusty floor", "measured next state is position 1.58 m, velocity 0.55 m/s", "predicted position 1.54 m, velocity 0.42 m/s", "planner has found a weak spot in the model", "executes only the first brake command", "x_{t+1}=f_hat(x_t,u_t)", "p_hat(x_{t+1}|x_t,u_t)", "[u_0,u_1,u_2]", "position error is 1.58 - 1.54 = 0.04 m", "velocity error is 0.55 - 0.42 = 0.13 m/s", "20 possible models", "0.28, 0.26, 0.09, -0.04, and 0.31 meters", "(0.28 + 0.26 + 0.09 - 0.04 + 0.31)/5 = 0.18 meters", "below the required 0.20 meters", "0.24, 0.23, 0.25, 0.22, and 0.24 meters", "mean 0.236 meters", "uncertainty changes planning", "underestimates braking distance by 0.10 meters", "old data distribution and the state distribution created by the planner"]:
                if marker not in text:
                    errors.append(f"model-based RL concept page missing learned-model-planning marker: {marker}")
            if len(words) < 1160:
                errors.append(f"model-based RL concept page below core richness floor: {len(words)} < 1160")
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
