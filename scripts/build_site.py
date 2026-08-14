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


def sentence_body(value: str) -> str:
    return value.strip().rstrip(".")


def recognition_sentence(value: str) -> str:
    text = sentence_body(value)
    lowered = text[:1].lower() + text[1:]
    for prefix in ["Use it when ", "Use this when ", "Use this term when "]:
        if text.lower().startswith(prefix.lower()):
            return "Use it when " + text[len(prefix):]
    if text.lower().startswith("choose this lens when "):
        return "Use this lens when " + text[len("choose this lens when "):]
    if text.lower().startswith("before asking "):
        body = text[len("before asking "):]
        body = re.sub(r", ask\s+", "; first ask ", body, flags=re.I)
        return "Use it before asking " + body
    if text.lower().startswith("ask "):
        return "Use it when you need to " + lowered
    if text.lower().startswith("look for "):
        return "Use it when you need to " + lowered
    return "Use it when you need to " + lowered


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
        "run": "A drone pilot may want the drone to be two meters higher, but height is not the command. Suppose the drone is at 10 meters, moving upward at 0.2 m/s, and the controller raises average rotor thrust from hover thrust to 48 percent above hover for the next 0.1 seconds. That command changes vertical acceleration first. Only after acceleration changes does velocity change, and only after velocity changes does height change. If the plan writes 'go to 12 meters' as the action, it has skipped the actuator and asked the optimizer for an outcome the drone cannot directly issue.",
        "math": "The action u is the command passed into the dynamics. A simple vertical model might update velocity by v_next = v + dt * a(u) and height by h_next = h + dt * v_next. With dt = 0.1, the thrust command changes acceleration during that tenth of a second; it does not set h_next to the desired height. The next state is produced by x_next = f(x, u), so action limits are limits on u, not on wishes about x_next.",
    },
    "dynamics": {
        "run": "If a car is moving at 20 m/s on dry asphalt, a small steering command for the next 0.2 seconds may change heading enough to begin a lane move. On ice, the same steering command can produce much less lateral force, so the next state has nearly the same heading but more sideways slip. The action was identical; the next state changed because the rule connecting tire force, speed, heading, and road grip changed. Dynamics are that rule. Without it, the planner is only drawing where it wishes the car would go.",
        "math": "Dynamics can be written as x_next = f(x, u) in discrete time or dx/dt = f(x, u) in continuous time. A simple update might carry position by p_next = p + dt * v and heading by theta_next = theta + dt * yaw_rate(x,u,grip). The grip term is not decoration. It changes how the same steering action becomes the next state, which is why a dry-road plan can fail on ice.",
    },
    "objective-cost-function": {
        "run": "A parking controller compares two futures. Path A reaches the spot in 8 seconds but passes 6 centimeters from the wall and uses hard steering. Path B takes 12 seconds, stays 35 centimeters from the wall, and turns gently. If the cost counts only time, Path A wins. If the cost adds wall clearance, steering effort, and final alignment, Path B may win. The objective is the written scoreboard; the optimizer does not know the human meaning of safe, smooth, or rude unless those penalties are in the score or constraints. The chosen path reveals what the score truly valued on pavement.",
        "math": "A typical objective adds stage costs along the path and a terminal cost at the end: J = sum_k stage_cost(x_k,u_k) + terminal_cost(x_N). A parking stage cost might include 1.0*time_step + 0.2*steering_effort + 5.0*wall_risk. The weights are not decoration; they decide whether saving four seconds is worth scraping the car. If damage is absent from J and not forbidden by a constraint, the controller is free to choose damage.",
    },
    "horizon": {
        "run": "A delivery drone is 60 meters from the pad, flying 8 m/s, with 18 percent battery left. A three-second horizon sees only the next 24 meters, so flying straight at full speed looks cheap. A thirty-second horizon sees the descent, crosswind near the building, battery reserve, and the need to slow before touchdown. The short horizon may choose the fast first command and leave the drone too low on battery to reject the later wind. The horizon is the length of future the controller is willing to put on the table; if the real danger appears after the table ends, the optimizer cannot price it.",
        "math": "A finite-horizon problem chooses actions for k = 0...N. With dt = 0.5 seconds and N = 6, the controller sees only 3 seconds. With N = 60, it sees 30 seconds. N is not just a number of samples; it decides whether delayed costs such as low battery, touchdown speed, or wind near the landing zone can enter the optimization before the first action is chosen.",
    },
    "constraints": {
        "run": "A robot arm moving a camera around a shelf can save energy by cutting through the shelf corner. Suppose the gripper must stay at least 4 centimeters from the shelf and each joint motor is limited to 12 newton-meters of torque. A path that clears the shelf by -1 centimeter or asks for 15 newton-meters may have a lower written cost, but it is not a candidate path. Constraints remove that future from the legal set before the optimizer compares scores.",
        "math": "A constraint is an equation or inequality such as g(x,u) <= 0. A clearance constraint might be 0.04 - distance_to_shelf(x_k) <= 0 at every grid point, and a torque bound might be abs(tau_k) <= 12. A candidate path is admissible only when every required constraint is satisfied at the relevant time; low cost cannot buy permission to cross a hard physical limit.",
    },
    "feasibility": {
        "run": "A car is 18 meters behind a stopped truck, moving 22 m/s, with a wet-road braking limit of 6 m/s^2. Even full braking needs roughly v^2/(2a), or about 40 meters, before the car stops. A lane change is also illegal because a truck is beside it with only 0.5 meters of side clearance. In that state, the question is not which plan is best. The feasible set may already be empty because no allowed braking, steering, or acceleration sequence avoids the blocked space. The controller should report the emergency boundary, not pretend that a slightly cheaper collision path is a plan.",
        "math": "The feasible set contains states and actions satisfying dynamics, bounds, and path constraints. In symbols, a horizon plan is feasible only if each x_{k+1}=f(x_k,u_k), each u_k stays within actuator limits, and every clearance and speed constraint is satisfied. If the set F(x_0) is empty, optimization has no legal candidate to compare; the correct output is infeasibility, not a heroic best effort.",
    },
    "static-optimization": {
        "run": "Choosing one thermostat setting for the next hour is a static problem. Choosing a heater command every second while room temperature changes is control. Static optimization is the smaller grammar: decision, objective, constraint, and local improvement.",
        "math": "A static problem chooses z to minimize J(z) subject to constraints. There is no evolving state unless the problem is extended into a time-indexed control problem.",
    },
    "gradient-first-order-condition": {
        "run": "A rover adjusting a steering angle can try a tiny change left and a tiny change right. If every tiny legal change makes the score worse, the rover is locally stuck. The gradient is the local slope that says which small change lowers cost fastest.",
        "math": "For an unconstrained smooth minimum, the first derivative is zero. With constraints, the first-order condition includes which legal directions remain available.",
    },
    "calculus-of-variations": {
        "run": "A thrown ball path is not chosen at one point. The whole curve matters. Calculus of variations asks what happens to total cost if the entire path is nudged slightly, while endpoints or dynamics are respected.",
        "math": "The object is a functional: it takes a whole curve and returns a number. The operation is to perturb the curve and set the first variation to zero for an optimal candidate.",
    },
    "costate-adjoint-variable": {
        "run": "A rocket one meter too low early in flight may force extra fuel burn later. The costate is the backward price of that state error. It tells the controller how expensive a small state mistake is after future dynamics have had time to amplify it.",
        "math": "The costate evolves backward from terminal conditions. It carries the derivative of future cost with respect to state, so current control can be priced by downstream effect.",
    },
    "hamiltonian-optimal-control": {
        "run": "More thrust costs fuel now and changes velocity later. The Hamiltonian puts both facts in one local expression: immediate cost plus the costate's price for how the dynamics move the state.",
        "math": "H(x,u,lambda) combines stage cost with lambda times dynamics. Stationarity with respect to u gives a necessary condition for a locally optimal control.",
    },
    "indirect-methods": {
        "run": "Instead of giving a big nonlinear program to a solver, an indirect method first derives the equations an optimal path must obey. It is like finding the laws of the winning path before trying to compute the path itself.",
        "math": "The method derives state equations, costate equations, boundary conditions, and stationarity conditions, then solves that boundary-value problem.",
    },
    "value-function": {
        "run": "A rover has two first moves. The rocky shortcut costs 1 minute now but leaves the rover with damaged wheels, and from that damaged state the remaining trip is estimated at 18 minutes. The smooth route costs 4 minutes now but leaves the rover healthy, with 7 minutes of remaining trip. If the rover looks only at the next move, it chooses the shortcut. If it reads the value of the next state, it compares 1 + 18 against 4 + 7 and chooses the smooth route. The value of a state is that stored future burden.",
        "math": "V(x) stores the best future cost from state x. Once V is known, a current action can be judged by immediate cost plus the value of the next state it creates: choose u by comparing cost(x,u) + V(f(x,u)). In the rover run, the rocky next state has V = 18 and the smooth next state has V = 7, so the current action changes because the future price is attached to the state after the move.",
    },
    "bellman-recursion": {
        "run": "A warehouse robot stands at a junction and can enter aisle A or aisle B. Aisle A costs 2 seconds now and leaves the robot in a crowded state whose stored future value is 9. Aisle B costs 5 seconds now and leaves the robot beside a clear lane whose stored future value is 3. The Bellman step does not list every route to the loading dock. It computes A: 2 + 9 = 11 and B: 5 + 3 = 8, then stores 8 as the value of the junction and chooses aisle B. Choosing A would be greedy about the next aisle and blind to the jam after it.",
        "math": "In the deterministic case, V(x) = min_u [cost(x,u) + V(f(x,u))]. The bracket is the work: for each legal action u, move to f(x,u), read the value stored there, add the immediate cost, and keep the smallest total. With uncertainty, replace the single next value with an expected next value over possible next states.",
    },
    "direct-transcription": {
        "run": "A robot arm must move from joint angle 0.0 rad to 1.2 rad in 0.6 seconds while staying under a torque limit. Direct transcription does not ask for a smooth curve in one piece. It creates grid variables at t = 0.0, 0.2, 0.4, and 0.6 seconds: joint angle, joint velocity, and torque at each point. If the grid says the arm is at 0.4 rad with velocity 1.0 rad/s at t = 0.2, then the dynamics predict roughly 0.6 rad at t = 0.4 after the chosen torque. If the next grid variable says 0.9 rad, the defect is 0.3 rad. That defect must be driven to zero or the path is a drawing, not a real arm motion.",
        "math": "The continuous path becomes decision variables x_0...x_N and u_0...u_N. A defect constraint has the form defect_k = x_{k+1} - step(x_k,u_k). Direct transcription asks the optimizer to choose all grid states and controls while also enforcing defect_k = 0, torque bounds, endpoint constraints, and collision constraints. The grid points are therefore not independent dots; they are tied by equations that make neighboring states obey real dynamics.",
    },
    "shooting-methods": {
        "run": "A small test cart starts at x = 0 meters with v = 0 m/s and must stop at x = 10 meters after 2 seconds. Use dt = 1 second and let the optimizer choose only two acceleration commands, u_0 and u_1. Try u_0 = 4 m/s^2 and u_1 = -1 m/s^2. With a simple update that changes velocity first and then moves the cart, the first command gives v_1 = 4 m/s and x_1 = 4 meters. The second command gives v_2 = 3 m/s and x_2 = 7 meters, so the cart is still 3 meters short and still moving. The optimizer cannot move x_1 or x_2 by hand. It changes the guessed controls, simulates again, and reads the endpoint miss. If the cart must avoid a camera cable between x = 5.0 and x = 5.5 meters, shooting can only check that cable after the simulated states appear. That is why shooting is small and natural when controls are the main unknown, but awkward when many state limits must be enforced along the way.",
        "math": "In shooting, only u_0 and u_1 are decision variables in this two-step example. The states are produced by repeated dynamics such as v_{k+1}=v_k + dt*u_k and x_{k+1}=x_k + dt*v_{k+1}. The endpoint residual can be written as residual r = [x_2 - 10, v_2 - 0]. The optimizer changes u, integrates forward again, and tries to drive r toward zero while reducing cost. Single shooting makes one long chain from the initial state to the end, so a small early control change can move every later state. Multiple shooting shortens that chain: introduce a join state x_join at t = 1 second, simulate each shorter piece, and add a matching condition such as gap_1 = x_join - step(x_0,u_0). The join state is not free to lie; the gap must go to zero. The benefit is that the optimizer gets handles in the middle while dynamics still decide whether the pieces connect.",
    },
    "collocation": {
        "run": "A robot arm must swing around a fixture between t = 0.0 and t = 0.4 seconds. The endpoints can look legal: the gripper is left of the fixture at the start and right of it at the end. Collocation adds a midpoint at t = 0.2 seconds. If the polynomial path puts the gripper at x = 0.10 meters while the fixture occupies x = 0.08 to 0.12 meters, the midpoint exposes the collision that endpoint checking hid. Endpoint-only checking would accept the move; collocation rejects it because the checked interior state sits inside the fixture. The method also checks whether the path derivative at that midpoint matches the velocity predicted by the arm dynamics.",
        "math": "Collocation uses polynomial or grid approximations and enforces defect equations at selected points. A midpoint defect can be written as defect_mid = path_derivative_mid - f(x_mid,u_mid). Driving defect_mid to 0 says the curve's slope at the checked point agrees with the dynamics. A zero start error and a zero finish error are not enough; the curve must also point in a physically possible direction where it is sampled. More collocation points make it harder for the optimizer to hide a collision, torque spike, or impossible acceleration between endpoints.",
    },
    "trajectory-optimization": {
        "run": "A walking robot needs to move its foot from behind a box to the floor in front of it over 1.2 seconds. The answer is not one footstep point. At t = 0.0, 0.3, 0.6, 0.9, and 1.2 seconds, the plan must name body angle, foot position, joint velocity, and motor torque. A path that clears the box at the sampled foot positions can still fail if the body leans too far at t = 0.6 or the knee torque exceeds 40 newton-meters at t = 0.9. A start-and-finish plan would hide the fall in the middle. Trajectory optimization treats that whole state-action history as the decision.",
        "math": "The decision is a sequence or curve of states and controls, such as x_0...x_N and u_0...u_{N-1}. The solver minimizes path cost while satisfying dynamics x_{k+1}=f(x_k,u_k), boundary conditions, and constraints along the trajectory. Each time index contributes cost and must pass its own balance and torque legality checks. A valid answer must make every neighboring pair physically connected, not only put the start and finish in good-looking places while hiding trouble.",
    },
    "dynamic-programming": {
        "run": "A grid rover is two cells from the charging pad. The goal cell has value 0. The cell just before the goal has value 1 because one legal move reaches the pad. Now update a muddy cell beside it. Moving right costs 1 and reaches the value-1 cell, so that branch costs 2. Moving down costs 3 and reaches a rough cell with value 6, so that branch costs 9. Dynamic programming writes V(muddy) = 2 and stores the right move. The rover did not plan every full path at once; it reused values already written for smaller future problems. That reuse is the whole computational bargain.",
        "math": "Dynamic programming solves coupled subproblems indexed by state. A deterministic update has the same shape as V(s) = min_a [c(s,a) + V(next(s,a))]. The backward pass starts from terminal values, then writes neighboring state values, then uses those values to write earlier states. The order matters because each update needs future values that have already been assigned or are being iterated toward consistency.",
    },
    "lqr": {
        "run": "A small delivery cart is 20 centimeters left of the center line, so write the lateral error as e = 0.20 meters. Near the center line, one steering correction can be approximated as e_next = e + u, where u is the sideways change produced over the next short step. The cart dislikes being off-center, but it also dislikes hard steering. A simple local score is 5*e^2 + u^2 now, plus a future penalty 20*e_next^2. If u = 0, the cart stays 20 centimeters off and pays the future penalty. If u = -0.20, the next error is zero but the steering effort is larger. The best local compromise is not a slogan; minimizing u^2 + 20*(0.20 + u)^2 gives u = -0.190 meters. The feedback rule is therefore push back almost the full measured error, but not quite, because steering itself has a price. If the cart is 5 centimeters left instead, the same local rule gives a smaller correction. That proportional correction is what LQR turns into a gain.",
        "math": "LQR assumes linear dynamics such as x_{k+1}=A_k x_k + B_k u_k and a quadratic cost such as x_k^T Q_k x_k + u_k^T R_k u_k plus a terminal quadratic. The important closure is that a quadratic future value stays quadratic when carried one step backward through linear dynamics. In the scalar cart example, minimize J(u)=u^2 + 20*(0.20 + u)^2. The derivative is 2u + 40*(0.20 + u), so 42u + 8 = 0 and u = -8/42 = -0.190. Written as feedback, u = -K e with K = 20/21. Larger R would make K smaller because control effort is expensive; larger future state penalty would make K closer to 1. LQR stops being the right explanation when the local model is false, the actuator saturates, or a hard state constraint matters, because those features are not inside the plain linear-quadratic problem.",
    },
    "stochastic-dynamic-programming": {
        "run": "A delivery rover can cross gravel or detour around it. Crossing gravel costs 1 minute now. The rover moves as commanded with probability 0.6 and reaches a state with future value 5, slips left with probability 0.3 and reaches a state with future value 12, or slips right with probability 0.1 and reaches a state with future value 20. The next state is not one promise. The expected future value is 0.6*5 + 0.3*12 + 0.1*20 = 8.6, so the gravel action costs 1 + 8.6 before comparing it with the detour. If the detour costs 4 minutes now and then has future value 4, its total is 8, so the safer-looking longer route wins.",
        "math": "The stochastic Bellman update uses an expectation over next states: cost(x,u) + sum over x_next of P(x_next|x,u) V(x_next). The probabilities are part of the model. If the 0.1 slip-right event reaches a dangerous state, its value still enters the average even though it is unlikely. A policy that ignores that branch is not optimistic in a harmless way; it has priced a different world than the rover will face.",
    },
    "local-quadratic-approximation": {
        "run": "A robot gripper is following a planned motion, but at one instant it is 6 centimeters too far left. The full contact model is messy: if the gripper moves a little right, the error improves; if it moves too far, it hits the rim of the bin and the real cost jumps. Around the current command, test three nearby nudges. At delta u = -0.02 meters the measured local score is 5.8. At delta u = 0 meters the score is 4.0. At delta u = 0.02 meters the score is 3.0. Those three readings say the local slope is negative: moving right helps. They also show the curve is bending upward, so the next improvement should get smaller. A local quadratic model is the small bowl fitted to that neighborhood, not a promise about the whole bin. It lets the solver compute a correction before trying the real motion again. If the fitted bowl says jump 12 centimeters right, the controller should distrust that step because the data came from nudges of only 2 centimeters.",
        "math": "Around a nominal state and action, write the change as delta x and delta u. A second-order local model has the shape q(delta u) = c + g*delta u + 0.5*H*delta u^2 when delta x is fixed for this one small calculation. Suppose the fitted numbers are c = 4.0, g = -70, and H = 2500. Setting the derivative to zero gives g + H*delta u = 0, so delta u* = -g/H = 0.028 meters. The math says try a 2.8 centimeter rightward correction, then remeasure and refit around the new point. In control, the same idea is applied to dynamics and value: linearize the dynamics, quadratize the cost or Q function, solve the easier local problem, and take a guarded step. The boundary is the trust region. If the proposed delta u is much larger than the neighborhood used to fit g and H, the quadratic may be explaining empty space rather than the real system.",
    },
    "reachability": {
        "run": "Two cars are 5 meters apart along the road. The rear car is drifting toward the front car's lane at 0.6 meters per second, and the front car can move sideways at at most 0.4 meters per second. A one-second plan that only checks the current gap may say the front car is safe because there is still 1.2 meters of lateral space. Reachability asks a different question: if the rear car gets one bad push from wind or a steering error, is there still any legal evasive command that keeps the cars out of the collision target set? Suppose the bad target is lateral distance below 0.3 meters. If the rear car can close 0.6 meters while the front car can open only 0.4 meters, then a state with only 0.5 meters of lateral gap is already in trouble: after one second the worst case can leave 0.3 meters or less. A state with 1.2 meters of lateral gap is outside that one-step danger set because the front car still has enough room to grow the gap. The output is not a single heroic swerve. It is a map of starting states: these states are already unsafe under the modeled disturbance, these states still have a safety move.",
        "math": "For an avoidance question, define the target set as collision states, for example T_bad = {gap <= 0.3 meters}. A simple one-step predecessor calculation marks a state unsafe if there exists a disturbance w such that for every legal control u, next_gap(gap,u,w) is in T_bad. With gap = 0.5, front control u can add at most 0.4 meters of lateral separation and disturbance w can remove 0.6 meters, so next_gap <= 0.5 + 0.4 - 0.6 = 0.3. That starting state belongs to the backward avoidance set A_1. With gap = 1.2, the same worst case gives next_gap <= 1.0, so it is not in this one-step bad set. For a goal-reaching question, the quantifiers flip: for all disturbances, there must exist a control that reaches the good target. Reachability is hard because it prices the fight between control and disturbance over sets of states, not only one predicted path.",
    },
    "model-predictive-control": {
        "run": "A warehouse cart is 3.0 meters from a loading mark and is moving at 1.0 m/s. Every 0.5 seconds it solves a small plan with three future acceleration commands. At 10:00:00 the optimizer predicts this sequence: brake at -0.8 m/s^2, then -0.6, then -0.2. It also predicts positions 3.45 meters, 3.75 meters, and 3.95 meters from the start of the aisle while staying below the 4.0 meter stop line. MPC applies only the first command, -0.8 m/s^2, for the next 0.5 seconds. A floor bump slows the cart more than expected, so the measured state at 10:00:00.5 is position 3.40 meters and velocity 0.50 m/s, not the predicted 3.45 meters and 0.60 m/s. The controller now discards the old second and third commands as promises made from the wrong state. It solves again from the measured state, with a shifted horizon that now covers 10:00:00.5 to 10:00:02.0. The method is not 'plan once carefully.' It is 'plan, use the first piece, measure, and make a new plan from reality.'",
        "math": "At time k, MPC solves a finite-horizon problem for variables u_0...u_{N-1} and predicted states x_0...x_N with x_0 = x_measured(k). The optimization minimizes predicted cost while enforcing dynamics, input bounds, state bounds, and any terminal rule. The implemented policy is pi_MPC(x_measured(k)) = u_0^*, the first control from that solve. After applying u_0^*, the real system produces x_measured(k+1). The next problem is not anchored at the old prediction x_1^pred if the sensor says otherwise; it uses x_0 = x_measured(k+1). This is why MPC is closed loop even though each solve is an open-loop optimization. The boundary is speed and future protection: if the solver is too slow, or the horizon and terminal structure allow a first move that leaves no feasible continuation, the loop can make a legal-looking move now and fail one step later.",
    },
    "recursive-feasibility": {
        "run": "A car can choose a legal steering command that fits through a narrow gap now but leaves no legal braking option one second later. Recursive feasibility rejects that move because today's feasible plan must hand tomorrow another feasible problem.",
        "math": "If x_k is feasible and the MPC applies u_k, recursive feasibility requires the resulting x_{k+1} to remain inside a set from which a feasible horizon plan exists.",
    },
    "stability-under-replanning": {
        "run": "A warehouse robot that replans every second can keep changing its mind and circle the same aisle forever. Stability under replanning asks for more than legality: each replan should make durable progress toward the goal or reduce a trusted measure of error.",
        "math": "A terminal cost, terminal set, or Lyapunov-like decrease condition can make repeated finite-horizon solves behave like one stable closed-loop controller.",
    },
    "imitation-learning": {
        "run": "A person can show a robot how to pull a drawer without writing a reward for every contact force and handle angle. Imitation learning turns demonstrations into an action rule. The danger is closed-loop drift: one small mistake puts the robot in a state the teacher never showed.",
        "math": "The data are state-action pairs from an expert. The learned policy maps observations to actions. Training loss measures action mismatch on the demonstrated states, not on every state the learned policy may later visit.",
    },
    "behavioral-cloning": {
        "run": "A robot sees thousands of examples where a human moves the gripper toward a handle. Behavioral cloning treats this like supervised learning: given this observation, predict the expert's action. It is simple, but it only trains on states the expert visited.",
        "math": "The policy parameters are fit by minimizing action prediction loss on demonstration pairs. Closed-loop success also depends on what states the learned policy creates after its own errors.",
    },
    "distribution-shift-imitation": {
        "run": "A cloned driving policy may drift a little right of lane center. The expert data has few examples from that off-center state because the expert rarely made the mistake. The learned policy now has to act in a part of the world where it was not trained.",
        "math": "Training data comes from the expert's state distribution, but deployment states come from the learned policy's distribution. Small action errors can compound because those distributions differ.",
    },
    "reinforcement-learning": {
        "run": "If no expert can label every action, the robot can try actions and learn from delayed reward. A grasp may look bad at first contact but succeed after a wrist turn. RL has to connect the later score back to earlier actions without letting unsafe exploration damage the system.",
        "math": "The learner adjusts a policy or value estimate to increase expected return. The hard parts are delayed credit, exploration, and whether the reward truly matches the task.",
    },
    "reward": {
        "run": "A robot rewarded only for moving an object to a target quickly may slap the object across the table and break it. The reward was not wrong by syntax; it was missing the real task values: gentle contact, no damage, and controlled motion.",
        "math": "Reward is the scalar feedback used to compute return. The learned behavior follows the written reward signal, including its omissions and loopholes.",
    },
    "policy": {
        "run": "A thermostat policy reads temperature and decides heat on or off. A robot policy reads camera, joint, and gripper state and decides a motion command. The policy is the closed-loop rule, not a one-time plan.",
        "math": "A policy maps state or observation to action, possibly as a probability distribution. In deployment, the policy's action changes the next input it will see.",
    },
    "value-based-rl": {
        "run": "A game-playing agent may not know the best move directly, but it can learn which board states tend to lead to higher future return. It then picks actions by looking at the values of the states those actions create.",
        "math": "Value-based RL learns V(x) or Q(x,u) from sampled rewards and transitions. The policy is obtained by choosing actions with high estimated value.",
    },
    "policy-optimization": {
        "run": "A walking robot with a neural policy may not have a small action table to fill. Policy optimization changes the policy parameters directly, making actions that led to better rollouts more likely and harmful actions less likely.",
        "math": "The objective is expected return under the current policy. Updates estimate a direction in parameter space that should increase that return.",
    },
    "exploration": {
        "run": "A robot that always repeats the first safe grasp it found may never learn a better grasp. A robot that explores wildly may drop objects or hit the shelf. Exploration is the controlled search for trials that teach the policy without wrecking the task.",
        "math": "Exploration changes the action distribution to gather information. The tradeoff is between learning value and the cost or risk of trying uncertain actions.",
    },
    "model-based-rl": {
        "run": "A real robot should not need to crash into a shelf a thousand times to learn that shelves are hard. Model-based RL learns or uses a model, rehearses possible futures inside it, and spends real trials on the choices that look most informative or promising.",
        "math": "The learned model predicts next states or rollout outcomes. Planning through that model reduces real trial count, but model errors can create plans that work only inside the model.",
    },
}


def concept_run(concept: dict[str, Any]) -> dict[str, str]:
    return CONCEPT_RUNS[concept["id"]]


FAMILY_DEEPENING: dict[str, dict[str, str]] = {
    "problem-setup": {
        "pressure": "This family exists because a moving system does not obey wishes. A planner must name what is known, what can be changed, how the world moves, what future is preferred, and which lines cannot be crossed.",
        "operation": "Turn a story into state, action, dynamics, cost, horizon, constraints, and feasibility before choosing any solver.",
        "worked": "For a drone delivery task, 'get there fast' becomes position, velocity, attitude, battery, payload, wind, rotor thrust, no-fly zones, landing pad error, and safe touchdown speed.",
        "wrong_turn": "Choosing a solver before naming these pieces turns a control problem into a guess about tools.",
        "boundary": "The setup is only as good as the state, action set, dynamics, objective, and constraints that were actually written.",
    },
    "optimization-foundations": {
        "pressure": "Before control chooses a path, ordinary optimization teaches what it means for a choice to be locally better, blocked by a constraint, or stuck at a boundary.",
        "operation": "Look at small changes in the decision and ask whether the objective can still be lowered without leaving the legal set.",
        "worked": "A thermostat setting may lower temperature error but hit a power limit. The gradient points toward a better setting; the constraint says whether that setting is legal.",
        "wrong_turn": "Treating a stationary point as a final answer hides boundaries, constraints, and local traps.",
        "boundary": "This family explains one decision snapshot; control still has to carry state through time.",
    },
    "trajectory-optimization": {
        "pressure": "A path is not a drawing between start and finish. Every point along it must be reachable from the previous point using real commands.",
        "operation": "Make the whole path the decision, enforce dynamics along the path, and ask the solver for a legal low-cost history.",
        "worked": "A robot arm moving around a fixture needs joint angles, velocities, and torques at many times, not just a start pose and an end pose.",
        "wrong_turn": "Checking only endpoints can hide collision, torque spikes, or fast motion between the checked points.",
        "boundary": "The path result depends on model accuracy, grid resolution, constraint fidelity, and whether the solver found a good local candidate.",
    },
    "dynamic-programming": {
        "pressure": "Some problems are too large if the controller lists every future action sequence. The repeated structure is that after one action, the remaining future is another control problem.",
        "operation": "Attach a future-cost number to each state, then compare actions by immediate cost plus the future value of the state they create.",
        "worked": "A rover chooses between a short rocky route and a longer smooth route by pricing wheel damage as a worse future state, not only by counting meters.",
        "wrong_turn": "Comparing immediate cost alone erases the burden carried by the next state.",
        "boundary": "The recursion is truthful only if the state contains the information needed for future consequences.",
    },
    "local-structure": {
        "pressure": "Near a planned motion, the full nonlinear problem may be more detail than the controller needs at every instant.",
        "operation": "Replace the local neighborhood with linear dynamics and quadratic cost, compute fast feedback, and use it only while the state stays near that neighborhood.",
        "worked": "A drone hovering near level can push back against a small drift with LQR; after impact, the same approximation is no longer a truthful picture.",
        "wrong_turn": "Using local feedback after the system leaves the local region treats a false approximation as the real machine.",
        "boundary": "The family stops at large deviations, contact changes, saturation, and model regions where linear/quadratic structure no longer describes the behavior.",
    },
    "safety-and-feasibility": {
        "pressure": "A plan can look good and still put the system into a state where no safe future remains.",
        "operation": "Track sets of states that can reach a target, avoid danger, or remain feasible after the next action.",
        "worked": "A car entering a narrow gap should ask whether braking or steering remains possible one second later, not only whether the next two seconds are collision-free.",
        "wrong_turn": "Treating safety as a soft preference can allow a cheap plan that crosses a hard boundary.",
        "boundary": "The set calculation depends on the modeled controls, disturbances, target sets, and time horizon.",
    },
    "replanning": {
        "pressure": "A long open-loop plan goes stale as soon as wind, traffic, contact, or estimation error changes the state.",
        "operation": "Solve a short future problem, apply the first command, measure again, and solve from the new state while protecting the next solve.",
        "worked": "An autonomous car replans after each small movement because nearby cars move and the measured state is more trustworthy than yesterday's prediction.",
        "wrong_turn": "Believing every feasible short-horizon solve is safe misses the state handed to the next solve.",
        "boundary": "Replanning needs terminal structure, backup policy, reachable set, or another guard when short horizons hide delayed danger.",
    },
    "learning-based-control": {
        "pressure": "Sometimes the model, reward, or expert behavior is too hard to write down cleanly, but data can show part of the missing structure.",
        "operation": "Fit a policy, value, reward, or model from demonstrations or experience, then keep asking what state distribution, reward, and safety boundary the learner is actually using.",
        "worked": "A warehouse robot can clone a human drawer-opening motion, then use reward or a learned model to improve, while checking that mistakes do not move it outside the demonstrated states.",
        "wrong_turn": "Treating data as a replacement for control thinking hides distribution shift, reward loopholes, unsafe exploration, and learned-model error.",
        "boundary": "Learning is only credible where the data, reward, model, and deployment state distribution cover the behavior being asked of the controller.",
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


PRIMITIVE_TESTS: dict[str, dict[str, str]] = {
    "state": {
        "question": "What must be remembered right now so the next command can be predicted?",
        "run": "Two cars share the same lane position. One is centered and steady; the other is sliding with a fast rear car closing. A position-only state would tell both cars to do the same thing, which is physically wrong.",
        "failure": "Missing state turns different futures into the same record, so the controller acts blind.",
    },
    "action": {
        "question": "What command can the machine actually receive?",
        "run": "A drone can want to rise two meters, but the command is rotor thrust or a lower-level velocity target. The height change arrives only after thrust changes acceleration and velocity.",
        "failure": "A fake action asks the plan to choose an outcome the actuator cannot directly produce.",
    },
    "dynamics": {
        "question": "How does the command change the next state?",
        "run": "The same steering command on dry pavement and ice creates different next states. The dynamics are where tire grip, delay, mass, and actuator limits enter the story.",
        "failure": "Wrong dynamics make a future look legal on paper and fail on the real system.",
    },
    "cost": {
        "question": "Which future is the controller being asked to prefer?",
        "run": "A parking controller that prices only time may scrape a wall. Adding distance, steering effort, wall clearance, and final alignment changes what counts as a good future.",
        "failure": "A thin cost makes the controller obey the written scoreboard while violating the human task.",
    },
    "constraint": {
        "question": "What line may not be crossed even if crossing it lowers cost?",
        "run": "A robot arm may save energy by passing through a shelf. Collision is not a tradeoff to be balanced away; it removes that path from the legal set.",
        "failure": "A missing constraint lets the optimizer find a cheap answer that the world will not allow.",
    },
    "value": {
        "question": "What future burden is attached to standing in this state?",
        "run": "A rover one step from sharp rocks should not ask only about the next meter. It should ask what future travel costs after wheel damage.",
        "failure": "Without value, delayed damage, battery drain, and lost options are invisible to the current action.",
    },
    "policy": {
        "question": "What rule chooses the next action from the current information?",
        "run": "A thermostat policy turns temperature into heat on or off. A robot policy turns camera and joint information into a gripper command, then has to handle the next state its own command creates.",
        "failure": "A policy trained only on clean states may fail after its own small mistake creates an unfamiliar state.",
    },
    "uncertainty": {
        "question": "Which part of the next state is not promised?",
        "run": "A rover crossing gravel may move forward, slip left, or slip right. The action must be priced over possible next states, not a single hoped-for outcome.",
        "failure": "Ignoring uncertainty makes a controller trust a future that wind, gravel, sensors, drivers, or model error can break.",
    },
    "feasibility": {
        "question": "Does any legal future remain from this state?",
        "run": "A car too close to a wall at high speed may have no steering or braking command that avoids collision. Before choosing the best plan, the controller must know whether the legal set is empty.",
        "failure": "If feasibility is skipped, the solver can return emergency behavior or no plan after the system is already boxed in.",
    },
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
        "input": "present state and command",
        "output": "next state or state derivative",
        "wrong_read": "Reading f as a label instead of the physical rule that turns commands into motion.",
    },
    {
        "name": "Objective",
        "shape": "total cost = path costs + terminal cost",
        "problem": "A future is not good just because it reaches the goal. It may use too much fuel, hit a wall, arrive late, or end with unsafe speed.",
        "object": "The object is a cost functional: a rule for scoring a whole history.",
        "operation": "Add the cost paid along the path and the cost left at the end.",
        "worked": "A rocket landing score can add fuel burn every second, then add a large final penalty for height error and touchdown speed.",
        "failure": "If the written cost omits damage or risk, the optimizer can choose a future that is cheap on paper and bad in the world.",
        "input": "a candidate state-action history",
        "output": "one score for comparing that history with another",
        "wrong_read": "Treating the cost as intention instead of the written scoreboard the optimizer will obey.",
    },
    {
        "name": "Bellman Recursion",
        "shape": "V(x) = best action of cost now + value next",
        "problem": "The controller needs to judge a current action by the future state it creates, without listing every complete future.",
        "object": "The object is a value function: future cost stored at each state.",
        "operation": "For each action, add immediate cost to the value of the next state, then choose the best sum.",
        "worked": "A rover may pay one extra minute to avoid sharp rocks because the next state after the rocky shortcut has damaged wheels and worse future value.",
        "failure": "If the state is missing hidden information, the value table attaches the wrong future price to that state.",
        "input": "current state, candidate action, one-step cost, and next-state value",
        "output": "the best future cost attached to the current state",
        "wrong_read": "Reading the recursion as algebra only, without asking what next state each action creates.",
    },
    {
        "name": "Hamiltonian",
        "shape": "H = stage cost + costate times dynamics",
        "problem": "A small action change affects cost now and also pushes the whole future state history.",
        "object": "The object is a local package that combines immediate cost with a backward price on state motion.",
        "operation": "Price a control change by adding what it costs now to what its state change costs later.",
        "worked": "For a rocket, more thrust burns fuel now but changes future velocity. The costate says how valuable that velocity change is later near touchdown.",
        "failure": "Hamiltonian conditions are necessary conditions; they can identify a candidate path without proving it is the best global path.",
        "input": "state, control, current cost, dynamics, and costate price",
        "output": "a local stationarity test for a candidate optimal control",
        "wrong_read": "Treating the Hamiltonian as energy here instead of a cost-and-dynamics bookkeeping device.",
    },
    {
        "name": "MPC",
        "shape": "solve horizon, apply first action, measure, repeat",
        "problem": "A long plan becomes stale after the first gust of wind, moving car, or bad state estimate.",
        "object": "The object is a finite-horizon problem rebuilt from the current measured state.",
        "operation": "Solve, use only the first command, shift the horizon, and solve again.",
        "worked": "A car plans five seconds ahead but executes only 0.1 seconds of steering and throttle before traffic is measured again.",
        "failure": "A short horizon without terminal protection can make a legal first move that leaves no legal move next time.",
        "input": "measured state, model, horizon, cost, and constraints",
        "output": "the first command of a newly solved short plan",
        "wrong_read": "Thinking MPC trusts the whole plan instead of deliberately throwing most of it away after measuring again.",
    },
    {
        "name": "Policy Gradient",
        "shape": "move policy parameters toward higher return",
        "problem": "Sometimes the learner has no clean model or action labels, only rollouts and delayed reward.",
        "object": "The object is a parameterized policy that chooses actions from observations or states.",
        "operation": "Use rollout returns to nudge the policy toward actions that led to higher long-run reward.",
        "worked": "A grasping robot tries many wrist angles; successful lifts increase the probability of similar actions in similar poses.",
        "failure": "Sparse reward, unsafe exploration, or random lucky rollouts can push the policy in the wrong direction.",
        "input": "rollouts, rewards, and current policy parameters",
        "output": "a parameter update direction for the policy",
        "wrong_read": "Treating a successful rollout as proof every action in it deserves credit.",
    },
]


CONCEPT_OVERVIEW_FAMILIES: list[dict[str, str]] = [
    {
        "family": "Problem setup",
        "pressure": "The learner must first stop saying what they want and start naming what the machine can actually know and command.",
        "ordinary_run": "For a drone landing on a pad, state is height, velocity, attitude, battery, payload, and wind estimate; action is thrust or a lower-level motion command; dynamics say how thrust changes motion; cost prices time, energy, landing error, and smoothness; constraints forbid no-fly zones, empty battery, and hard touchdown.",
        "failure_test": "If two physically different situations get the same state, or if the action asks for an outcome instead of a command, the setup is lying before any solver runs.",
    },
    {
        "family": "Trajectory optimization",
        "pressure": "A path is a history, not a line drawn between start and finish. Every piece of that history must be reachable from the previous piece.",
        "ordinary_run": "For a robot arm near a shelf, a short geometric path can pass through a joint state that needs torque above the motor limit. Direct transcription and collocation make the hidden middle of the path visible to the solver.",
        "failure_test": "If the grid is too coarse, a solution can satisfy every written dot while hiding a collision, torque spike, or fast unstable motion between dots.",
    },
    {
        "family": "Dynamic programming",
        "pressure": "The next action matters because it creates the state from which all later actions must be chosen.",
        "ordinary_run": "For a rover choosing between a rocky shortcut and a longer smooth route, Bellman reasoning compares distance now plus the future cost of damaged wheels, not distance alone.",
        "failure_test": "If the state does not include wheel health, battery, or another delayed burden, the value function stores the wrong price for the future.",
    },
    {
        "family": "Local structure",
        "pressure": "Sometimes the full nonlinear problem is too much, but the system is close enough to a planned motion for a local picture to tell the truth.",
        "ordinary_run": "For a hovering drone pushed a few centimeters sideways, linearized dynamics and a quadratic bowl around the target can produce a fast feedback correction.",
        "failure_test": "After impact, contact, actuator saturation, or tumbling, the local picture no longer describes the machine the controller is actually moving.",
    },
    {
        "family": "Safety and replanning",
        "pressure": "A plan can be legal for the next few seconds and still hand the controller a state with no legal future.",
        "ordinary_run": "For a car entering a narrow traffic gap, MPC may find a collision-free two-second path, but recursive feasibility asks whether braking or steering remains possible after the first command.",
        "failure_test": "If today's first action makes tomorrow's optimization infeasible, the controller was not planning safely even though the current solve looked clean.",
    },
    {
        "family": "Learning-based control",
        "pressure": "Data enters when the model, reward, contact strategy, or expert behavior cannot be fully written by hand.",
        "ordinary_run": "For a warehouse robot, demonstrations can teach a drawer-pulling motion, reward can improve repeated attempts, and a learned model can rehearse shelf contacts before hardware trials.",
        "failure_test": "If the learned policy visits states outside the demonstrations, or if the reward omits damage and force, more training can make the wrong behavior more reliable.",
    },
]


REVIEW_WALKTHROUGH: list[dict[str, str]] = [
    {
        "title": "Setup Page Test",
        "sample": "Open State, Action / Control Input, Dynamics, Objective / Cost Function, and Constraints.",
        "pass": "A passing page lets the reviewer rebuild a drone, car, or robot setup before any formal label appears. It says what the controller knows, what command it can issue, how the world changes, what future is preferred, and what is forbidden.",
        "reject": "Reject a page that only defines the term or says the idea matters. The page must show a real command moving a real state and name the visible failure caused by a missing variable, impossible action, wrong model, weak cost, or soft constraint.",
    },
    {
        "title": "Path Page Test",
        "sample": "Open Trajectory Optimization, Direct Transcription, Shooting Methods, and Collocation.",
        "pass": "A passing page makes clear that the answer is a whole history of states and actions. It should show why a smooth-looking path can still be illegal because dynamics, torque, collision, or grid spacing expose a hidden middle.",
        "reject": "Reject a page that treats the method as a solver choice without saying what variables are created, what defects are enforced, what simulation is run, or what can be missed between grid points.",
    },
    {
        "title": "Future-Price Page Test",
        "sample": "Open Value Function, Bellman Recursion, Dynamic Programming, and Stochastic Dynamic Programming.",
        "pass": "A passing page makes future consequence feel like an object attached to the current state. A rover, option, battery, or wheel-damage example should show why the next action is judged by the state it creates.",
        "reject": "Reject a page that only writes the recursion. It must explain what the value stores, why the state must contain delayed burdens, and how uncertainty changes one promised next state into an average over possible next states.",
    },
    {
        "title": "Replanning Safety Test",
        "sample": "Open Model Predictive Control, Recursive Feasibility, Reachability, and Stability Under Replanning.",
        "pass": "A passing page distinguishes a legal short plan from a safe handoff to the next solve. It should show a car, drone, or warehouse robot taking one command and then asking whether the next state still has a legal future.",
        "reject": "Reject a page that praises replanning without naming the first action, the measured next state, the terminal protection, the safe set, or the failure where tomorrow's optimization has no escape.",
    },
    {
        "title": "Learning Page Test",
        "sample": "Open Imitation Learning, Behavioral Cloning, Distribution Shift, Reward, Reinforcement Learning, Policy Optimization, Exploration, and Model-Based RL.",
        "pass": "A passing page keeps control thinking alive after data appears. It names the state distribution, reward loophole, exploration risk, learned-model error, and closed-loop states created by the learner's own actions.",
        "reject": "Reject a page that treats learning as magic performance gain. The page must say what signal is learned from, what the learner can exploit, and what hardware or task failure appears when the signal is incomplete.",
    },
]


QUALITY_TESTS: list[dict[str, str]] = [
    {
        "title": "Start With A Machine, Not A Term",
        "weak": "State is a vector used by the controller.",
        "strong": "A car at the same lane position can need different steering if one version is sliding and the other is moving straight. State is the record that preserves that difference before the controller chooses.",
        "test": "The sentence passes only if a reader can picture the thing being moved and say why the formal object must exist.",
    },
    {
        "title": "Name The Command The World Receives",
        "weak": "The action changes the system.",
        "strong": "A drone cannot command height directly. It commands thrust; thrust changes acceleration, acceleration changes velocity, and velocity changes height.",
        "test": "The sentence passes only if it separates the desired outcome from the command the actuator or policy can issue.",
    },
    {
        "title": "Turn Math Into An Operation",
        "weak": "The Bellman equation relates current and future value.",
        "strong": "For each rover move, add the cost of that move to the stored future cost of the state it creates, then choose the smallest total.",
        "test": "The sentence passes only if the reader can perform the operation on a small example before reading symbols.",
    },
    {
        "title": "Make Failure Visible",
        "weak": "MPC requires care with feasibility.",
        "strong": "A car can fit through a gap for two seconds and still be in trouble if the first acceleration leaves no legal braking or steering move for the next solve.",
        "test": "The sentence passes only if it shows the concrete bad state that appears when the assumption is missing.",
    },
    {
        "title": "Keep Learning Inside Control",
        "weak": "Behavioral cloning learns from demonstrations.",
        "strong": "A cloned gripper policy trains on expert states. If its own small mistake nudges the object eight centimeters sideways, the policy may now face a state the expert data never labeled.",
        "test": "The sentence passes only if it names the data source, the closed-loop state the learner creates, and the failure caused by the gap.",
    },
    {
        "title": "Tie Evidence To The Exact Claim",
        "weak": "The lecture discusses reachability.",
        "strong": "The transcript window names reachable sets and targets; the page adds the learner rule that safety is a question about which states can still avoid a bad target under allowed controls and disturbances.",
        "test": "The sentence passes only if it separates what the transcript says from what the course page adds as explanation.",
    },
    {
        "title": "Use Numbers When They Expose The Tradeoff",
        "weak": "The rocket must balance fuel and landing speed.",
        "strong": "At 80 meters and -18 m/s, a hard one-second burn may leave -12 m/s for the next state, while a weak burn may leave -20 m/s and make the last 30 meters unrecoverable under thrust limits.",
        "test": "The sentence passes only if the numbers change the decision pressure, not if they decorate a claim already made in words.",
    },
    {
        "title": "Say Where The Method Stops",
        "weak": "LQR works near a nominal point.",
        "strong": "LQR can correct a two-centimeter hover drift because the local dynamics and cost still look like the planned model. After a branch strike, tumbling and actuator saturation put the drone outside that local picture.",
        "test": "The sentence passes only if it gives both the inside case and the outside case, so the learner can see the boundary.",
    },
]


PROVENANCE_CHECKS: list[tuple[str, str]] = [
    (
        "Source Capture",
        "Start with the playlist record, then inspect the raw VTT and cleaned transcript for the lecture. The raw file keeps timestamped caption evidence; the clean file makes the words searchable. If either layer is missing, a concept page should not pretend to have local transcript support.",
    ),
    (
        "Evidence Record",
        "Open the matching row in analysis/evidence/evidence-ledger.json. A trustworthy record names the video id, timestamp, local transcript path, transcript window, what the transcript supports, and what the page adds beyond the transcript.",
    ),
    (
        "Teaching Synthesis",
        "Open the concept or teaching artifact that uses the record. The page may explain more than the transcript says, but it must keep the boundary visible. The transcript can support that Lecture 11 discusses reachable sets; the page can then synthesize the learner rule about safe states and bad targets.",
    ),
    (
        "Generated Page",
        "Open the rendered HTML after rebuilding. The page should contain the same evidence anchor and the same first-principles structure: ordinary pressure, object, operation, concrete run, math one level deeper, and boundary.",
    ),
    (
        "Validation Gate",
        "Run the validator after rendering. The validator checks links, evidence anchors, transcript coverage, required teaching markers, word floors, broad anti-filler phrases, and concept-page richness markers.",
    ),
    (
        "Manual Review Override",
        "Some evidence rows need human wording after the automatic transcript match. Those overrides live in analysis/evidence/manual-review-overrides.json. They should make the transcript support sharper, not inflate it into a claim the lecture did not make.",
    ),
    (
        "Durable Edit Rule",
        "If a reviewer wants a richer explanation, the edit belongs in scripts/build_site.py, scripts/build_first_principles_atlas.py, scripts/build_teaching_artifacts.py, or the analysis source files that feed them. Editing only the rendered HTML creates a stale page that the next build will overwrite.",
    ),
    (
        "Cold Rebuild Rule",
        "A clean rebuild is the proof that the course is reproducible. Delete nothing by hand; run the generator chain and validator. If the same 57 pages, 38 concepts, 38 evidence records, and teaching artifacts reappear, the source layer and rendered layer still agree.",
    ),
]


COMPLETION_REQUIREMENTS: list[tuple[str, str, str]] = [
    (
        "Playlist Source Coverage",
        "19/19 lectures have local transcript records and the transcript index reports 207,618 words.",
        "This proves source availability, not teaching quality. A reviewer still has to inspect whether the page uses the transcript honestly.",
    ),
    (
        "Concept Coverage",
        "38 concept pages are generated from the atlas, and each concept page must include ordinary pressure, object, concrete run, math one level deeper, boundary, and transcript evidence markers.",
        "This proves every named concept has the required structure. It does not prove every paragraph has reached the richest possible explanation.",
    ),
    (
        "Evidence Coverage",
        "38 evidence records are rendered with anchors, transcript windows, support statements, and synthesis boundaries; manual review remaining is zero in the audit artifact.",
        "This proves every concept can be traced to a local evidence record. It does not mean the transcript alone proves every teaching sentence.",
    ),
    (
        "Teaching Artifacts",
        "Derivations, worked examples, drills, solutions, and weak-claim repairs are generated from source artifacts and validated for concrete runs, transfer checks, setup hints, grading criteria, and replacement rules.",
        "This proves the practice layer exists and has required fields. A reviewer should still solve at least two drills to test whether the solution reasoning feels transferable.",
    ),
    (
        "Editorial Gates",
        "The validator enforces page markers, concept word floors, top-level word floors, broad anti-filler phrases, evidence anchors, local links, and generated site coherence.",
        "This proves a baseline bar. It cannot replace reading the site against the reference explainers for rhythm, depth, and plain everyday language.",
    ),
]


COMPLETION_SAMPLE_CHECKS: list[tuple[str, str]] = [
    (
        "State And Action",
        "Open state.html and action-control-input.html. The reviewer should be able to say why lane position is not enough for a car and why a drone commands thrust rather than height. If either page starts and ends as a definition, the setup layer is not complete.",
    ),
    (
        "Bellman And Value",
        "Open bellman-recursion.html and value-function.html. The reviewer should see the rover-style future-price idea before symbols: pay now, enter a new state, inherit the future burden from that state.",
    ),
    (
        "MPC And Reachability",
        "Open model-predictive-control.html and reachability.html. The reviewer should see the difference between a short legal plan and a state set that protects future safety under controls and disturbances.",
    ),
    (
        "Learning Boundary",
        "Open behavioral-cloning.html and reward.html. The reviewer should see the exact closed-loop risk: a learned policy visits states outside the data, or a reward omits damage and teaches the wrong behavior.",
    ),
    (
        "Practice Transfer",
        "Open drills.html and solutions.html. The reviewer should be able to change drone delivery to indoor delivery, or traffic MPC to a narrow drone window, and still use the same reasoning.",
    ),
]


LECTURE_DEEPENING: dict[int, dict[str, str]] = {
    1: {
        "problem": "The course first has to make control visible in ordinary systems: a car, drone, thermostat, or robot changes because commands push state through time.",
        "move": "Name the basic pieces before choosing methods: state, action, dynamics, objective, horizon, and constraints.",
        "run": "A drone delivery problem becomes concrete only after height, velocity, attitude, battery, thrust, wind, landing error, and no-fly zones are named.",
    },
    2: {
        "problem": "Before a controller can choose a path, it needs the grammar of a single constrained decision: what can move, what is legal, and what local change lowers cost.",
        "move": "Use finite-dimensional optimization, gradients, open sets, and constraints as the small-scale version of later control problems.",
        "run": "A heater setting that lowers temperature error may violate a power limit; the gradient points downhill, but the constraint says whether that move is allowed.",
    },
    3: {
        "problem": "A path cannot be judged by one point. The whole curve has cost, endpoints, and legal motion along the way.",
        "move": "Shift from choosing numbers to choosing functions or trajectories, then ask how total cost changes when the whole path is nudged.",
        "run": "A rocket arc that starts and ends correctly can still waste fuel in the middle; calculus of variations asks what path-wide nudge would lower the total cost.",
    },
    4: {
        "problem": "A small state error now can change fuel, velocity, and endpoint error later, so present controls need a price for downstream state changes.",
        "move": "Introduce costates and the Hamiltonian as local bookkeeping for immediate cost plus future state sensitivity.",
        "run": "More rocket thrust costs fuel now, but it may reduce a costly terminal velocity error. The costate prices that later benefit.",
    },
    5: {
        "problem": "Necessary equations are not enough if the actual path still has to be computed on a machine.",
        "move": "Connect optimality conditions to computational methods and the practical burden of solving trajectory problems.",
        "run": "A boundary-value condition may describe the landing path, but a solver still needs variables, guesses, tolerances, and checks that the result obeys the dynamics.",
    },
    6: {
        "problem": "A computer cannot optimize over every point of a continuous path directly.",
        "move": "Use direct methods: shooting, collocation, and transcription turn a path problem into finite variables and constraints.",
        "run": "A robot arm path becomes joint states and torques on a grid; defect constraints stop the optimizer from inventing motion between grid points.",
    },
    7: {
        "problem": "Listing every future action sequence becomes impossible when every action creates a new state with later choices.",
        "move": "Use dynamic programming: store future cost at states and solve the problem by now-plus-future recursion.",
        "run": "A rover cell near sharp rocks gets a high future price because entering it damages later mobility, even if the next step is short.",
    },
    8: {
        "problem": "A full nonlinear solve is too much for small deviations near a planned motion.",
        "move": "Exploit linear dynamics and quadratic cost so local feedback can be computed from value curvature.",
        "run": "A hovering drone pushed two centimeters sideways can use a local feedback gain instead of replanning the whole flight.",
    },
    9: {
        "problem": "The next state may be a distribution, not a promise, when wind, gravel, or sensor noise changes the outcome.",
        "move": "Extend dynamic programming so future value is averaged over possible next states.",
        "run": "A rover crossing gravel prices a move by the chance of slipping left, slipping right, or moving as intended.",
    },
    10: {
        "problem": "A controller needs to know which states can still reach a target or avoid danger before optimizing a preferred path.",
        "move": "Use reachability to reason about sets of states under controls, disturbances, and targets.",
        "run": "A car near a wall may look safe by distance, but reachability asks whether any legal steering and braking sequence can still avoid collision.",
    },
    11: {
        "problem": "A plan made at the old state goes stale as soon as the world moves or the model is wrong.",
        "move": "Introduce MPC: solve a finite-horizon problem, apply the first action, observe, and solve again.",
        "run": "A car plans five seconds of steering but executes only a small slice before measuring traffic again.",
    },
    12: {
        "problem": "Repeated planning can make legal moves that leave the next optimization with no legal solution.",
        "move": "Study feasibility, recursive feasibility, and stability conditions for MPC.",
        "run": "A car entering a narrow gap may be collision-free now but have no braking option one second later; recursive feasibility rejects that handoff.",
    },
    13: {
        "problem": "Learning enters only after the course has named what written models and objectives can and cannot supply.",
        "move": "Bridge model-based control to data-driven control: what can be learned, from what signal, and with what new failure modes.",
        "run": "A robot may know its arm physics but not the right contact strategy for a drawer handle; demonstrations or reward can fill that missing piece.",
    },
    14: {
        "problem": "Imitation and reinforcement learning answer different missing-information problems.",
        "move": "Separate learning from demonstrations from learning through reward and interaction.",
        "run": "If an expert can show good grasps, imitation is natural; if success can only be scored after trial, reinforcement learning becomes the tool.",
    },
    15: {
        "problem": "Copying expert actions is not the same as building a controller that recovers after its own small mistakes.",
        "move": "Study imitation learning and behavioral cloning as supervised policy learning with distribution-shift risk.",
        "run": "A cloned driving policy trained near lane center may drift right, then face states the expert almost never visited.",
    },
    16: {
        "problem": "A reward signal can teach behavior without action labels, but delayed credit and unsafe exploration make the learning problem hard.",
        "move": "Introduce reinforcement learning through policy, reward, return, exploration, and objective learning.",
        "run": "A grasp that succeeds after a wrist correction must credit earlier actions, not only the final lift.",
    },
    17: {
        "problem": "The learner may not know the best action, but it can learn which states or state-action pairs lead to better future return.",
        "move": "Use value-based RL to learn future-return estimates from sampled transitions.",
        "run": "A game agent chooses a move by comparing the learned values of the board positions those moves create.",
    },
    18: {
        "problem": "Large continuous action policies may be easier to improve directly than through a table of values.",
        "move": "Use policy optimization to update the action rule from rollout returns.",
        "run": "A walking robot changes neural policy weights so steps that led to longer stable walking become more likely.",
    },
    19: {
        "problem": "Real trial-and-error is expensive when hardware can break or data collection is slow.",
        "move": "Use model-based RL to learn or use a predictive model, rehearse futures, and spend real trials carefully.",
        "run": "A warehouse robot can test shelf-collision futures inside a learned model before risking the real arm.",
    },
}


LECTURE_BLOCKS: list[dict[str, str]] = [
    {
        "title": "Lectures 1-2: Make Control Speak Plainly",
        "extract": "The learner should leave with the grammar of a control problem: state, action, dynamics, cost, horizon, constraints, feasibility, and local improvement.",
        "wrong_turn": "Do not treat these lectures as preliminaries to skip. If the setup is vague, every later solver and learner will solve the wrong problem.",
        "run": "A drone delivery story becomes real only when position, velocity, attitude, battery, wind, thrust, no-fly zones, and touchdown speed are named.",
    },
    {
        "title": "Lectures 3-6: Turn A Path Into Something A Computer Can Check",
        "extract": "The learner should see why a trajectory is the decision: calculus of variations, costates, Hamiltonians, shooting, transcription, and collocation all ask how a whole path obeys dynamics and cost.",
        "wrong_turn": "Do not read these as solver trivia. The danger is a path that looks smooth but hides endpoint error, torque spikes, missed collisions, or dynamics defects.",
        "run": "A robot arm going around a fixture needs states and torques along the path, not only a start pose and an end pose.",
    },
    {
        "title": "Lectures 7-10: Price The Future From The State",
        "extract": "The learner should understand value as stored future burden. Dynamic programming, stochastic outcomes, LQR, and reachability all depend on what the current state says about possible futures.",
        "wrong_turn": "Do not reduce Bellman reasoning to a formula. The real move is judging today's action by the state it creates.",
        "run": "A rover may avoid a short rocky path because wheel damage makes every later move worse.",
    },
    {
        "title": "Lectures 11-12: Replan Without Destroying Tomorrow",
        "extract": "The learner should distinguish a feasible short plan from a safe repeated controller. MPC, recursive feasibility, stability, and reachability ask what state is handed to the next solve.",
        "wrong_turn": "Do not trust the current optimization just because it found a legal two-second path.",
        "run": "A car can fit into a traffic gap now and still leave no legal braking future after the first acceleration.",
    },
    {
        "title": "Lectures 13-19: Learn Missing Structure Without Forgetting Control",
        "extract": "The learner should see learning as filling missing policy, reward, value, or model structure while keeping state distribution, reward loopholes, exploration risk, and model error visible.",
        "wrong_turn": "Do not treat data as a magic replacement for state, action, dynamics, cost, constraints, and safety boundaries.",
        "run": "A warehouse robot can clone drawer-opening demonstrations, but its own small error may put the handle pose outside the demonstrated states.",
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
    missing_concept_runs = [concept["id"] for concept in concepts if concept["id"] not in CONCEPT_RUNS]
    if missing_concept_runs:
        raise SystemExit(f"missing first-principles concept runs: {', '.join(missing_concept_runs)}")
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
  <div class="explain-box">
    <p>Start with a car entering traffic. The driver wants the next lane, but the controller cannot command "be in that lane." It can command steering, braking, and acceleration. Those commands move the state through tire forces, speed, heading, and the motion of nearby cars. A one-second action can create a future where braking is still possible, or a future where no legal move remains.</p>
    <p>That small scene is the whole course in miniature: name the state, name the action, write how the world moves, score the future, forbid unsafe states, choose a path, price delayed consequences, replan from new measurements, and learn missing structure only when data is the honest source.</p>
  </div>
  {stats}
</section>
<h2>Strongest Entry Points</h2>
<section class="grid">{entries}</section>
<h2>How To Read This Site</h2>
<div class="essay">
  <p>Start with a simple physical question: what can the system do now, and what future will that action create? Every page comes back to that question. State says what the controller must know. Action says what can actually be commanded. Dynamics say how the command changes the world. Cost says which future is preferred. Constraints say what future is illegal.</p>
  <p>The course then changes tools only when the pressure changes. Direct methods appear when the whole path must be chosen. Dynamic programming appears when future consequence can be stored by state. LQR appears when the world is close enough to a local model. MPC appears when a plan must be rebuilt from fresh measurements. Learning appears when the model, reward, or expert behavior cannot be fully written by hand.</p>
  <p>The evidence links keep the transcript layer honest. The teaching prose goes beyond the transcript, but each evidence record says what the lecture actually supports and where the site is synthesizing.</p>
</div>
<h2>The Route Through The Material</h2>
<section class="stack">
  <article class="card"><h3>1. Make The Problem Physical</h3><p>A controller starts with a moving thing: drone, car, rocket, robot arm, rover, policy, or learned model. The first job is to stop speaking in wishes and name the present-tense record, the command, the transition rule, the score, and the forbidden states.</p></article>
  <article class="card"><h3>2. Choose A Whole Future</h3><p>Trajectory optimization appears when one command is not enough. A landing rocket or robot arm needs a history of states and actions. The path has to obey dynamics at every step, not only look good at the endpoints.</p></article>
  <article class="card"><h3>3. Store Future Burden</h3><p>Dynamic programming appears when the same question repeats after every action. A rover that damages a wheel has changed the future problem. Value stores that future burden at the state so today's action can be judged honestly.</p></article>
  <article class="card"><h3>4. Replan Without Losing Safety</h3><p>MPC plans a short future, applies one action, and measures again. The hard test is the handoff: after that first action, does the next state still have a legal future? Reachability and recursive feasibility make that question explicit.</p></article>
  <article class="card"><h3>5. Learn Where Writing Runs Out</h3><p>Learning-based control enters when demonstrations, rewards, rollouts, or learned models carry structure the designer cannot write cleanly. The control questions remain: what states does the learner visit, what signal is being followed, and what failure can the signal hide?</p></article>
</section>
<h2>What This Site Is Not</h2>
<div class="essay">
  <p>It is not a transcript dump. The transcripts are the source floor, not the finished teaching. It is not a glossary. A definition is only acceptable when it is tied to a machine, an operation, and a failure. It is not a set of solver recommendations. Every method is introduced because some ordinary pressure made the previous framing break.</p>
  <p>The intended reading standard is simple: after a page, you should be able to retell the idea with a new car, drone, robot, rover, or learning setup without hiding behind the course vocabulary.</p>
</div>
<h2>First Read Path</h2>
<div class="essay">
  <p>Read <a href="course-spine.html">Course Spine</a> first if you want the whole argument in order. Then open <a href="concepts/state.html">State</a>, <a href="concepts/dynamics.html">Dynamics</a>, and <a href="concepts/objective-cost-function.html">Objective / Cost Function</a> to see how a story becomes a control problem. Next read <a href="concepts/bellman-recursion.html">Bellman Recursion</a> and <a href="concepts/model-predictive-control.html">Model Predictive Control</a> to see how future cost and repeated measurement change the decision. Finish with <a href="concepts/behavioral-cloning.html">Behavioral Cloning</a> and <a href="concepts/reward.html">Reward</a> to see why data does not remove the need for control reasoning.</p>
  <p>After that path, use the drills as a transfer test. If you can move the drone-delivery setup indoors, move the MPC traffic failure to a narrow drone window, and spot the reward loophole in a new robot task, the site is doing more than naming concepts.</p>
</div>
<h2>Current Build State</h2>
<p>The current build has full transcript coverage, a complete minimum concept atlas, timestamped evidence records with manual deepening, and expanded teaching artifacts for derivations, examples, drills, solutions, and weak-claim repairs.</p>
""",
            "overview",
        ),
    )

    lecture_rows = []
    for video in manifest["videos"]:
        rec = by_video.get(video["id"], {})
        deep = LECTURE_DEEPENING.get(video["lecture"])
        available = bool(rec.get("transcript_available"))
        label = "transcript captured" if available else "missing transcript"
        lecture_concepts = [c for c in concepts if c.get("lecture") == video["lecture"]]
        links = " ".join(f'<span class="pill">{concept_link(c)}</span>' for c in lecture_concepts[:6])
        if len(lecture_concepts) > 6:
            links += f' <span class="muted">+{len(lecture_concepts)-6} more</span>'
        if not deep:
            raise SystemExit(f"missing lecture deepening: lecture {video['lecture']}")
        lecture_rows.append(
            f"""<div class="lecture-row">
  <strong>Lecture {video['lecture']:02d}</strong>
  <div>
    <h3>{esc(video['title'])}</h3>
    <p class="muted">{esc(label)} · {rec.get('word_count', 0):,} words · <a href="https://www.youtube.com/watch?v={esc(video['id'])}">{esc(video['id'])}</a></p>
    <p><strong>The problem:</strong> {esc(deep['problem'])}</p>
    <p><strong>The move:</strong> {esc(deep['move'])}</p>
    <div class="explain-box"><p>{esc(deep['run'])}</p></div>
    <p>{links or '<span class="muted">No primary concept assigned yet.</span>'}</p>
  </div>
  <span class="tag">{'ready' if available else 'gap'}</span>
</div>"""
        )
    lecture_intro = """
<h1>Lectures</h1>
<p class="lede">Read the playlist as one route through a problem, not as nineteen isolated videos. Each lecture adds one pressure: name the moving system, choose a path, price the future, replan safely, or learn the missing structure from data.</p>
<div class="essay">
  <p>The lecture list below keeps transcript counts and source links, but the main job is different: it tells you what new control problem each lecture makes visible and what mathematical move the lecture adds.</p>
  <p>Use the blocks first, then the individual lecture rows. The blocks say what a learner should extract from a cluster of videos. The rows say what each video contributes and which concept pages carry the idea further.</p>
</div>
"""
    lecture_block_cards = "".join(
        card(
            item["title"],
            f"""<p><strong>Extract:</strong> {esc(item['extract'])}</p>
<p><strong>Wrong turn:</strong> {esc(item['wrong_turn'])}</p>
<div class="explain-box"><p>{esc(item['run'])}</p></div>""",
        )
        for item in LECTURE_BLOCKS
    )
    lectures_body = f"""{lecture_intro}
<h2>Lecture Blocks</h2>
<section class="stack">{lecture_block_cards}</section>
<h2>How To Use A Lecture Row</h2>
<div class="essay">
  <p>Read each row in four passes. First, read the problem sentence and ask what pressure entered the course at that point. Second, read the move sentence and identify the mathematical object or method family that answers that pressure. Third, read the concrete run and check whether you can retell it with another machine. Fourth, open the linked concepts and evidence record to separate transcript support from teaching synthesis.</p>
  <p>For example, Lecture 12 should not be remembered as "the MPC lecture after reachability." It should be remembered as the place where repeated planning is tested: today's feasible first command must leave tomorrow's optimization with a legal continuation. Lecture 15 should not be remembered as "imitation learning." It should be remembered as supervised policy learning under a closed-loop distribution problem.</p>
</div>
<h2>Lecture Route Cross-Checks</h2>
<div class="essay">
  <p>Check the route against three other pages. The concept atlas should turn each lecture move into a standalone explanation with ordinary pressure, concrete run, math, evidence, and boundary. The drills should force transfer: a lecture idea should survive a new drone, car, rover, warehouse, or reward setup. The evidence ledger should keep the source trail honest by saying what the transcript directly supports.</p>
  <p>A lecture row fails this cross-check if it only names a topic. "Lecture 7 covers dynamic programming" is not enough. The row must say that dynamic programming stores future cost at states so the controller can judge today's action by the state it creates. "Lecture 19 covers model-based RL" is not enough. The row must say that a learned model lets the robot rehearse futures while model error remains a failure mode.</p>
  <p>The first and last lectures should still feel connected. Lecture 1 asks what state, action, dynamics, cost, and constraints make a control problem. Lecture 19 returns to the same pieces after data enters: the model may be learned, but it still predicts next states for actions inside a control loop under real constraints, hardware limits, and safety checks.</p>
</div>
<h2>Lecture-By-Lecture Route</h2>
<section class="lecture-list">{''.join(lecture_rows)}</section>"""
    write(SITE / "lectures.html", page("Lectures", lectures_body, "lectures"))

    transcript_cards = []
    for video in manifest["videos"]:
        rec = by_video.get(video["id"], {})
        transcript_cards.append(
            card(
                f"Lecture {video['lecture']:02d}: {video['title']}",
                f"<p>{'transcript captured' if rec.get('transcript_available') else 'missing transcript'} · {rec.get('word_count', 0):,} words</p><p><code>{esc(rec.get('clean_text', 'not downloaded'))}</code></p>",
            )
        )
    transcript_intro = f"""
<h1>Transcript Index</h1>
<p class="lede">The transcript layer is the source floor. It keeps the course companion from becoming free-floating explanation.</p>
<div class="essay">
  <p>There are {transcript_index.get('available_transcripts', 0)} local transcripts for {transcript_index.get('videos', 0)} playlist videos, totaling {transcript_index.get('total_transcript_words', 0):,} words. Raw VTT captions stay separate from cleaned text so evidence can be traced back to timestamped source material.</p>
  <p>The site does not treat transcripts as finished teaching. A transcript window can support a claim that a lecture introduced reachability, Bellman recursion, MPC, imitation learning, or policy optimization. The explanation page then has to say what it is synthesizing beyond that window.</p>
  <p>Use this page when auditing source coverage: every lecture should show a captured transcript, a local clean-text path, and a word count large enough to support real review.</p>
  <p>If a lecture has no transcript, no concept page should pretend to quote it or build evidence from memory.</p>
</div>
<h2>How To Use A Transcript</h2>
<div class="essay">
  <p>Start with a narrow claim, not with a whole page. A transcript can prove that a lecture named model predictive control, reachable sets, quadratic cost, behavior cloning, or policy optimization. It can also support the local wording around that concept: for example, whether the lecture connects MPC with feasibility, or whether it frames behavior cloning as supervised learning from demonstrations.</p>
  <p>A transcript cannot by itself prove the whole first-principles synthesis. If a concept page says a car entering a narrow gap may leave no legal braking future, that sentence is teaching synthesis. The transcript may support the course topic of recursive feasibility; the page must still declare the added control interpretation through the evidence record.</p>
  <p>That split is deliberate. The transcript gives the floor; the course page builds the explanation. A reviewer should be able to inspect both layers without guessing which sentence came from source and which sentence came from synthesis.</p>
</div>
<h2>One Transcript Audit Run</h2>
<div class="essay">
  <p>Use Lecture 12 as a model. First open the clean transcript path and search for feasibility or stability. Then open the evidence record for recursive feasibility. The transcript window should show that the lecture discusses persistent feasibility in the MPC pipeline. The evidence record should say what that supports. The concept page can then teach the everyday test: after today's MPC action, does tomorrow's optimization problem still have a legal solution?</p>
  <p>Do the same for a learning concept. A behavior-cloning transcript window can support supervised learning from demonstrated behavior. The page can add the closed-loop warning: if the learned policy drifts into a state outside the demonstrations, action prediction accuracy on the original data is not enough.</p>
</div>
<h2>Transcript Red Flags</h2>
<div class="essay">
  <p>Be suspicious if an evidence record only repeats a keyword, if a concept page quotes no local transcript path, if the raw VTT cannot be traced to a timestamp, or if the explanation claims more certainty than the transcript window supports.</p>
  <p>Also be suspicious of transcript-shaped prose. Captions often contain false starts, repeated phrases, and lecture logistics. A good course page should not merely polish that sequence; it should rebuild the idea in everyday words, then point back to the transcript for source support.</p>
</div>
<h2>What To Record After Review</h2>
<div class="essay">
  <p>After checking a transcript claim, record three things. First, what the transcript directly supports: the lecture names a method, states an assumption, contrasts two families, or gives a formal object. Second, what the page adds: a car example, a drone failure, a reward loophole, or a plain-language operation. Third, whether the boundary is visible: the page should say where the lecture support ends and where synthesis begins.</p>
  <p>This record matters because rich writing can drift. The deeper the explanation gets, the more carefully the evidence trail has to separate source from teaching. The goal is not to make every sentence a quote; the goal is to make every strong teaching sentence auditable.</p>
  <p>A good note is specific: transcript supports quadratic cost terms; page adds the bowl picture and the warning that the approximation only holds near the planned motion. That note is reviewable months later by another course editor during source review work.</p>
</div>
"""
    write(SITE / "transcripts.html", page("Transcripts", f"{transcript_intro}<section class=\"grid\">{''.join(transcript_cards)}</section>", "transcripts"))

    family_sections = []
    for family in families:
        rows = concepts_by_family.get(family["id"].replace("-", " "), []) or [concepts_by_id[cid] for cid in family["concepts"] if cid in concepts_by_id]
        concept_cards = "".join(card(c["name"], f"<p>{esc(c['plain_language_definition'])}</p><p>{concept_link(c)}</p>") for c in rows)
        family_sections.append(f"<h2>{esc(family['name'])}</h2><p>{esc(family['problem'])}</p><section class=\"grid\">{concept_cards}</section>")
    concept_cards = "".join(
        card(c["name"], f"<p>{esc(c['plain_language_definition'])}</p><p><span class=\"tag\">{esc(c['family'])}</span></p><p>{concept_link(c)}</p>")
        for c in concepts
    )
    concept_family_cards = "".join(
        card(
            item["family"],
            f"""<p><strong>Pressure:</strong> {esc(item['pressure'])}</p>
<div class="explain-box"><p>{esc(item['ordinary_run'])}</p></div>
<p><strong>Failure test:</strong> {esc(item['failure_test'])}</p>""",
        )
        for item in CONCEPT_OVERVIEW_FAMILIES
    )
    concept_intro = """
<h1>Concept Atlas</h1>
<p class="lede">The concept atlas is the learner's map from ordinary control pressure to mathematical objects.</p>
<div class="essay">
  <p>Do not read these as vocabulary flashcards. Each concept page has to answer a practical question: what real system is being controlled, what simple approach breaks, what object carries the burden, what operation is performed, and what visible failure appears outside the assumptions.</p>
  <p>The cards below are only doors. The real work is inside each concept page: one concrete run, a math block one level deeper, transcript evidence, and a boundary test.</p>
  <p>A good review path samples one concept from each family before trusting the atlas as complete, balanced, and usable.</p>
</div>
<h2>How To Read A Concept</h2>
<div class="essay">
  <p>Read every concept through the same four-step test. First, name the ordinary pressure: a drone falling, a car merging, a robot arm near a shelf, a rover crossing gravel, or a policy learning from reward. Second, name the burden the concept carries. State carries what must be remembered. Dynamics carry how commands become motion. Value carries future cost. Constraints carry the lines the plan may not cross. Third, name the operation: update, propagate, minimize, price, constrain, replan, sample, or fit. Fourth, name the failure that appears when the assumptions are false.</p>
  <p>For example, a car changing lanes is not only a geometry problem. State must include nearby cars and velocity. Action is steering and acceleration, not the wish to be in the next lane. Dynamics say how quickly the car can move. Cost prices progress and comfort. Constraints protect lane boundaries and collision margins. MPC replans from new measurements, but recursive feasibility asks whether the first command leaves a safe future. Reachability asks which states are already too close to danger under worst-case nearby motion.</p>
  <p>The same reading works for learning. A warehouse robot may clone demonstrations because writing the contact strategy is hard, but cloning only trains on the states in the demonstrations. If the gripper nudges an object eight centimeters sideways, distribution shift has turned the policy into a controller for a state it may never have practiced. Reward can repair part of the behavior, but only if the written reward prices damage, force, smoothness, and safety.</p>
</div>
<h2>Family Pressure Map</h2>
<section class="stack">""" + concept_family_cards + """</section>
<h2>Atlas Doors</h2>
"""
    write(SITE / "concepts.html", page("Concepts", f"{concept_intro}<section class=\"grid\">{concept_cards}</section>", "concepts"))

    for concept in concepts:
        ev_cards = "".join(evidence_card(ev_by_id[eid], depth=1) for eid in concept.get("course_evidence_ids", []) if eid in ev_by_id)
        related = [c for c in concepts if c["family"] == concept["family"] and c["id"] != concept["id"]][:6]
        run = concept_run(concept)
        mathematical_object = sentence_body(concept["mathematical_object"]).lower()
        recognition = recognition_sentence(concept["recognition_test"])
        learning_control_check = ""
        if concept.get("family") == "learning-based control":
            learning_control_check = """
<section class="fp">
  <div class="kick">06 · data inside the loop</div>
  <h2>What the learner changes next</h2>
  <div class="essay">
    <p>Keep the learned piece inside the control loop. The data, reward, value estimate, policy, or learned model does not act in a separate world. It reads a state or observation, helps choose an action, and that action creates the next state the learner must handle.</p>
    <p>Ask three checks before trusting the result. What states did the data actually cover? What behavior does the reward or loss literally pay for? What happens after the learner's own first mistake changes the next input? These checks turn learning back into control instead of letting it become a vague promise that more data will fix the task.</p>
    <p>Use the warehouse drawer case as the common run. A demonstration may show the gripper centered on the handle. A cloned policy can miss by a few centimeters, rotate the handle, and then see a state absent from the demonstrations. A reward may push for quick opening while hiding excessive force. A learned model may rehearse contacts that are slightly wrong. The controller still has to ask what state it visits, what action it issues, and what failure the learned signal can hide.</p>
  </div>
</section>
"""
        body = f"""
<p><a href="../concepts.html">Back to concept atlas</a></p>
<h1>{esc(concept['name'])}</h1>
<p class="lede">{esc(concept['plain_language_definition'])}</p>
<section class="fp">
  <div class="kick">01 · the ordinary pressure</div>
  <h2>Why this idea has to exist</h2>
  <div class="essay">
    <p>{esc(concept['ordinary_problem'])}</p>
    <p>A common wrong first move is: {esc(concept['naive_approach'])} It fails when {esc(concept['why_naive_fails']).lower()}</p>
  </div>
</section>
<section class="fp">
  <div class="kick">02 · the object</div>
  <h2>What the math keeps track of</h2>
  <div class="essay">
    <p>The working object is {esc(mathematical_object)}. {esc(recognition)}.</p>
    <p>What the object does: {esc(concept['operation'])}</p>
  </div>
</section>
<section class="fp">
  <div class="kick">03 · read it with your hands</div>
  <h2>What to inspect first</h2>
  <div class="essay">
    <p>Before naming the method, point to {esc(mathematical_object)} in the setup. Ask what a person could measure, command, update, price, or forbid in one small run.</p>
    <p>Now apply one command or one update. {esc(concept['operation'])} After that operation, ask what changed in the next state, the path, the value, the constraint set, the policy, or the learned model. If nothing concrete changes, the explanation is still only a label.</p>
    <p>The world check is the example: {esc(concept['worked_example'])} Try the same question on another car, drone, rover, robot arm, or reward signal. The concept should still name what changes, what is paid for, and what can fail.</p>
  </div>
</section>
<section class="fp">
  <div class="kick">04 · one concrete run</div>
  <h2>Work it through before naming the formula</h2>
  <div class="explain-box"><p>{esc(run['run'])}</p></div>
  <details class="math"><summary>the actual math, one level deeper</summary><div><p>{esc(run['math'])}</p></div></details>
</section>
<section class="fp">
  <div class="kick">05 · boundary</div>
  <h2>Where the idea stops working</h2>
  <div class="essay">
    <p>{esc(concept['assumption_boundary'])}</p>
    <p>When that condition fails, look for this visible break: {esc(concept['failure_mode']).lower()}</p>
    <p><strong>Recognize it in a new problem:</strong> {esc(concept['recognition_test'])}</p>
  </div>
</section>{learning_control_check}
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
            "Once those pieces are named, the course can ask for more than one command. It can ask for a whole legal history of states and actions.",
            "If this move is skipped, every later method is floating. The solver may optimize a wish, the learner may copy labels without knowing state, and the safety check may protect the wrong boundary.",
        ),
        (
            "02",
            "Make the whole path the decision",
            "Static optimization chooses a point. Control chooses a path. Calculus of variations, costates, Hamiltonians, shooting, transcription, and collocation are different ways of saying that a legal answer is not one number; it is a history of states and actions that must fit the dynamics at every step.",
            "For a robot arm moving around a fixture, a shortest geometric curve can still require impossible torque. Direct methods put states and commands on a grid, enforce dynamics between neighboring grid points, and let the solver choose a path that the arm can physically trace.",
            "Once a path can be written as variables and constraints, the course asks how to judge paths whose early choices change later options.",
            "If this move is skipped, the learner may think control is a sequence of disconnected optimizations instead of a time-coupled path through physical states.",
        ),
        (
            "03",
            "Price the future from each state",
            "Dynamic programming appears when the future after the next state is another copy of the same problem. The value function is the price tag on being in a state with all future choices still open. Bellman recursion is the bookkeeping rule: compare actions by the cost now plus the future value of the state they create.",
            "A rover may choose a longer route around rough ground because the short route damages its wheels. The immediate distance is smaller, but the next state has worse future value because every later move is harder.",
            "Once future burden can be stored at a state, the course can exploit local structure: near a planned motion, that value can have a simpler shape.",
            "If this move is skipped, delayed consequences disappear. A controller will prefer the short route, early option exercise, or cheap first action even when it creates a worse future.",
        ),
        (
            "04",
            "Use local structure when the world is near the plan",
            "LQR works when the real motion is close enough to a nominal motion that the dynamics look linear and the cost looks like a bowl. It is not magic feedback. It is a local promise: small errors near the planned state can be pushed back with a fast linear correction.",
            "A hovering drone can use LQR for a small drift. After clipping a branch and tumbling, the same local model is no longer the right picture; the state has left the region where the approximation tells the truth.",
            "Once the boundary of local feedback is visible, the course can explain why a controller replans when the measured state moves away from the old prediction.",
            "If this move is skipped, LQR sounds like a universal controller rather than a local argument with a clear operating region.",
        ),
        (
            "05",
            "Replan without losing tomorrow",
            "MPC turns planning into feedback by repeatedly solving a short future problem and applying only the first command. Reachability and recursive feasibility ask the question MPC alone can miss: after this first command, will the next problem still have a legal escape?",
            "A car can choose a narrow traffic gap that is collision-free for two seconds and still be making a bad control choice if the state after one second has no safe braking or steering option left.",
            "Once replanning and safety are clear, learning can enter without pretending that data removes the need for state, action, dynamics, cost, and constraints.",
            "If this move is skipped, a learner may trust every feasible short-horizon solve and miss the handoff failure where tomorrow has no legal move.",
        ),
        (
            "06",
            "Learn only where written structure runs out",
            "Learning-based control is not a replacement for control thinking. It enters when the model is incomplete, the cost is hard to write, expert behavior is easier to show than specify, or trial feedback is the only teacher. The same questions remain: what is the state, what action is chosen, what future is being priced, and what failure does the learner create?",
            "Behavior cloning can teach a robot a drawer-pulling motion from demonstrations, but the learned policy may drift into a handle angle the expert never showed. RL can improve from reward, but if the reward pays only for speed, the robot may learn to damage the object quickly.",
            "This move returns to the beginning: even when the policy is learned, it still acts on state, issues actions, changes the next state, and creates the future it must handle.",
            "If this move is skipped, learning looks like a separate topic instead of another way to fill missing model, reward, value, or policy structure inside a control loop.",
        ),
    ]
    spine_html = "".join(
        f"""<section class="fp">
  <div class="kick">{num} · course move</div>
  <h2>{esc(title)}</h2>
  <div class="essay"><p>{esc(problem)}</p></div>
  <div class="explain-box"><p>{esc(example)}</p></div>
  <div class="essay">
    <p><strong>Handoff:</strong> {esc(handoff)}</p>
    <p><strong>If skipped:</strong> {esc(if_skipped)}</p>
  </div>
</section>"""
        for num, title, problem, example, handoff, if_skipped in spine_items
    )
    spine_intro = """
<h1>Course Spine</h1>
<p class="lede">The course is one question repeated at larger scale: what should this system do now, knowing that the action changes the future it will have to live in?</p>
<div class="essay">
  <p>Use one car merge to read the whole course. The car is in the right lane, a truck is ahead, a faster car is behind in the left lane, and the controller has two seconds to decide whether to accelerate, brake, or stay put. The state is not just lane position; it includes speed, heading, nearby cars, and enough prediction to know what the next command will change. The action is not "merge"; it is steering, throttle, and brake. Dynamics turn those commands into the next state. Cost prices progress, comfort, and delay. Constraints forbid collision, road departure, and acceleration beyond limits.</p>
  <p>Once that setup exists, the rest of the course is not a list of techniques. It is a sequence of repairs to harder versions of the same pressure. If the whole future path matters, trajectory optimization appears. If the next state changes every later choice, dynamic programming and value appear. If the car is close to a planned lane center, local feedback can help. If traffic moves, MPC replans. If nearby driver behavior, reward, or contact strategy cannot be written cleanly, learning enters. The spine below names each repair and the mistake it prevents.</p>
</div>
<h2>Same Car, Harder Questions</h2>
<div class="essay">
  <p>Read the spine as six passes over one traffic scene. At first the car only needs a truthful setup: speed, heading, nearby cars, steering, throttle, brake, road limits, comfort, and collision. Then the question grows from one command to a whole two-second history. The path must say where the car is after each small time step, what command was used, and whether tire force and acceleration stayed within the physical limits.</p>
  <p>Next the route asks why a cheap first move can be wrong. Accelerating into the gap may reduce delay now, but the next state can be expensive because the left-lane car is closing and the brake margin is gone. That is the value-function idea in ordinary clothes: the present action is judged by the future state it creates, not by the next meter alone.</p>
  <p>Then the car is near a planned lane center, so a local feedback law can correct small drift. This only works while the car remains near the region where the local model is honest. If the tires saturate or the road turns icy, the same local picture stops telling the truth. The course then replans from measurement: solve a short future, use the first command, measure again. But replanning has its own failure. The first command must leave the next solve with legal braking or steering, or the controller has only postponed the crash.</p>
  <p>Learning enters last because some parts of the scene may not be writable by hand. The other driver's behavior may come from data. The reward for comfort may be learned from examples. A policy may be copied from demonstrations. But the learned piece still sits inside the same loop. It receives state, chooses action, changes the next state, and can create states the data did not cover.</p>
</div>
"""
    write(SITE / "course-spine.html", page("Course Spine", f"{spine_intro}{spine_html}", "spine"))

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
  <p><strong>Wrong shortcut:</strong> {esc(deep.get('wrong_turn', ''))}</p>
  <p><strong>Boundary test:</strong> {esc(deep.get('boundary', ''))}</p>
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
  <p>A second test is transfer. If you can move the family from a car to a drone, or from a robot arm to a warehouse policy, without changing the family question, then the method has been understood as a response to pressure rather than as a name to memorize.</p>
</div>
<h2>Choosing A Family In One Run</h2>
<div class="essay">
  <p>Take a warehouse robot asked to pull a drawer. Problem setup comes first: state is gripper pose, handle pose, joint velocity, contact estimate, and shelf geometry; action is arm motion and gripper force; constraints forbid collision and damaging contact. Trajectory optimization enters if the drawer motion can be planned from a trusted model. Dynamic programming enters if each partial opening changes the value of later choices. Local structure enters near a known motion where small errors can be corrected cheaply. Replanning enters when contact slips and the measured state no longer matches the plan. Learning enters when the contact strategy is easier to demonstrate than write.</p>
  <p>The wrong family choice has a visible failure. Pure geometry misses torque and contact. Pure dynamic programming may be too large without a compact state. Pure local feedback fails after the handle slips. Pure MPC can replan into a state with no safe contact recovery. Pure imitation can drift outside demonstrated handle poses. The family choice is therefore a diagnosis of what is hard in the current problem, not a preference for a fashionable method.</p>
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
        test = PRIMITIVE_TESTS.get(p["id"], {})
        body = f"""
<p>{esc(PRIMITIVE_DEEPENING.get(p['id'], p['plain_language']))}</p>
<p><strong>Question it answers:</strong> {esc(test.get('question', ''))}</p>
<div class="explain-box"><p>{esc(test.get('run', ''))}</p></div>
<p><strong>Failure if wrong:</strong> {esc(test.get('failure', ''))}</p>
<p>{links}</p>
"""
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
  <p>Read each primitive as a small test. If you cannot answer the question it asks, run the concrete case, and name the failure when it is wrong, the word has not become usable yet.</p>
</div>
<h2>One Debug Sequence</h2>
<div class="essay">
  <p>Take the car merge from the course spine. The state must include lane position, speed, heading, nearby cars, and enough prediction to know whether the next command leaves room. The action is steering, throttle, and brake. Dynamics say how those commands move the car through tire grip and speed. Cost prices progress, comfort, and delay. Constraints forbid collision and road departure. Value prices the future after the first command. A policy chooses the command from the current state. Uncertainty admits that the rear car may accelerate or the tire grip may be lower than expected. Feasibility asks whether any legal future remains after the first move.</p>
  <p>Now change the object to a drone entering a narrow window. The same primitive sequence still works. State needs position, velocity, attitude, battery, wind, and localization uncertainty. Action is thrust or attitude target. Dynamics carry thrust through acceleration. Cost prices time, energy, and landing accuracy. Constraints enforce clearance and thrust limits. Value prices whether entering the window leaves enough room to stop. Policy chooses the next command. Uncertainty widens the future. Feasibility asks whether the drone can still avoid the frame after the first command.</p>
  <p>That transfer is the point of this page. A primitive is learned only when it survives a change of machine without losing its job in the control feedback loop.</p>
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
  <p><strong>Input:</strong> {esc(item.get('input', ''))}</p>
  <p><strong>Output:</strong> {esc(item.get('output', ''))}</p>
  <p><strong>Wrong read:</strong> {esc(item.get('wrong_read', ''))}</p>
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
  <p>The reading order is always the same. First ask what real situation forced the formula to exist. Then identify the object it stores. Then name the operation it performs. Only after that should the symbols matter.</p>
</div>
<h2>One Reading Run</h2>
<div class="essay">
  <p>Use a landing rocket. Dynamics read height, velocity, fuel, and thrust, then return the next height, velocity, and fuel. The objective reads the whole candidate landing history and returns a score built from fuel use, touchdown speed, and final height error. Bellman recursion reads one thrust choice, the next state it creates, and the stored future value of that next state. The Hamiltonian reads immediate fuel cost and the costate price of changing velocity. MPC reads the measured rocket state, solves a short landing problem, applies the first thrust command, then measures again. A policy-gradient formula would read rollout returns from attempted landings and adjust a policy only if the credit signal is credible.</p>
  <p>This is how to reject a shallow formula reading. If the formula does not say what enters, what leaves, what future is priced, and where the reading fails, the symbols have not been explained yet.</p>
</div>
<h2>Three Checks For Any Formula</h2>
<div class="essay">
  <p>First, ask what would go wrong in the world if the formula did not exist. Dynamics exist because commands are not teleportation. Value exists because the next state carries later burden. MPC exists because yesterday's plan goes stale after measurement.</p>
  <p>Second, ask what object the formula carries. A transition rule carries motion, a cost carries preference, a value function carries future burden, a costate carries sensitivity, and a policy update carries evidence from rollouts.</p>
  <p>Third, ask what false reading would hurt a real system. A cost can omit damage. A value can price the wrong state. A local condition can miss the global path. A short MPC horizon can leave no future move. A policy update can reward noise.</p>
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
    derivation_intro = """
<h1>Derivation Walkthroughs</h1>
<p class="lede">Slow, problem-first derivations that explain why the formula shape exists before asking the learner to manipulate symbols.</p>
<div class="essay">
  <h2>How To Read A Derivation</h2>
  <p>A derivation is not a ritual for moving symbols from one line to the next. It is a way to make a physical accounting rule unavoidable. Start by naming the thing that must be preserved: a state transition, a whole path, a future value, a local sensitivity, a feasibility condition, or a policy update.</p>
  <p>Then ask what one legal step does. For Bellman recursion, one action creates one next state and carries one immediate cost. For the Hamiltonian, one control change has a cost now and a priced effect on later state. For direct transcription, one grid interval must connect neighboring state variables through dynamics. If the one-step move is vague, the derivation will only look formal.</p>
  <p>Finally, read the failure test before trusting the formula. A Bellman derivation fails if the state does not carry the future-relevant information. A local quadratic derivation fails if the system has left the small region where the bowl picture is truthful. An MPC argument fails if the first action leaves no legal next solve. The failure is not a footnote; it tells you what the derivation assumed.</p>
</div>
<h2>One Derivation Run</h2>
<div class="essay">
  <p>Use the rover route from the value pages. The rover can take a rocky shortcut or a longer smooth path. The derivation should not begin with the Bellman symbol. It begins with the fact that the first move changes wheel health, battery, and position. Those variables become the state because they decide what future moves remain possible.</p>
  <p>Now price each first move. The rocky move may have low distance cost, but it creates a next state with damaged wheels. The smooth move pays more now, but leaves a next state with cheaper later travel. The Bellman shape appears because every first move is judged by the same two-part ledger: what it costs now plus the future value stored at the state it creates.</p>
  <p>This is the standard for every card below. The formula shape should feel like the shortest honest way to keep the accounting straight, not like a symbol copied from the lecture.</p>
</div>
<h2>Derivation Cards</h2>
"""
    write(SITE / "derivations.html", page("Derivations", f"{derivation_intro}<section class=\"stack\">{''.join(derivation_cards)}</section>", "derivations"))

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
  <tr><th>Concrete Run</th><td>{esc(item.get('concrete_run', ''))}</td></tr>
  <tr><th>Method Boundary</th><td>{esc(item.get('method_boundary', ''))}</td></tr>
  <tr><th>Transfer Question</th><td>{esc(item.get('transfer_question', ''))}</td></tr>
</table>
<p>{linked}</p>
"""
        example_cards.append(card(item["title"], body))
    worked_intro = """
<h1>Worked Examples</h1>
<p class="lede">Concrete setups that force the learner to name state, action, cost, constraints, method route, and failure signal.</p>
<div class="essay">
  <h2>How To Read A Worked Example</h2>
  <p>Begin with the moving object, not the method name. A rocket, rover, robot arm, car, or drone has a present condition. It accepts only certain commands. The world changes after each command. Some endings are wanted, some are costly, and some are forbidden. The table is useful only after those pieces are visible.</p>
  <p>Then read the method route as a choice made under pressure. A shooting method is natural when the whole path can be described by a small set of starting guesses. A transcription method is natural when many points along the path must satisfy dynamics and limits. Dynamic programming is natural when the same state can be reached by different earlier choices and the future burden must be stored at that state.</p>
  <p>The failure signal is the part to linger on. If the example says a rocket violates touchdown speed, that is not a small detail; it means the cost or constraint failed to protect the real landing. If the rover chooses sharp rocks because distance is cheap, the future state was priced too weakly. If a learned policy leaves the demonstrated poses, the training data stopped covering the states the controller now visits.</p>
</div>
<h2>Example Cards</h2>
"""
    write(SITE / "worked-examples.html", page("Worked Examples", f"{worked_intro}<section class=\"stack\">{''.join(example_cards)}</section>", "derivations"))

    drill_cards = []
    solution_cards = []
    for item in drills:
        linked = " ".join(f'<span class="pill">{concept_link(concepts_by_id[cid])}</span>' for cid in item.get("linked_concepts", []) if cid in concepts_by_id)
        criteria = section_list([esc(criterion) for criterion in item.get("grading_criteria", [])])
        drill_cards.append(
            card(
                item["title"],
                f"<p>{esc(item['prompt'])}</p><p><strong>Setup hint:</strong> {esc(item.get('setup_hint', ''))}</p><p><strong>Wrong turn to avoid:</strong> {esc(item['wrong_turn'])}</p><p><strong>What a strong answer must include:</strong></p>{criteria}<p><strong>Transfer variant:</strong> {esc(item.get('transfer_variant', ''))}</p><p>{linked}</p>",
            )
        )
        solution_cards.append(
            card(
                f"{item['title']} Solution",
                f"<p><strong>Prompt:</strong> {esc(item['prompt'])}</p><p><strong>Setup hint:</strong> {esc(item.get('setup_hint', ''))}</p><p><strong>Wrong turn:</strong> {esc(item['wrong_turn'])}</p><p><strong>Strong answer:</strong> {esc(item['strong_answer'])}</p><p><strong>Solution walkthrough:</strong> {esc(item.get('solution_walkthrough', ''))}</p><p><strong>Transfer variant:</strong> {esc(item.get('transfer_variant', ''))}</p><p><strong>Grading criteria:</strong></p>{criteria}<p>{linked}</p>",
            )
        )
    drill_intro = """
<h1>Drills</h1>
<p class="lede">Practice prompts that train setup, method choice, future-cost recognition, feasibility diagnosis, reward repair, and approximation boundaries.</p>
<div class="essay">
  <h2>How To Work A Drill</h2>
  <p>Do not begin by hunting for the lecture label. First write the machine in plain words: what is measured now, what command can be sent, what changes next, what future is being paid for, and what line cannot be crossed. If that sentence cannot be written, the answer is still too thin.</p>
  <p>After the setup is physical, choose the method by the kind of pressure in the problem. A path-planning drill asks for many linked states and commands. A Bellman drill asks what future burden is stored at a state. An MPC drill asks whether the short plan leaves a state from which another legal plan can still be made. A learning drill asks which part of the control loop is missing and what new failure data creates.</p>
  <p>The transfer variant is the real test. If a drone delivery answer cannot survive an indoor drone window, it was memorized. If a traffic MPC answer cannot survive a narrower braking margin, it did not understand recursive feasibility. If a reward repair answer cannot survive a different robot task, it only patched the words.</p>
</div>
<h2>Drill Cards</h2>
"""
    solution_intro = """
<h1>Solutions</h1>
<p class="lede">Full solution notes that name the common wrong turn before giving the stronger control explanation.</p>
<div class="essay">
  <h2>What Counts As A Strong Solution</h2>
  <p>A strong solution should sound like an operator could check it. It names the state record, the command, the rule that moves the system, the cost paid along the way, the end condition, and the hard limits. It does not hide behind words such as performance or behavior. It says what changes and why.</p>
  <p>For path problems, the solution should say whether the unknown is a continuous curve, a sequence of knot points, or a feedback rule. For future-price problems, it should say what value is stored and how an action changes the next state before the next value is read. For repeated planning, it should test the state left behind for the next solve. For learning, it should say what the data covers and what happens when the closed loop visits states outside that cover.</p>
  <p>Use the wrong turn as a diagnostic. The wrong answer is not merely incomplete; it usually drops one physical piece. It drops the action limits, drops wind, drops future cost, drops terminal safety, drops distribution shift, or lets reward reward the wrong thing. The stronger answer repairs the missing piece and then checks the repair on the transfer variant.</p>
</div>
<h2>Solution Cards</h2>
"""
    write(SITE / "drills.html", page("Drills", f"{drill_intro}<section class=\"stack\">{''.join(drill_cards)}</section>", "drills"))
    write(SITE / "solutions.html", page("Solutions", f"{solution_intro}<section class=\"stack\">{''.join(solution_cards)}</section>", "drills"))

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
                f"<p><strong>Diagnosis:</strong> {esc(item['diagnosis'])}</p><p><strong>Failure consequence:</strong> {esc(item.get('failure_consequence', ''))}</p><p><strong>Replacement rule:</strong> {esc(item.get('replacement_rule', ''))}</p><p><strong>Stronger version:</strong> {esc(item['strong'])}</p><p><strong>Transfer prompt:</strong> {esc(item.get('transfer_prompt', ''))}</p>",
            )
        )
    misconception_intro = """
<h1>Misconceptions And Weak-Claim Repairs</h1>
<p class="lede">Weak claims are places where the writing has lost the machine, the command, the future, or the boundary.</p>
<div class="essay">
  <h2>How To Repair A Weak Claim</h2>
  <p>First ask what the sentence hides. A claim about a better controller may hide the cost being reduced. A claim about safety may hide the reachable states being protected. A claim about learning may hide which part is learned: policy, reward, value, or model. The repair should name the hidden object in ordinary words before it names the course term.</p>
  <p>Second, ask what would go wrong in a real run. A car planner can look legal for two seconds and still leave no braking path. A model-based learner can plan through a learned model and choose a move that only works inside the model mistake. A reward can be maximized by the wrong action if the reward misses the task goal.</p>
  <p>Third, write the replacement sentence so it can be checked. It should say what state is measured, what action is allowed, what future is priced, what constraint is active, or what data cover is missing. If none of those pieces appears, the sentence is probably still decoration.</p>
  <p>A repair is done only when it changes what the reader would inspect. For MPC, the reader should inspect the state left for the next solve. For imitation learning, the reader should inspect states reached after small policy errors. For reward design, the reader should inspect the action that wins the score and ask whether it also completes the task.</p>
</div>
<h2>Repair Cards</h2>
"""
    write(SITE / "misconceptions.html", page("Misconceptions", f"{misconception_intro}<section class=\"grid\">{''.join(misconception_cards)}</section>", "review"))

    evidence_html = "".join(evidence_card(row) for row in evidence)
    evidence_intro = """
<h1>Evidence Ledger</h1>
<p class="lede">Evidence is the guardrail between lecture source and teaching synthesis.</p>
<div class="essay">
  <p>Each record points to a lecture, video id, timestamp URL, local transcript window, and raw VTT source. The timestamp is only the locator. The record must say what the transcript directly supports and what the site adds beyond the transcript.</p>
  <p>Use this page to check honesty. A keyword match is not evidence by itself. A good evidence record names the lecture argument: for example, that Lecture 11 discusses reachability through reachable sets, or that Lecture 7 frames dynamic programming as state-indexed recursion.</p>
  <p>If a concept page makes a stronger teaching claim, the evidence record should make the boundary visible rather than hiding that synthesis.</p>
</div>
<h2>How To Inspect One Evidence Record</h2>
<div class="essay">
  <p>Read the transcript window first and underline only what the lecture itself says. It may name a method, introduce a formal object, contrast two approaches, or state a condition. Do not let the nearby concept page smuggle in extra meaning yet.</p>
  <p>Then read <strong>Transcript supports</strong>. That sentence should be narrow. For recursive feasibility, a strong support sentence says the lecture discusses persistent feasibility across repeated MPC solves. It should not claim that the transcript proves the whole car-gap story. The car-gap story belongs to teaching synthesis.</p>
  <p>Now read <strong>Synthesis boundary</strong>. This is where the page is allowed to teach in plain words: a first MPC command can leave tomorrow's solve with no legal braking or steering continuation. The boundary is honest only if it tells the reader that this is an interpretation built from the lecture topic, not a quotation from the caption.</p>
  <p>Reject the record if the transcript window only contains a word match, if the support sentence is broader than the quoted window, if the synthesis boundary is blank, or if the concept page has no concrete operation tied to that evidence. Evidence should narrow the claim before the prose becomes rich.</p>
</div>
<h2>Two Good Evidence Shapes</h2>
<div class="essay">
  <p>For a math concept, the transcript should support the object or operation. A Bellman record can support state-indexed recursion, value, and immediate-plus-future accounting. The concept page can then teach the rover shortcut: the rocky path has low cost now but creates a damaged-wheel state with worse future value.</p>
  <p>For a learning concept, the transcript should support the learning setup: demonstrations, reward, policy update, exploration, or learned model. The concept page can then teach the closed-loop risk: a policy trained on centered drawer-handle demonstrations can move the handle off-center and create a state absent from the data.</p>
  <p>In both cases, evidence does not make the page less explanatory. It makes explanation accountable. The richer the page gets, the more visible the source boundary must be.</p>
  <p>A reviewer should leave a record with one clear verdict: source supports the term, source supports the operation, source supports only a nearby topic, or source is too weak for the page claim. That verdict keeps later editing from treating every timestamp as equal, complete, or equally trusted.</p>
</div>
"""
    write(SITE / "evidence.html", page("Evidence", f"{evidence_intro}<section class=\"stack\">{evidence_html}</section>", "evidence"))

    review = [
        (
            "First-principles depth",
            "Open a setup concept, a dynamic-programming concept, an MPC concept, and a learning concept. The page should begin with a real object such as a drone, car, rocket, rover, robot arm, shelf, or reward signal. If the first sentence that teaches the idea is only a formal definition, the page is not done.",
        ),
        (
            "Concrete operation",
            "For each page, identify what gets moved, updated, propagated, minimized, priced, constrained, sampled, or replanned. A good page lets the reader say what the mathematical object does before seeing symbols.",
        ),
        (
            "Evidence discipline",
            "Open evidence records and verify that local transcript windows support the concept vocabulary without pretending to prove the whole synthesis. The record should say what the transcript supports and what the site adds as explanation.",
        ),
        (
            "Practice transfer",
            "Run the drills and read the solutions. A strong solution names the wrong turn, explains why it fails in a control setting, and then repairs the setup or method choice.",
        ),
        (
            "Reference comparison",
            "Compare the main pages with the local reference explainers. They should feel like compact essays: problem, failure, object, operation, concrete run, math one level deeper, and boundary.",
        ),
        (
            "Audit path",
            "Use the completion audit, evidence ledger, and provenance page to verify transcript coverage, timestamp anchors, generated pages, local rebuild commands, and richness gates.",
        ),
    ]
    review_intro = """
<h1>Review Guide</h1>
<p class="lede">Use this page like a reviewer path through the site. The goal is not to confirm that files exist; it is to decide whether the writing teaches control from first principles.</p>
<div class="essay">
  <p>A quick review should sample one page from each part of the course: setup, trajectory optimization, dynamic programming, MPC, imitation learning, reinforcement learning, and model-based RL. On each page, ask whether a learner can retell the idea using a real system before using course vocabulary.</p>
  <p>The review should be strict about order. A page should start with a pressure in the world, then introduce the mathematical object because that object solves a problem. If the reader meets symbols before they know what the symbols are carrying, the page still needs work. If the page has a concrete story but never says where the story breaks, it also needs work.</p>
  <p>The reference standard is an explainer that a learner can retell without memorizing. After reading a page, the learner should be able to say: here is the machine, here is the command, here is what changes next, here is what future gets priced, here is the line the plan cannot cross, and here is the assumption that can fail.</p>
</div>
"""
    walkthrough_cards = "".join(
        card(
            item["title"],
            f"""<p><strong>Sample:</strong> {esc(item['sample'])}</p>
<p><strong>Pass condition:</strong> {esc(item['pass'])}</p>
<p><strong>Reject condition:</strong> {esc(item['reject'])}</p>""",
        )
        for item in REVIEW_WALKTHROUGH
    )
    review_body = f"""{review_intro}
<h2>Reviewer Route</h2>
<section class="stack">{walkthrough_cards}</section>
<h2>Rubric Checks</h2>
<section class="stack">{''.join(card(a,b) for a,b in review)}</section>"""
    write(SITE / "review-guide.html", page("Review Guide", review_body, "review"))

    quality = [
        (
            "First principles",
            "Start from a moving thing and an available command. A sentence is strong when it says what state changes, what action causes the change, what future consequence matters, and what assumption could make the conclusion false.",
        ),
        (
            "Plain language",
            "Use everyday words before course labels. Say the drone commands thrust before saying control input. Say the rover stores future travel cost before saying value function. Say the car must still have a legal braking future before saying recursive feasibility.",
        ),
        (
            "Concrete math",
            "Translate formal objects without flattening their job. A formula block should name the object, the operation, a small run with numbers or time steps, and the failure case.",
        ),
        (
            "Failure boundary",
            "State where the method breaks: model mismatch, infeasibility, coarse discretization, local approximation error, distribution shift, unsafe exploration, reward hacking, or learned-model exploitation.",
        ),
        (
            "Evidence honesty",
            "Separate what the transcript directly supports from synthesis beyond the transcript. A timestamp is not enough; the record must name the lecture argument being used.",
        ),
        (
            "No filler",
            "Remove sentences that only praise a method without naming its job. Replace praise with the state, action, future cost, constraint, approximation, or failure a practitioner would see.",
        ),
    ]
    quality_intro = """
<h1>Quality Rubric</h1>
<p class="lede">This rubric is an editorial test, not a decoration. It exists to keep the AA203 site close to the richer first-principles explainers: concrete, simple, low-jargon, and transferable.</p>
<div class="essay">
  <p>The standard is visible transfer. After reading a page, a learner should be able to recognize the same idea in a new car, drone, robot arm, rover, or learning setup. If the learner can only repeat a definition, the page is not rich enough yet.</p>
  <p>Good writing here is plain but not thin. It uses everyday words to carry real technical load: what is known, what is commanded, what moves, what is priced, what is forbidden, and what breaks.</p>
  <p>A page should also survive a cold read. A learner who has not watched the lecture should still be able to follow the ordinary pressure, then use the evidence link to see what the lecture actually supports. The prose can synthesize, but it should not float away from the transcript or hide the assumption boundary.</p>
  <p>The simplest editorial question is this: can the sentence be tested against a small physical run? If not, rewrite it until it names a state, action, transition, cost, constraint, value, policy, disturbance, or failure.</p>
</div>
"""
    quality_test_cards = "".join(
        card(
            item["title"],
            f"""<p><strong>Weak version:</strong> {esc(item['weak'])}</p>
<p><strong>Stronger version:</strong> {esc(item['strong'])}</p>
<p><strong>Pass test:</strong> {esc(item['test'])}</p>""",
        )
        for item in QUALITY_TESTS
    )
    quality_body = f"""{quality_intro}
<h2>Editorial Tests</h2>
<section class="stack">{quality_test_cards}</section>
<h2>Rubric Rules</h2>
<section class="grid">{''.join(card(a,b) for a,b in quality)}</section>"""
    write(SITE / "quality.html", page("Quality", quality_body, "review"))

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
    completion_requirement_rows = (
        "<table><tr><th>Requirement</th><th>Evidence Now</th><th>What This Does Not Prove</th></tr>"
        + "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in COMPLETION_REQUIREMENTS)
        + "</table>"
    )
    completion_intro = """
<h1>Completion Audit</h1>
<p class="lede">This page is the local proof that the package can be rebuilt and reviewed.</p>
<div class="essay">
  <p>The audit is deliberately mechanical about files, counts, transcript coverage, evidence review, and generated pages. That mechanical check does not replace editorial judgment, but it prevents a different failure: polished prose with missing transcripts, broken links, absent evidence, or stale generated output.</p>
  <p>Read this together with the quality rubric. The audit proves the source layer is present and the site is coherent; the rubric asks whether the writing reaches the first-principles standard.</p>
  <p>A reviewer should be able to rerun the build, reopen the same pages, and see the same transcript-backed route through the course, without hidden manual edits.</p>
  <p>The audit is also careful about what it does not claim. A green build proves that required structures and source trails are present. It does not prove that every page has the same depth as the strongest reference explainers. That final judgment still requires sampling the rendered pages as writing.</p>
</div>
"""
    completion_review = """
<h2>Requirement Evidence</h2>
<div class="essay">
  <p>Use this table before declaring completion. Each row names the current evidence and the boundary of that evidence. The boundary matters because this course goal is not just to generate files; it is to produce pages that teach control from first principles in plain language.</p>
</div>
"""
    completion_final_review = """
<h2>Two Proofs Required</h2>
<div class="essay">
  <p>Completion needs two different proofs. The mechanical proof is local and repeatable: transcripts exist, artifacts rebuild, links resolve, evidence anchors render, and validation passes. The editorial proof is slower: sampled pages must read like first-principles explanations, not polished summaries.</p>
  <p>Do the mechanical proof first. Run the build chain and confirm the numbers on this page: 19 transcripts, 38 concepts, 38 evidence records, 57 HTML pages, zero missing transcript references, and zero remaining manual evidence reviews. If those numbers drift, the site is not ready for editorial judgment because the source layer itself is unstable.</p>
  <p>Then do the editorial proof in the browser. Open a page and ask what physical pressure starts the explanation. A state page should make missing velocity visible. A Bellman page should show why the next state carries future burden. An MPC page should distinguish a legal short plan from a legal next solve. A learning page should show how data, reward, or a learned model changes the next state the controller must handle.</p>
  <p>The reject rule is strict: if a page can be summarized as "this lecture covers this topic," it fails. If it defines a term without a machine, command, future cost, constraint, or failure, it fails. If it links evidence but the evidence only supports a nearby keyword, it fails. If it sounds rich but cannot be traced back to a transcript window and synthesis boundary, it fails.</p>
  <p>For each sampled page, write one sentence in your own words without using the page title. If that sentence cannot name the machine, the command, the future consequence, and the bad outcome, the page has not yet taught the idea. The test is simple because the course promise is simple: a learner should be able to carry the idea to a new car, drone, rover, robot arm, or learned policy.</p>
</div>
"""
    sample_cards = "".join(card(title, f"<p>{esc(body)}</p>") for title, body in COMPLETION_SAMPLE_CHECKS)
    completion_close = """
<h2>Human Review Still Required</h2>
<div class="essay">
  <p>Before calling the course finished, open the course spine, concept atlas, formula reader, review guide, quality rubric, two setup concept pages, two dynamic-programming pages, two MPC or reachability pages, and two learning pages. Each page should survive the same test: ordinary pressure first, concrete operation next, math one level deeper, then the boundary where the idea stops working.</p>
  <p>If a sampled page only summarizes a lecture, defines a term, or praises a method without showing the state/action/future-cost machinery, the course is not done even if this audit table is green.</p>
  <p>The final reviewer should write down at least one pass example and one risk example. A pass example names the ordinary problem, the object, the operation, the concrete run, the math layer, the boundary, and the evidence record. A risk example names the exact page and the sentence or section that still feels thin. That note becomes the next editing target.</p>
</div>
"""
    sample_section = f"""
<h2>Sampled Page Checks</h2>
<section class="stack">{sample_cards}</section>
"""
    write(SITE / "completion-audit.html", page("Completion Audit", f"{completion_intro}{audit_table}{completion_review}{completion_requirement_rows}{completion_final_review}{sample_section}{completion_close}", "review"))

    provenance_cards = "".join(card(title, f"<p>{esc(body)}</p>") for title, body in PROVENANCE_CHECKS)
    write(
        SITE / "provenance.html",
        page(
            "Provenance",
            f"""
<h1>Provenance</h1>
<p class="lede">Provenance explains where the course material came from and how the site is rebuilt from local artifacts.</p>
<div class="essay">
  <p>The canonical source is <a href="{esc(manifest['playlist_url'])}">{esc(manifest['playlist_url'])}</a>. The repo keeps this source layer separate from synthesis so a reviewer can inspect the raw material before trusting the teaching pages.</p>
  <p>Playlist metadata is stored in <code>raw-material/youtube/playlist.json</code>. Caption files are stored under <code>raw-material/youtube/transcripts/raw-vtt/</code>, cleaned text under <code>raw-material/youtube/transcripts/clean/</code>, and availability in <code>raw-material/youtube/transcript-index.json</code>.</p>
  <p>Analysis artifacts live in <code>analysis/concepts/</code>, <code>analysis/evidence/</code>, <code>analysis/throughlines/</code>, and <code>analysis/teaching/</code>. The site under <code>site/</code> is generated output, not the only source of truth.</p>
  <p>The build path is: download or refresh transcripts, build the first-principles atlas and evidence ledger, build teaching artifacts, run the quality audit, render the static site, then validate links, evidence references, and richness gates.</p>
  <p>This separation matters because the writing can improve without losing the source trail. A richer explanation should still point back to the same transcript window and declare what is synthesis. That is the difference between a course companion and an unsupported essay or summary.</p>
</div>
<h2>Source-To-Page Trail</h2>
<section class="stack">{provenance_cards}</section>
<h2>Concrete Claim Check</h2>
<div class="essay">
  <p>Use reachability as the model check. The source layer stores the Lecture 11 caption window that names reachable sets, target sets, controls, disturbances, and safety objectives. The evidence record says that the transcript supports reachability as set-valued reasoning. The concept page then teaches the ordinary rule: from this car state, with this steering and braking limit, which future states can still avoid the wall or bad target?</p>
  <p>The teaching sentence is allowed to be clearer than the transcript, but it is not allowed to pretend the transcript proved every part of the synthesis. A reviewer should be able to move from rendered page to evidence id to local transcript window to raw VTT timestamp without guessing.</p>
  <p>Do the same check for one learning page. For behavioral cloning, the transcript supports supervised learning from demonstrated state-action behavior. The page adds the closed-loop warning: the learned policy can create states the expert did not label. That extra warning is allowed because the provenance trail names it as synthesis rather than transcript quotation.</p>
</div>
<h2>One Claim From Source To Teaching</h2>
<div class="essay">
  <p>Take the sentence: after today's MPC action, tomorrow's optimization problem must still have a legal solution. The raw caption layer should locate the lecture moment where MPC feasibility, terminal structure, or stability is discussed. The cleaned transcript makes that moment searchable. The evidence record states the narrow support: the lecture discusses recursive feasibility as a condition on repeated MPC solves.</p>
  <p>The concept page may then turn that into the traffic-gap example. A car can fit between two vehicles for the next two seconds and still be in a bad state if the first acceleration leaves no braking or steering move for the next solve. That car story is not copied from the transcript. It is the page's teaching move, and provenance is what keeps that move honest.</p>
  <p>A reviewer should be able to ask four questions. What exact transcript window supports the course term? What does the evidence record say the window supports? What did the concept page add to make the idea teachable? What boundary tells the reader where the claim stops? If any answer is missing, the page may still be readable, but it is not yet source-disciplined.</p>
</div>
<h2>What A Rebuild Protects</h2>
<div class="essay">
  <p>A rebuild protects against quiet drift. If a concept is deepened only in rendered HTML, the next generated site can erase it. If the concept data is changed without rebuilding, the visible page can lie about the current source. If the validator is not run, broken evidence anchors and missing transcript files can hide under polished writing.</p>
  <p>The durable route is simple: source material, analysis artifact, generator, rendered page, validator. Each step has a job. Source material keeps the course tied to the playlist. Analysis artifacts organize concepts and evidence. The generator turns those records into pages. The validator checks that required markers, links, word floors, evidence ids, and anti-filler rules still hold.</p>
  <p>This does not make the prose automatically rich. It makes the prose reviewable. The human review still has to compare pages with the reference explainers and ask whether the writing starts with ordinary pressure, names the object, runs the operation, opens the math one level deeper, and shows where the idea breaks.</p>
</div>
<h2>Do Not Trust The Page If</h2>
<div class="essay">
  <p>Do not trust a page if the source path is missing, the evidence record only repeats a keyword, the synthesis boundary is blank, the rendered page has no evidence anchor, the concept page skips the concrete run, or the validator was not run after generation.</p>
  <p>Do not trust a manual edit in <code>site/</code> by itself. The durable source is the generator and analysis artifacts. A real improvement changes the source layer, rebuilds the page, and passes validation.</p>
  <p>Run <code>python3 scripts/build_first_principles_atlas.py</code>, then <code>python3 scripts/build_teaching_artifacts.py</code>, then <code>python3 scripts/audit_course_quality.py</code>, then <code>python3 scripts/build_site.py</code>, then <code>python3 scripts/validate_all.py</code>.</p>
</div>
""",
            "provenance",
        ),
    )
    print(f"built {len(list(SITE.rglob('*.html')))} HTML pages in {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
