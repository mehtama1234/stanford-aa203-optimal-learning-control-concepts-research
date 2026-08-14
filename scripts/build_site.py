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


CONCEPT_RUNS: dict[str, dict[str, str]] = {
    "optimal-control-problem": {
        "run": "Suppose a landing rocket is 80 meters above the pad, falling at 18 m/s, with 12 seconds of fuel left. A hard burn now slows it, but may leave too little fuel for the last meters. A weak burn saves fuel, but may make the later braking problem impossible. The object is not one throttle command. It is the whole chain of states and commands until touchdown.",
        "math": "State x might contain height, velocity, and fuel. Control u is thrust. Dynamics move x forward one time step. Cost adds fuel use, landing error, and touchdown speed. Constraints forbid negative fuel, too much thrust, and unsafe impact speed.",
    },
    "state": {
        "run": "Two cars can sit at the same point in a lane and need opposite controls. One is moving straight at 20 mph; the other is sliding sideways at 20 mph. Position alone hides the difference. Speed, heading, tire slip, and nearby cars are part of the state because they change what the next steering or braking command will do.",
        "math": "A state is the smallest present-tense record that lets the model predict the next state from the next action. If two histories give the same state, the controller is claiming their future options are the same.",
    },
    "action-control-input": {
        "run": "A drone pilot may want the drone to be two meters higher. The controller cannot choose height directly. It can change rotor thrust; thrust changes acceleration, acceleration changes velocity, and velocity changes height. Calling height the action would make the plan ask for magic.",
        "math": "The action u is the command passed into the dynamics. The next state is not chosen directly; it is produced by x_next = f(x, u).",
    },
    "dynamics": {
        "run": "If a car is moving fast on ice, the same steering angle produces a different next state than it would on dry asphalt. Dynamics are the rule that carries a command through the body and the world. Without that rule, planning is only drawing wishes on a map.",
        "math": "Dynamics can be written as x_next = f(x, u) in discrete time or dx/dt = f(x, u) in continuous time. The function is the claim about how action becomes motion.",
    },
    "objective-cost-function": {
        "run": "A car that reaches a parking spot fastest may scrape the wall. A car that never moves is safe but useless. The cost is the scoreboard that says which future is better: time, distance from the goal, steering effort, comfort, and collision risk all get counted in one place.",
        "math": "A typical objective adds stage costs along the path and a terminal cost at the end. The weights are not decoration; they state the tradeoff the controller will actually obey.",
    },
    "value-function": {
        "run": "A rover at the edge of a rocky slope should not ask only whether the next meter is easy. It should ask what the world looks like after that meter. The value of a state is the price tag on standing there with all future choices still ahead.",
        "math": "V(x) stores the best future cost from state x. Once V is known, a current action can be judged by immediate cost plus the value of the next state it creates.",
    },
    "bellman-recursion": {
        "run": "A warehouse robot choosing between two aisles does not need to list every possible path to the loading dock. For each aisle, it can count the cost of entering that aisle now, then look up the best remaining cost from the state at the end of that move. That is the Bellman split: pay now, then inherit the future value of the state you created.",
        "math": "V(x) = min over u of cost(x,u) + V(f(x,u)) in the deterministic case. With uncertainty, the next value is averaged over possible next states.",
    },
    "direct-transcription": {
        "run": "A robot arm path is a smooth curve, but a solver needs a finite list of numbers. Direct transcription places dots along the path: joint angles, velocities, and commands at selected times. Then it adds constraints saying neighboring dots must be connected by the dynamics. The solver chooses the dots; the engineer checks whether the space between dots hid trouble.",
        "math": "The continuous path becomes decision variables x_0...x_N and u_0...u_N. Defect constraints enforce x_{k+1} minus the dynamics step from x_k and u_k.",
    },
    "lqr": {
        "run": "A drone hovering in still air does not need a full nonlinear planner for a two-centimeter drift. Near hover, the motion is almost linear and the penalty for being off-center is almost a bowl. LQR turns that local picture into a feedback rule: if the state error points this way, push back that way.",
        "math": "Linear dynamics plus quadratic cost make the value function quadratic. The feedback gain comes from carrying that quadratic value backward through time.",
    },
    "reachability": {
        "run": "A car near a wall may still look safe because there is space in front of it. Reachability asks the sharper question: from this speed and steering limit, is there any legal sequence of controls that avoids the wall no matter what disturbance arrives? The answer is a set of states, not a single path.",
        "math": "A backward reachable set collects states that can reach a target, or cannot avoid a bad target, under the allowed controls and disturbances. Safety means staying on the correct side of that set.",
    },
    "model-predictive-control": {
        "run": "An autonomous car plans five seconds ahead, but only drives the first tenth of a second. Then it looks again. The old plan was not wrong; it was temporary. Traffic moved, the measured state changed, and the next optimization should start from the real state, not the predicted one.",
        "math": "MPC repeatedly solves a finite-horizon problem, applies the first control, shifts the horizon, and solves again. Recursive feasibility asks whether that first control leaves tomorrow's problem solvable.",
    },
    "imitation-learning": {
        "run": "A person can show a robot how to pull a drawer without writing a reward for every contact force and handle angle. Imitation learning turns demonstrations into an action rule. The danger is closed-loop drift: one small mistake puts the robot in a state the teacher never showed.",
        "math": "The data are state-action pairs from an expert. The learned policy maps observations to actions. Training loss measures action mismatch on the demonstrated states, not on every state the learned policy may later visit.",
    },
    "reinforcement-learning": {
        "run": "If no expert can label every action, the robot can try actions and learn from delayed reward. A grasp may look bad at first contact but succeed after a wrist turn. RL has to connect the later score back to earlier actions without letting unsafe exploration damage the system.",
        "math": "The learner adjusts a policy or value estimate to increase expected return. The hard parts are delayed credit, exploration, and whether the reward truly matches the task.",
    },
    "model-based-rl": {
        "run": "A real robot should not need to crash into a shelf a thousand times to learn that shelves are hard. Model-based RL learns or uses a model, rehearses possible futures inside it, and spends real trials on the choices that look most informative or promising.",
        "math": "The learned model predicts next states or rollout outcomes. Planning through that model reduces real trial count, but model errors can create plans that work only inside the model.",
    },
}


def concept_run(concept: dict[str, Any]) -> dict[str, str]:
    if concept["id"] in CONCEPT_RUNS:
        return CONCEPT_RUNS[concept["id"]]
    return {
        "run": (
            f"{concept['worked_example']} Start from the ordinary pressure: {concept['ordinary_problem']} "
            f"The shortcut is to {concept['naive_approach'].lower()} That fails because {concept['why_naive_fails'].lower()} "
            f"So the page introduces {concept['mathematical_object'].lower()} and uses it to {concept['operation'].lower()}"
        ),
        "math": (
            f"The mathematical object is {concept['mathematical_object'].lower()} The operation is: "
            f"{concept['operation']} The boundary is: {concept['assumption_boundary']}"
        ),
    }


FAMILY_DEEPENING: dict[str, dict[str, str]] = {
    "problem-setup": {
        "pressure": "This family exists because a moving system does not obey wishes. A planner must name what is known, what can be changed, how the world moves, what future is preferred, and which lines cannot be crossed.",
        "operation": "Turn a story into state, action, dynamics, cost, horizon, constraints, and feasibility before choosing any solver.",
        "worked": "For a drone delivery task, 'get there fast' becomes position, velocity, attitude, battery, payload, wind, rotor thrust, no-fly zones, landing pad error, and safe touchdown speed.",
    },
    "optimization-foundations": {
        "pressure": "Before control chooses a path, ordinary optimization teaches what it means for a choice to be locally better, blocked by a constraint, or stuck at a boundary.",
        "operation": "Look at small changes in the decision and ask whether the objective can still be lowered without leaving the legal set.",
        "worked": "A thermostat setting may lower temperature error but hit a power limit. The gradient points toward a better setting; the constraint says whether that setting is legal.",
    },
    "trajectory-optimization": {
        "pressure": "A path is not a drawing between start and finish. Every point along it must be reachable from the previous point using real commands.",
        "operation": "Make the whole path the decision, enforce dynamics along the path, and ask the solver for a legal low-cost history.",
        "worked": "A robot arm moving around a fixture needs joint angles, velocities, and torques at many times, not just a start pose and an end pose.",
    },
    "dynamic-programming": {
        "pressure": "Some problems are too large if the controller lists every future action sequence. The repeated structure is that after one action, the remaining future is another control problem.",
        "operation": "Attach a future-cost number to each state, then compare actions by immediate cost plus the future value of the state they create.",
        "worked": "A rover chooses between a short rocky route and a longer smooth route by pricing wheel damage as a worse future state, not only by counting meters.",
    },
    "local-structure": {
        "pressure": "Near a planned motion, the full nonlinear problem may be more detail than the controller needs at every instant.",
        "operation": "Replace the local neighborhood with linear dynamics and quadratic cost, compute fast feedback, and use it only while the state stays near that neighborhood.",
        "worked": "A drone hovering near level can push back against a small drift with LQR; after impact, the same approximation is no longer a truthful picture.",
    },
    "safety-and-feasibility": {
        "pressure": "A plan can look good and still put the system into a state where no safe future remains.",
        "operation": "Track sets of states that can reach a target, avoid danger, or remain feasible after the next action.",
        "worked": "A car entering a narrow gap should ask whether braking or steering remains possible one second later, not only whether the next two seconds are collision-free.",
    },
    "replanning": {
        "pressure": "A long open-loop plan goes stale as soon as wind, traffic, contact, or estimation error changes the state.",
        "operation": "Solve a short future problem, apply the first command, measure again, and solve from the new state while protecting the next solve.",
        "worked": "An autonomous car replans after each small movement because nearby cars move and the measured state is more trustworthy than yesterday's prediction.",
    },
    "learning-based-control": {
        "pressure": "Sometimes the model, reward, or expert behavior is too hard to write down cleanly, but data can show part of the missing structure.",
        "operation": "Fit a policy, value, reward, or model from demonstrations or experience, then keep asking what state distribution, reward, and safety boundary the learner is actually using.",
        "worked": "A warehouse robot can clone a human drawer-opening motion, then use reward or a learned model to improve, while checking that mistakes do not move it outside the demonstrated states.",
    },
}


PRIMITIVE_DEEPENING: dict[str, str] = {
    "state": "The state is the present-tense record the controller trusts. If the record leaves out velocity, fuel, contact, or another car, two different futures may look identical.",
    "action": "The action is the command the machine can actually issue, not the outcome it wants. A drone commands thrust; height changes only after dynamics carry thrust forward.",
    "dynamics": "Dynamics are the rule that turns action into the next state. They are where mass, friction, actuator limits, and delay enter the story.",
    "cost": "Cost is the written scoreboard for futures. If damage, discomfort, or risk is missing from it, the controller is free to ignore those things.",
    "constraint": "A constraint is a line the plan may not cross: no collision, no empty battery, no torque beyond the motor, no state outside the safe set.",
    "value": "Value is future cost compressed into a number attached to the current state. It lets the controller compare actions without listing every later move.",
    "policy": "A policy is the rule that turns current information into an action. In closed loop, its own actions create the next states it must handle.",
    "uncertainty": "Uncertainty means the next state is not a single promised outcome. Wind, sensor noise, human drivers, and learned-model error all widen the future.",
    "feasibility": "Feasibility asks whether any legal plan exists before asking which legal plan is best.",
}


FORMULA_EXPLAINERS: list[dict[str, str]] = [
    {
        "name": "Dynamics",
        "shape": "x_next = f(x, u)",
        "problem": "A command is not a teleport. If the car turns the steering wheel, the next state depends on current speed, tire grip, and heading.",
        "object": "The object is a transition rule from present state and action to next state.",
        "operation": "Feed in the state and action, then propagate the consequence one step forward.",
        "worked": "If a drone has upward velocity 1 m/s and the controller cuts thrust, the next height may still rise for a moment while velocity falls. Dynamics explain that delay.",
        "failure": "If the model ignores wind, ice, contact, or actuator lag, the controller prices a future that the real system will not follow.",
    },
    {
        "name": "Objective",
        "shape": "total cost = path costs + terminal cost",
        "problem": "A future is not good just because it reaches the goal. It may use too much fuel, hit a wall, arrive late, or end with unsafe speed.",
        "object": "The object is a cost functional: a rule for scoring a whole history.",
        "operation": "Add the cost paid along the path and the cost left at the end.",
        "worked": "A rocket landing score can add fuel burn every second, then add a large final penalty for height error and touchdown speed.",
        "failure": "If the written cost omits damage or risk, the optimizer can choose a future that is cheap on paper and bad in the world.",
    },
    {
        "name": "Bellman Recursion",
        "shape": "V(x) = best action of cost now + value next",
        "problem": "The controller needs to judge a current action by the future state it creates, without listing every complete future.",
        "object": "The object is a value function: future cost stored at each state.",
        "operation": "For each action, add immediate cost to the value of the next state, then choose the best sum.",
        "worked": "A rover may pay one extra minute to avoid sharp rocks because the next state after the rocky shortcut has damaged wheels and worse future value.",
        "failure": "If the state is missing hidden information, the value table attaches the wrong future price to that state.",
    },
    {
        "name": "Hamiltonian",
        "shape": "H = stage cost + costate times dynamics",
        "problem": "A small action change affects cost now and also pushes the whole future state history.",
        "object": "The object is a local package that combines immediate cost with a backward price on state motion.",
        "operation": "Price a control change by adding what it costs now to what its state change costs later.",
        "worked": "For a rocket, more thrust burns fuel now but changes future velocity. The costate says how valuable that velocity change is later near touchdown.",
        "failure": "Hamiltonian conditions are necessary conditions; they can identify a candidate path without proving it is the best global path.",
    },
    {
        "name": "MPC",
        "shape": "solve horizon, apply first action, measure, repeat",
        "problem": "A long plan becomes stale after the first gust of wind, moving car, or bad state estimate.",
        "object": "The object is a finite-horizon problem rebuilt from the current measured state.",
        "operation": "Solve, use only the first command, shift the horizon, and solve again.",
        "worked": "A car plans five seconds ahead but executes only 0.1 seconds of steering and throttle before traffic is measured again.",
        "failure": "A short horizon without terminal protection can make a legal first move that leaves no legal move next time.",
    },
    {
        "name": "Policy Gradient",
        "shape": "move policy parameters toward higher return",
        "problem": "Sometimes the learner has no clean model or action labels, only rollouts and delayed reward.",
        "object": "The object is a parameterized policy that chooses actions from observations or states.",
        "operation": "Use rollout returns to nudge the policy toward actions that led to higher long-run reward.",
        "worked": "A grasping robot tries many wrist angles; successful lifts increase the probability of similar actions in similar poses.",
        "failure": "Sparse reward, unsafe exploration, or random lucky rollouts can push the policy in the wrong direction.",
    },
]


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
.fp { border-top: 1px solid var(--line); padding: 26px 0 8px; }
.kick { font-size: 12px; color: var(--accent-2); font-weight: 760; text-transform: uppercase; letter-spacing: .08em; }
.essay p { max-width: 76ch; font-size: 16px; color: #24323a; margin: 10px 0; }
.explain-box {
  border: 1px solid var(--line);
  border-left: 3px solid var(--accent);
  border-radius: 8px;
  background: var(--paper);
  padding: 14px 16px;
  margin: 14px 0;
}
.explain-box p { margin: 7px 0; }
.math {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #eef5f4;
  margin: 14px 0;
}
.math summary {
  cursor: pointer;
  padding: 10px 13px;
  color: var(--accent);
  font-weight: 760;
}
.math div { border-top: 1px solid var(--line); padding: 4px 14px 12px; }
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
<p>The current build has full transcript coverage, a complete minimum concept atlas, timestamped evidence records with manual deepening, and expanded teaching artifacts for derivations, examples, drills, solutions, and weak-claim repairs.</p>
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
        run = concept_run(concept)
        body = f"""
<p><a href="../concepts.html">Back to concept atlas</a></p>
<h1>{esc(concept['name'])}</h1>
<p class="lede">{esc(concept['plain_language_definition'])}</p>
<section class="fp">
  <div class="kick">01 · the ordinary pressure</div>
  <h2>Why this idea has to exist</h2>
  <div class="essay">
    <p>{esc(concept['ordinary_problem'])}</p>
    <p>The tempting shortcut is simple: {esc(concept['naive_approach'])} But that shortcut breaks because {esc(concept['why_naive_fails']).lower()}</p>
  </div>
</section>
<section class="fp">
  <div class="kick">02 · the object</div>
  <h2>What the math keeps track of</h2>
  <div class="essay">
    <p>The controller keeps track of {esc(concept['mathematical_object']).lower()} This answers a practical question: {esc(concept['recognition_test']).lower()}</p>
    <p>The operation is concrete: {esc(concept['operation'])}</p>
  </div>
</section>
<section class="fp">
  <div class="kick">03 · one concrete run</div>
  <h2>Work it through before naming the formula</h2>
  <div class="explain-box"><p>{esc(run['run'])}</p></div>
  <details class="math"><summary>the actual math, one level deeper</summary><div><p>{esc(run['math'])}</p></div></details>
</section>
<section class="fp">
  <div class="kick">04 · boundary</div>
  <h2>Where the idea stops working</h2>
  <div class="essay">
    <p>{esc(concept['assumption_boundary'])}</p>
    <p>If that boundary is crossed, the visible failure is this: {esc(concept['failure_mode']).lower()}</p>
    <p><strong>Recognize it in a new problem:</strong> {esc(concept['recognition_test'])}</p>
  </div>
</section>
<h2>Transcript Evidence</h2>
<section class="stack">{ev_cards or '<p class="muted">No evidence record yet.</p>'}</section>
<h2>Nearby Concepts</h2>
<p>{' '.join(f'<span class="pill">{concept_link(item, depth=1)}</span>' for item in related)}</p>
"""
        write(SITE / "concepts" / f"{concept['id']}.html", page(concept["name"], body, "concepts", depth=1))

    spine_items = [
        (
            "01",
            "Name the moving situation",
            "A control problem begins when a choice today changes what choices are available tomorrow. Before formulas, name the moving thing, the information you know now, the command you can issue, the rule that turns that command into motion, the future you prefer, and the lines you cannot cross.",
            "A delivery drone is not controlled by saying 'arrive quickly.' Its state includes position, velocity, attitude, battery, payload, and wind estimate. Its action is thrust or a lower-level motion command. Its cost trades time, energy, landing error, and smoothness. Its constraints include no-fly zones, thrust limits, battery reserve, and safe touchdown.",
        ),
        (
            "02",
            "Make the whole path the decision",
            "Static optimization chooses a point. Control chooses a path. Calculus of variations, costates, Hamiltonians, shooting, transcription, and collocation are different ways of saying that a legal answer is not one number; it is a history of states and actions that must fit the dynamics at every step.",
            "For a robot arm moving around a fixture, a shortest geometric curve can still require impossible torque. Direct methods put states and commands on a grid, enforce dynamics between neighboring grid points, and let the solver choose a path that the arm can physically trace.",
        ),
        (
            "03",
            "Price the future from each state",
            "Dynamic programming appears when the future after the next state is another copy of the same problem. The value function is the price tag on being in a state with all future choices still open. Bellman recursion is the bookkeeping rule: compare actions by the cost now plus the future value of the state they create.",
            "A rover may choose a longer route around rough ground because the short route damages its wheels. The immediate distance is smaller, but the next state has worse future value because every later move is harder.",
        ),
        (
            "04",
            "Use local structure when the world is near the plan",
            "LQR works when the real motion is close enough to a nominal motion that the dynamics look linear and the cost looks like a bowl. It is not magic feedback. It is a local promise: small errors near the planned state can be pushed back with a fast linear correction.",
            "A hovering drone can use LQR for a small drift. After clipping a branch and tumbling, the same local model is no longer the right picture; the state has left the region where the approximation tells the truth.",
        ),
        (
            "05",
            "Replan without losing tomorrow",
            "MPC turns planning into feedback by repeatedly solving a short future problem and applying only the first command. Reachability and recursive feasibility ask the question MPC alone can miss: after this first command, will the next problem still have a legal escape?",
            "A car can choose a narrow traffic gap that is collision-free for two seconds and still be making a bad control choice if the state after one second has no safe braking or steering option left.",
        ),
        (
            "06",
            "Learn only where written structure runs out",
            "Learning-based control is not a replacement for control thinking. It enters when the model is incomplete, the cost is hard to write, expert behavior is easier to show than specify, or trial feedback is the only teacher. The same questions remain: what is the state, what action is chosen, what future is being priced, and what failure does the learner create?",
            "Behavior cloning can teach a robot a drawer-pulling motion from demonstrations, but the learned policy may drift into a handle angle the expert never showed. RL can improve from reward, but if the reward pays only for speed, the robot may learn to damage the object quickly.",
        ),
    ]
    spine_html = "".join(
        f"""<section class="fp">
  <div class="kick">{num} · course move</div>
  <h2>{esc(title)}</h2>
  <div class="essay"><p>{esc(problem)}</p></div>
  <div class="explain-box"><p>{esc(example)}</p></div>
</section>"""
        for num, title, problem, example in spine_items
    )
    write(SITE / "course-spine.html", page("Course Spine", f"<h1>Course Spine</h1><p class=\"lede\">The course is one question repeated at larger scale: what should this system do now, knowing that the action changes the future it will have to live in?</p>{spine_html}", "spine"))

    family_cards = []
    for family in families:
        deep = FAMILY_DEEPENING.get(family["id"], {})
        links = " ".join(
            f'<span class="pill">{concept_link(concepts_by_id[cid])}</span>'
            for cid in family["concepts"]
            if cid in concepts_by_id
        )
        body = f"""
<div class="essay">
  <p>{esc(deep.get('pressure', family['problem']))}</p>
  <p><strong>The move:</strong> {esc(deep.get('operation', family['problem']))}</p>
</div>
<div class="explain-box"><p>{esc(deep.get('worked', family['problem']))}</p></div>
<p>{links}</p>
"""
        family_cards.append(card(family["name"], body))
    write(
        SITE / "families.html",
        page(
            "Method Families",
            f"""<h1>Method Families</h1>
<p class="lede">A method family is a response to a specific pressure: the path is too large, the future is delayed, the local model is enough, the plan goes stale, or the missing structure must be learned from data.</p>
<div class="essay">
  <p>Read this page as a map of why the course changes tools. The switch from direct methods to dynamic programming is not a change of fashion; it is a change in what is hard. Sometimes the hard part is making a legal path. Sometimes it is pricing all futures from a state. Sometimes it is keeping a short-horizon plan from destroying tomorrow. Sometimes the missing piece has to be learned from demonstrations or reward.</p>
  <p>The same test applies to every family: what real mistake would happen if this family did not exist?</p>
</div>
<section class="stack">{''.join(family_cards)}</section>""",
            "families",
        ),
    )

    primitive_cards = []
    for p in primitives:
        links = " ".join(
            f'<span class="pill">{concept_link(concepts_by_id[cid])}</span>'
            for cid in p["used_by"]
            if cid in concepts_by_id
        )
        body = f"<p>{esc(PRIMITIVE_DEEPENING.get(p['id'], p['plain_language']))}</p><p>{links}</p>"
        primitive_cards.append(card(p["name"], body))
    write(
        SITE / "primitives.html",
        page(
            "Primitives",
            f"""<h1>Mathematical Primitives</h1>
<p class="lede">These are the reusable pieces. They appear in different formulas, but each one answers an everyday control question.</p>
<div class="essay">
  <p>A primitive is not a small word to memorize. It is a role in the control story. State says what must be carried forward. Action says what can actually be commanded. Dynamics say how the command changes the world. Cost says which future is preferred. Constraint says what cannot be crossed. Value prices the future from here. Policy chooses the next action. Uncertainty admits that the next state may not be the one the planner hoped for.</p>
  <p>Once these pieces are named, the course becomes less mysterious. New methods mostly rearrange the same pieces: direct transcription lays them on a time grid, dynamic programming stores future cost in value, MPC rebuilds them every tick, and learning estimates one of them from data.</p>
  <p>If a plan fails, one primitive is usually lying, missing, or too loosely written. Debug the primitive before blaming the solver.</p>
</div>
<section class="grid">{''.join(primitive_cards)}</section>""",
            "primitives",
        ),
    )

    formula_cards = []
    for item in FORMULA_EXPLAINERS:
        body = f"""
<p class="tag">{esc(item['shape'])}</p>
<div class="essay">
  <p>{esc(item['problem'])}</p>
  <p><strong>The object:</strong> {esc(item['object'])}</p>
  <p><strong>The operation:</strong> {esc(item['operation'])}</p>
</div>
<div class="explain-box"><p>{esc(item['worked'])}</p></div>
<details class="math"><summary>where it fails</summary><div><p>{esc(item['failure'])}</p></div></details>
"""
        formula_cards.append(card(item["name"], body))
    write(
        SITE / "formula-reader.html",
        page(
            "Formula Reader",
            f"""<h1>Formula Reader</h1>
<p class="lede">A formula is a machine for doing one job. Read it by asking what it operates on, what gets changed, what future is being priced, and where the reading becomes false.</p>
<div class="essay">
  <p>The symbols in AA203 are easy to misread as decoration. They are not. Each formula is a small machine: put in a state, an action, a cost, a model, or a rollout; get out a next state, a price on the future, a constraint check, or a policy update.</p>
  <p>The useful reading order is always the same. First ask what real situation forced the formula to exist. Then identify the object it stores. Then name the operation it performs. Only after that should the symbols matter.</p>
</div>
<section class="stack">{''.join(formula_cards)}</section>""",
            "formulas",
        ),
    )

    derivation_cards = []
    for item in derivations:
        linked = " ".join(f'<span class="pill">{concept_link(concepts_by_id[cid])}</span>' for cid in item.get("linked_concepts", []) if cid in concepts_by_id)
        body = f"""
<p><strong>Problem:</strong> {esc(item['problem'])}</p>
<p><strong>Starting point:</strong> {esc(item['starting_point'])}</p>
<ol>{''.join(f'<li>{esc(step)}</li>' for step in item['steps'])}</ol>
<p><strong>Formula shape:</strong> {esc(item['formula_shape'])}</p>
<p><strong>Why it works:</strong> {esc(item['why_it_works'])}</p>
<p><strong>First-principles intuition:</strong> {esc(item.get('intuition', ''))}</p>
<p><strong>Common wrong turn:</strong> {esc(item.get('common_wrong_turn', ''))}</p>
<p><strong>Failure test:</strong> {esc(item['failure_test'])}</p>
<p><strong>Transfer check:</strong> {esc(item.get('transfer_check', ''))}</p>
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
  <tr><th>Decision Pressure</th><td>{esc(item.get('decision_pressure', ''))}</td></tr>
  <tr><th>Method Boundary</th><td>{esc(item.get('method_boundary', ''))}</td></tr>
  <tr><th>Transfer Question</th><td>{esc(item.get('transfer_question', ''))}</td></tr>
</table>
<p>{linked}</p>
"""
        example_cards.append(card(item["title"], body))
    write(SITE / "worked-examples.html", page("Worked Examples", f"<h1>Worked Examples</h1><p class=\"lede\">Concrete setups that force the learner to name state, action, cost, constraints, method route, and failure signal.</p><section class=\"stack\">{''.join(example_cards)}</section>", "derivations"))

    drill_cards = []
    solution_cards = []
    for item in drills:
        linked = " ".join(f'<span class="pill">{concept_link(concepts_by_id[cid])}</span>' for cid in item.get("linked_concepts", []) if cid in concepts_by_id)
        criteria = section_list([esc(criterion) for criterion in item.get("grading_criteria", [])])
        drill_cards.append(
            card(
                item["title"],
                f"<p>{esc(item['prompt'])}</p><p><strong>Wrong turn to avoid:</strong> {esc(item['wrong_turn'])}</p><p><strong>What a strong answer must include:</strong></p>{criteria}<p>{linked}</p>",
            )
        )
        solution_cards.append(
            card(
                f"{item['title']} Solution",
                f"<p><strong>Prompt:</strong> {esc(item['prompt'])}</p><p><strong>Wrong turn:</strong> {esc(item['wrong_turn'])}</p><p><strong>Strong answer:</strong> {esc(item['strong_answer'])}</p><p><strong>Solution walkthrough:</strong> {esc(item.get('solution_walkthrough', ''))}</p><p><strong>Grading criteria:</strong></p>{criteria}<p>{linked}</p>",
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
                f"<p><strong>Diagnosis:</strong> {esc(item['diagnosis'])}</p><p><strong>Failure consequence:</strong> {esc(item.get('failure_consequence', ''))}</p><p><strong>Stronger version:</strong> {esc(item['strong'])}</p><p><strong>Transfer prompt:</strong> {esc(item.get('transfer_prompt', ''))}</p>",
            )
        )
    write(SITE / "misconceptions.html", page("Misconceptions", f"<h1>Misconceptions And Weak-Claim Repairs</h1><section class=\"grid\">{''.join(misconception_cards)}</section>", "review"))

    evidence_html = "".join(evidence_card(row) for row in evidence)
    write(SITE / "evidence.html", page("Evidence", f"<h1>Evidence Ledger</h1><p class=\"lede\">Each record points to a local transcript window, timestamp URL, and manual statement of what the transcript supports versus what the site synthesizes beyond it.</p><section class=\"stack\">{evidence_html}</section>", "evidence"))

    review = [
        ("First-principles depth", "Open a setup concept, a dynamic-programming concept, an MPC concept, and a learning concept. Check that each starts from the control pressure before formulas."),
        ("Evidence discipline", "Open evidence records and verify that local transcript windows support the concept vocabulary without pretending to prove the whole synthesis."),
        ("Practice usefulness", "Run the drills and verify the solutions name wrong turns, not just final answers."),
        ("Audit path", "Use the completion audit, evidence ledger, and provenance page to verify transcript coverage, timestamp anchors, generated pages, and local rebuild commands."),
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
        ("Transcript coverage", "pending audit", f"{transcript_index.get('available_transcripts', 0)}/{transcript_index.get('videos', 0)} transcripts before audit reconciliation"),
        ("Concept atlas", "present", f"{len(concepts)} concepts generated"),
        ("Evidence ledger", "pending audit", f"{len(evidence)} evidence records before audit reconciliation"),
        ("Teaching artifacts", "present", f"{len(derivations)} derivations, {len(worked_examples)} examples, {len(drills)} drills, and {len(weak_claim_repairs)} repair cases generated from analysis/teaching"),
        ("Completion readiness", "pending audit", "quality audit not loaded yet"),
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
        blockers = quality_audit.get("completion_readiness", {}).get("remaining_blockers", [])
        audit_rows[5] = (
            "Completion readiness",
            "clear" if not blockers else "remaining",
            "No audit blockers found." if not blockers else "; ".join(blockers),
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
<p>Run <code>python3 scripts/build_first_principles_atlas.py</code>, then <code>python3 scripts/build_teaching_artifacts.py</code>, then <code>python3 scripts/audit_course_quality.py</code>, then <code>python3 scripts/build_site.py</code>, then <code>python3 scripts/validate_all.py</code>.</p>
""",
            "provenance",
        ),
    )
    print(f"built {len(list(SITE.rglob('*.html')))} HTML pages in {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
