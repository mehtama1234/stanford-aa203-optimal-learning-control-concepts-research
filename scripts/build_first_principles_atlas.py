#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw-material/youtube"
ANALYSIS = ROOT / "analysis"
CONCEPT_DIR = ANALYSIS / "concepts"
EVIDENCE_DIR = ANALYSIS / "evidence"
THROUGHLINE_DIR = ANALYSIS / "throughlines"


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def words(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text)


def compact_repeated_tokens(text: str) -> str:
    tokens = text.split()
    changed = True
    while changed:
        changed = False
        out: list[str] = []
        i = 0
        while i < len(tokens):
            removed = False
            for size in range(min(10, (len(tokens) - i) // 2), 0, -1):
                if tokens[i : i + size] == tokens[i + size : i + 2 * size]:
                    out.extend(tokens[i : i + size])
                    i += 2 * size
                    changed = True
                    removed = True
                    break
            if not removed:
                out.append(tokens[i])
                i += 1
        tokens = out
    return " ".join(tokens)


def sentence_window(text: str, pattern: str, radius: int = 42) -> str:
    tokens = words(text)
    joined = " ".join(tokens)
    match = re.search(pattern, joined, re.I)
    if not match:
        return compact_repeated_tokens(" ".join(tokens[: min(len(tokens), radius * 2)]))
    prefix = joined[: match.start()]
    start_word = len(words(prefix))
    lo = max(0, start_word - radius)
    hi = min(len(tokens), start_word + radius)
    return compact_repeated_tokens(" ".join(tokens[lo:hi]))


def clean_caption_line(line: str) -> str:
    line = re.sub(r"<[^>]+>", "", line)
    line = line.replace("&amp;", "&").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", line).strip()


def seconds_from_timestamp(value: str) -> int:
    match = re.match(r"(?:(\d+):)?(\d+):(\d+)\.(\d+)", value)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    return hours * 3600 + minutes * 60 + seconds


def parse_vtt_cues(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    cues: list[dict[str, str]] = []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "-->" not in line:
            i += 1
            continue
        start, rest = line.split("-->", 1)
        end = rest.strip().split()[0]
        i += 1
        text_lines: list[str] = []
        while i < len(lines) and lines[i].strip():
            cleaned = clean_caption_line(lines[i])
            if cleaned:
                text_lines.append(cleaned)
            i += 1
        text = " ".join(text_lines).strip()
        if text:
            cues.append({"start": start.strip(), "end": end.strip(), "text": text})
        i += 1
    deduped: list[dict[str, str]] = []
    for cue in cues:
        if not deduped or deduped[-1]["text"] != cue["text"]:
            deduped.append(cue)
    return deduped


def cue_window(row: dict[str, Any], pattern: str, radius: int = 2) -> dict[str, Any] | None:
    raw_path = row.get("raw_vtt")
    if not raw_path:
        return None
    cues = parse_vtt_cues(ROOT / raw_path)
    if not cues:
        return None
    for index, cue in enumerate(cues):
        if re.search(pattern, cue["text"], re.I):
            lo = max(0, index - radius)
            hi = min(len(cues), index + radius + 1)
            selected = cues[lo:hi]
            return {
                "timestamp_start": selected[0]["start"],
                "timestamp_end": selected[-1]["end"],
                "timestamp_seconds": seconds_from_timestamp(selected[0]["start"]),
                "local_transcript_window": compact_repeated_tokens(" ".join(item["text"] for item in selected)),
            }
    return None


def load_transcripts(index: dict[str, Any]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for row in index["records"]:
        if not row.get("transcript_available"):
            continue
        path = ROOT / row["clean_text"]
        out[row["lecture"]] = {**row, "text": path.read_text(encoding="utf-8")}
    return out


def find_evidence_transcript(
    preferred: dict[str, Any] | None,
    transcripts: dict[int, dict[str, Any]],
    pattern: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if preferred:
        cue = cue_window(preferred, pattern)
        if cue:
            return preferred, cue
    for candidate in transcripts.values():
        cue = cue_window(candidate, pattern)
        if cue:
            return candidate, cue
    return preferred, None


CONCEPTS: list[dict[str, Any]] = [
    {
        "id": "optimal-control-problem",
        "name": "Optimal Control Problem",
        "lecture": 1,
        "keywords": ["optimal control", "dynamics", "cost"],
        "family": "problem setup",
        "plain_language_definition": "A problem where you choose actions over time so a moving system reaches a better future without violating the rules.",
        "ordinary_problem": "A rocket, car, arm, portfolio, or economy does not respond only once. Each action changes the next situation, so the planner must judge a whole chain of consequences.",
        "naive_approach": "Pick the action that looks best right now.",
        "why_naive_fails": "A locally attractive action can make the later state expensive, unsafe, or impossible to recover from.",
        "mathematical_object": "A state, a control input, dynamics, a cost, constraints, and a horizon.",
        "operation": "Search over action sequences while propagating the state forward and adding future cost.",
        "worked_example": "For a landing rocket, throttling hard now may reduce height error but waste fuel and leave too little authority near touchdown.",
        "assumption_boundary": "The setup only says what should be optimized if the state, dynamics, cost, and constraints have been named correctly.",
        "failure_mode": "The controller can satisfy the written objective while missing the real mission, such as saving fuel while arriving too fast.",
        "recognition_test": "If today&apos;s action changes tomorrow&apos;s choices, write it as an optimal control problem before choosing a solver.",
    },
    {
        "id": "state",
        "name": "State",
        "lecture": 1,
        "keywords": ["state", "states"],
        "family": "problem setup",
        "plain_language_definition": "The information carried forward because it is enough to predict what the system can do next.",
        "ordinary_problem": "A controller cannot remember every past detail, but it needs the pieces of the present that determine future motion.",
        "naive_approach": "Store whatever measurements are available.",
        "why_naive_fails": "Some measurements are redundant, while missing velocity, battery charge, or contact mode can make the same position require different actions.",
        "mathematical_object": "A state vector or structured state description.",
        "operation": "Update the state through the dynamics after each action.",
        "worked_example": "A car&apos;s lane position is not enough; speed and heading decide whether a steering command is safe.",
        "assumption_boundary": "The chosen state must contain the information needed by the dynamics and cost.",
        "failure_mode": "A controller built on an incomplete state may take identical actions in situations that are physically different.",
        "recognition_test": "Ask what must be known now to predict the effect of the next action.",
    },
    {
        "id": "action-control-input",
        "name": "Action / Control Input",
        "lecture": 1,
        "keywords": ["control", "input", "action"],
        "family": "problem setup",
        "plain_language_definition": "The choice the controller is allowed to make at a particular moment.",
        "ordinary_problem": "A planner needs to know which knobs it can turn: thrust, steering, torque, investment, braking, or a robot joint command.",
        "naive_approach": "Treat every desired change as directly selectable.",
        "why_naive_fails": "A robot cannot choose its next position directly if motors only supply torques under limits.",
        "mathematical_object": "A control input, action, or policy output.",
        "operation": "Choose the input and feed it through the system dynamics.",
        "worked_example": "A drone can command rotor thrust, not instant position; the position changes only through acceleration and velocity.",
        "assumption_boundary": "The action set must reflect actuator limits and legal moves.",
        "failure_mode": "The plan asks for a move no actuator can produce.",
        "recognition_test": "Separate what you want the system to do from what command you can actually issue.",
    },
    {
        "id": "dynamics",
        "name": "Dynamics",
        "lecture": 1,
        "keywords": ["dynamics", "dynamic"],
        "family": "problem setup",
        "plain_language_definition": "The rule that says how the current state and action produce the next state.",
        "ordinary_problem": "Actions matter only through how they move the system. The controller needs a rule for that movement.",
        "naive_approach": "Plan as if the action immediately creates the desired result.",
        "why_naive_fails": "Momentum, delay, friction, and coupling can make the result arrive later or in a different direction.",
        "mathematical_object": "A transition equation or differential equation.",
        "operation": "Propagate the state forward one step or through continuous time.",
        "worked_example": "Turning a steering wheel changes heading gradually; the car does not slide sideways to the target lane.",
        "assumption_boundary": "The dynamics must match the time scale and operating region where the controller acts.",
        "failure_mode": "A model mismatch makes a plan look feasible on paper and fail on hardware.",
        "recognition_test": "If an action&apos;s effect depends on current motion, write the dynamics before optimizing.",
    },
    {
        "id": "objective-cost-function",
        "name": "Objective / Cost Function",
        "lecture": 1,
        "keywords": ["cost", "objective", "loss"],
        "family": "problem setup",
        "plain_language_definition": "The scoring rule that says which futures are better or worse.",
        "ordinary_problem": "A controller needs a way to compare a fast route, a smooth route, a safe route, and a cheap route.",
        "naive_approach": "Optimize the most visible target, such as time or distance.",
        "why_naive_fails": "The visible target can hide fuel, safety, wear, comfort, or constraint risk.",
        "mathematical_object": "A stage cost, terminal cost, reward, or objective functional.",
        "operation": "Accumulate cost across the trajectory and choose the action sequence with the best total.",
        "worked_example": "An autonomous car can minimize travel time by tailgating unless the cost also prices safety margin.",
        "assumption_boundary": "The written cost is only as good as the values and tradeoffs it encodes.",
        "failure_mode": "The controller optimizes a proxy and produces behavior the designer did not intend.",
        "recognition_test": "Ask what future mistake the scoring rule would punish.",
    },
    {
        "id": "horizon",
        "name": "Horizon",
        "lecture": 1,
        "keywords": ["horizon", "finite horizon", "infinite horizon"],
        "family": "problem setup",
        "plain_language_definition": "How far into the future the controller is asked to reason.",
        "ordinary_problem": "Planning one second ahead and planning the whole mission are different problems.",
        "naive_approach": "Pick an arbitrary lookahead window.",
        "why_naive_fails": "A short horizon can miss delayed consequences; a long horizon can be too expensive or depend on unreliable forecasts.",
        "mathematical_object": "A finite horizon, infinite horizon, or receding horizon.",
        "operation": "Limit or extend the future cost summed by the optimization.",
        "worked_example": "A car changing lanes must look far enough ahead to avoid a merge conflict, not just avoid the next meter.",
        "assumption_boundary": "The horizon should match the time scale at which consequences become visible.",
        "failure_mode": "The controller repeatedly makes greedy moves because the real cost lies just beyond the horizon.",
        "recognition_test": "Ask when the consequences of a bad action first appear.",
    },
    {
        "id": "constraints",
        "name": "Constraints",
        "lecture": 2,
        "keywords": ["constraint", "constraints"],
        "family": "problem setup",
        "plain_language_definition": "Rules the solution must obey even if breaking them would reduce the written cost.",
        "ordinary_problem": "Physical systems have limits: actuators saturate, obstacles block motion, temperatures must stay bounded, and budgets run out.",
        "naive_approach": "Add a soft penalty and hope the optimizer avoids illegal behavior.",
        "why_naive_fails": "Some violations are not tradeoffs; a robot collision or infeasible thrust command is simply not allowed.",
        "mathematical_object": "Equality and inequality constraints over states, actions, and trajectories.",
        "operation": "Restrict the feasible set before choosing the best point inside it.",
        "worked_example": "A drone path that clips through a wall may have low energy cost but is not a candidate path.",
        "assumption_boundary": "The constraint must describe the actual safety or physical boundary closely enough.",
        "failure_mode": "A controller finds a mathematically cheap path through a forbidden region.",
        "recognition_test": "Ask what the controller is never allowed to do, even to improve the score.",
    },
    {
        "id": "feasibility",
        "name": "Feasibility",
        "lecture": 12,
        "keywords": ["feasibility", "feasible", "infeasible"],
        "family": "problem setup",
        "plain_language_definition": "Whether there exists any action sequence that satisfies the constraints from the current state.",
        "ordinary_problem": "A controller cannot optimize a plan that no physical or legal action can execute.",
        "naive_approach": "Solve for the best plan and check constraints afterward.",
        "why_naive_fails": "If no admissible plan exists, the optimizer&apos;s output is not a plan; it is evidence that the setup is impossible or too tight.",
        "mathematical_object": "A feasible set or recursively feasible set.",
        "operation": "Check whether at least one trajectory obeys all dynamics and constraints.",
        "worked_example": "If a car is too close to a wall at high speed, no braking command may avoid impact within the remaining distance.",
        "assumption_boundary": "Feasibility depends on the current state, constraint model, horizon, and actuator limits.",
        "failure_mode": "An MPC controller repeatedly solves impossible subproblems and returns unstable or emergency behavior.",
        "recognition_test": "Before asking what is optimal, ask whether anything legal remains possible.",
    },
    {
        "id": "static-optimization",
        "name": "Static Optimization",
        "lecture": 2,
        "keywords": ["optimization", "minimize", "maximize"],
        "family": "optimization foundations",
        "plain_language_definition": "Choosing the best point when the decision does not itself unfold through system dynamics.",
        "ordinary_problem": "Many control methods reduce pieces of the course to ordinary optimization subproblems.",
        "naive_approach": "Assume static optimization is the whole control problem.",
        "why_naive_fails": "Control decisions are chained; a good static decision can be bad once future states are included.",
        "mathematical_object": "An objective function and feasible set.",
        "operation": "Search for a point with the smallest cost or largest reward.",
        "worked_example": "Choosing a single throttle setting for fuel use ignores that the rocket&apos;s velocity changes after the throttle is applied.",
        "assumption_boundary": "Static optimization is appropriate only when future dynamics have already been folded into the objective or constraints.",
        "failure_mode": "The solution is optimal for one snapshot and poor over the trajectory.",
        "recognition_test": "If there is no state transition, start with static optimization; if there is, treat it as a component.",
    },
    {
        "id": "gradient-first-order-condition",
        "name": "Gradient and First-Order Condition",
        "lecture": 2,
        "keywords": ["gradient", "first order", "derivative"],
        "family": "optimization foundations",
        "plain_language_definition": "A local test for whether a tiny move can immediately improve the objective.",
        "ordinary_problem": "An optimizer needs a direction that says which small change makes the score better or worse.",
        "naive_approach": "Try random changes until the cost goes down.",
        "why_naive_fails": "Random search wastes structure and becomes expensive in high-dimensional control trajectories.",
        "mathematical_object": "A gradient, derivative, or stationarity condition.",
        "operation": "Differentiate the objective and look for directions of improvement or stationarity.",
        "worked_example": "If increasing steering torque slightly reduces path error but increases actuator cost sharply, the gradient exposes the tradeoff.",
        "assumption_boundary": "Gradient reasoning is local and depends on smoothness and the chosen coordinates.",
        "failure_mode": "The method stops at a local stationary point that is not globally safe or useful.",
        "recognition_test": "Use it when tiny changes to a decision have meaningful, computable effects.",
    },
    {
        "id": "calculus-of-variations",
        "name": "Calculus of Variations",
        "lecture": 3,
        "keywords": ["calculus of variations", "variation", "functional"],
        "family": "trajectory optimization",
        "plain_language_definition": "Optimization where the unknown is an entire curve or trajectory, not a single number.",
        "ordinary_problem": "A controller must choose a path through time, and changing one part of the path changes the total cost.",
        "naive_approach": "Optimize each point on the path independently.",
        "why_naive_fails": "Neighboring points are linked by dynamics and smoothness, so a path must be varied as a connected object.",
        "mathematical_object": "A functional that scores a whole curve.",
        "operation": "Perturb the curve and require that no small admissible perturbation improves the cost.",
        "worked_example": "A robotic arm path is not a pile of unrelated positions; the arm must move continuously with limited velocity and torque.",
        "assumption_boundary": "The approach needs smooth variations and a meaningful path-level cost.",
        "failure_mode": "Ignoring path coupling creates jerky or dynamically impossible motion.",
        "recognition_test": "Use this lens when the decision variable is a function of time.",
    },
    {
        "id": "costate-adjoint-variable",
        "name": "Costate / Adjoint Variable",
        "lecture": 4,
        "keywords": ["costate", "adjoint", "lambda"],
        "family": "trajectory optimization",
        "plain_language_definition": "A shadow quantity that measures how much future cost changes if the state is nudged now.",
        "ordinary_problem": "An early state error matters because it changes every later possibility, but that downstream effect needs to be priced locally.",
        "naive_approach": "Only penalize the state error at the moment it appears.",
        "why_naive_fails": "The same small error can be harmless or disastrous depending on how it propagates into later cost.",
        "mathematical_object": "A costate or adjoint variable evolving backward in time.",
        "operation": "Propagate future sensitivity backward so present actions can be judged by downstream consequences.",
        "worked_example": "Being one meter off course near the start of a spacecraft maneuver may require large later correction, so the costate prices that future burden.",
        "assumption_boundary": "The interpretation depends on the model and differentiability of the trajectory problem.",
        "failure_mode": "The controller underprices early deviations whose cost appears later.",
        "recognition_test": "Look for the variable that tells how valuable or dangerous a state change is because of the future.",
    },
    {
        "id": "hamiltonian-optimal-control",
        "name": "Hamiltonian for Optimal Control",
        "lecture": 4,
        "keywords": ["Hamiltonian", "hamilton"],
        "family": "trajectory optimization",
        "plain_language_definition": "A combined expression that packages immediate cost with how actions move the state into future cost.",
        "ordinary_problem": "An action must be judged both by what it costs now and by how it changes the state that future costs depend on.",
        "naive_approach": "Choose the action with the smallest immediate cost.",
        "why_naive_fails": "The cheap action now can steer the state into an expensive region.",
        "mathematical_object": "The Hamiltonian in an optimal-control necessary condition.",
        "operation": "Combine stage cost, dynamics, and costate sensitivity, then choose controls that satisfy the necessary condition.",
        "worked_example": "A rocket burn costs fuel immediately but may reduce future position error; the Hamiltonian puts both effects in one local calculation.",
        "assumption_boundary": "It gives necessary conditions under model and smoothness assumptions, not automatic global optimality.",
        "failure_mode": "A trajectory satisfies local equations but is not the best or violates practical constraints.",
        "recognition_test": "Use it when a local action must be priced by immediate and future state effects together.",
    },
    {
        "id": "indirect-methods",
        "name": "Indirect Methods",
        "lecture": 4,
        "keywords": ["indirect methods", "necessary conditions"],
        "family": "trajectory optimization",
        "plain_language_definition": "Solve an optimal-control problem by first deriving equations that an optimal trajectory must satisfy.",
        "ordinary_problem": "Instead of searching over all paths directly, use mathematical structure to reduce the search to conditions of optimality.",
        "naive_approach": "Discretize everything immediately and hand the whole problem to a numerical optimizer.",
        "why_naive_fails": "Direct search can be large and blind to useful analytic structure.",
        "mathematical_object": "Necessary conditions such as state, costate, and stationarity equations.",
        "operation": "Derive the boundary-value problem implied by optimality and solve those equations.",
        "worked_example": "For a spacecraft transfer, the indirect method derives equations for both the state path and the shadow price of state errors.",
        "assumption_boundary": "It depends on correct derivation and can be sensitive to boundary guesses.",
        "failure_mode": "The equations are hard to solve numerically or describe only a local candidate.",
        "recognition_test": "Choose this lens when the analytic necessary conditions are central to the method.",
    },
    {
        "id": "direct-transcription",
        "name": "Direct Transcription",
        "lecture": 6,
        "keywords": ["direct transcription", "transcription", "direct method"],
        "family": "trajectory optimization",
        "plain_language_definition": "Turn a continuous trajectory problem into a finite optimization problem over many time-grid variables.",
        "ordinary_problem": "A computer cannot optimize over infinitely many points of a curve, so the curve must be represented by a finite set of decision variables.",
        "naive_approach": "Optimize only the start and end points.",
        "why_naive_fails": "The path between them may violate dynamics, obstacles, or actuator limits.",
        "mathematical_object": "A discretized trajectory with state and action variables at grid points.",
        "operation": "Add constraints that force neighboring grid points to approximate the dynamics.",
        "worked_example": "A robot arm path is represented by joint positions and torques at many time steps, with constraints tying each step to the next.",
        "assumption_boundary": "The discretization must be fine and accurate enough for the motion being planned.",
        "failure_mode": "A coarse grid hides collisions, unstable transitions, or excessive actuator demands.",
        "recognition_test": "Use this when the path is the object and a nonlinear optimizer will solve the finite version.",
    },
    {
        "id": "shooting-methods",
        "name": "Shooting Methods",
        "lecture": 6,
        "keywords": ["shooting", "single shooting", "multiple shooting"],
        "family": "trajectory optimization",
        "plain_language_definition": "Guess controls or missing boundary values, simulate forward, and adjust the guess until the endpoint or constraints match.",
        "ordinary_problem": "A trajectory problem often knows where it starts and what it wants to hit, but the control sequence between them is unknown.",
        "naive_approach": "Guess the whole path without checking how dynamics generate it.",
        "why_naive_fails": "The guessed path may not be reachable from the initial state.",
        "mathematical_object": "A parameterized initial condition or control sequence plus forward simulation.",
        "operation": "Shoot the dynamics forward and optimize the parameters by endpoint error and cost.",
        "worked_example": "Aim a spacecraft burn sequence, simulate where it lands, then adjust the burn parameters.",
        "assumption_boundary": "Forward simulation must be stable enough that small parameter changes are informative.",
        "failure_mode": "Sensitive dynamics make the shot miss wildly or create an ill-conditioned optimization.",
        "recognition_test": "Look for a method that treats simulation as the constraint-enforcing step.",
    },
    {
        "id": "collocation",
        "name": "Collocation",
        "lecture": 6,
        "keywords": ["collocation", "collocate"],
        "family": "trajectory optimization",
        "plain_language_definition": "A direct method that enforces dynamics at selected points along a discretized trajectory.",
        "ordinary_problem": "The optimizer needs a finite way to ensure the path obeys continuous dynamics.",
        "naive_approach": "Check the dynamics only at the endpoints.",
        "why_naive_fails": "A path can look valid at endpoints while bending through impossible motion between them.",
        "mathematical_object": "Collocation points and defect constraints.",
        "operation": "Force the derivative implied by the path representation to match the dynamics at chosen points.",
        "worked_example": "A drone path spline is checked at interior points so acceleration and velocity stay physically consistent.",
        "assumption_boundary": "The polynomial or grid representation must resolve the motion between points.",
        "failure_mode": "Too few collocation points let the optimizer exploit gaps between checks.",
        "recognition_test": "Use it when a continuous trajectory is represented by pieces and dynamics are enforced at sample points.",
    },
    {
        "id": "trajectory-optimization",
        "name": "Trajectory Optimization",
        "lecture": 6,
        "keywords": ["trajectory optimization", "trajectory", "path"],
        "family": "trajectory optimization",
        "plain_language_definition": "Choosing an entire path of states and actions that obeys dynamics while minimizing cost.",
        "ordinary_problem": "Many control tasks are not about one command but about a full motion plan.",
        "naive_approach": "Plan a geometric path first and worry about dynamics later.",
        "why_naive_fails": "A short path may require impossible acceleration, torque, or contact transitions.",
        "mathematical_object": "A state-action trajectory.",
        "operation": "Optimize the path while enforcing dynamics and constraints.",
        "worked_example": "A robotic arm must move around an obstacle without exceeding joint torque or velocity limits.",
        "assumption_boundary": "The optimized model must represent the important dynamics and constraints.",
        "failure_mode": "The trajectory is visually plausible but cannot be executed.",
        "recognition_test": "Use this term when the solution is a whole planned motion, not just a feedback rule.",
    },
    {
        "id": "dynamic-programming",
        "name": "Dynamic Programming",
        "lecture": 7,
        "keywords": ["dynamic programming"],
        "family": "dynamic programming",
        "plain_language_definition": "Solve a time-coupled decision problem by breaking it into state-indexed future-cost subproblems.",
        "ordinary_problem": "A planner needs to know which action is best now, but that depends on the best plan after the next state.",
        "naive_approach": "Enumerate every possible action sequence from the start.",
        "why_naive_fails": "The number of sequences grows explosively with horizon and branching.",
        "mathematical_object": "A value function over states and time.",
        "operation": "Work backward or iterate: combine immediate cost with the best future value after each action.",
        "worked_example": "A grid-world robot chooses a move by adding the step cost to the value of the cell it will reach.",
        "assumption_boundary": "The state must summarize the future-relevant information and the transition model must be usable.",
        "failure_mode": "The state space becomes too large or the model is wrong.",
        "recognition_test": "Use it when the same future subproblem appears after many different action histories.",
    },
    {
        "id": "value-function",
        "name": "Value Function",
        "lecture": 10,
        "keywords": ["optimal value function", "value function"],
        "family": "dynamic programming",
        "plain_language_definition": "A table or function that tells how much future cost remains from each state if decisions are made well.",
        "ordinary_problem": "To choose now, the controller needs a compact price for the future after each possible next state.",
        "naive_approach": "Re-solve the entire future plan from scratch for every possible action.",
        "why_naive_fails": "That repeats the same downstream reasoning and makes planning expensive.",
        "mathematical_object": "A value function V or J.",
        "operation": "Store or approximate the best future cost from each state.",
        "worked_example": "In navigation, a cell near the goal has low value; a cell near a trap has high future cost even if it is nearby.",
        "assumption_boundary": "The value is meaningful only for the state, dynamics, objective, and policy assumptions used to compute it.",
        "failure_mode": "A bad value estimate makes the controller prefer states that are actually costly later.",
        "recognition_test": "Look for the object that converts future planning into a number attached to the current state.",
    },
    {
        "id": "bellman-recursion",
        "name": "Bellman Recursion",
        "lecture": 7,
        "keywords": ["Bellman", "recursion"],
        "family": "dynamic programming",
        "plain_language_definition": "The rule that today's value equals immediate cost plus the best value of the next state.",
        "ordinary_problem": "A controller needs a local equation that accounts for the future without listing every full trajectory.",
        "naive_approach": "Judge actions only by immediate cost.",
        "why_naive_fails": "A cheap action can move the state into a costly future.",
        "mathematical_object": "A recursive equation for the value function.",
        "operation": "For each action, add current cost to the next state's value, then choose the best action.",
        "worked_example": "A car may brake now even if braking costs time because the next state's value is safer.",
        "assumption_boundary": "The recursion depends on a correct state transition and cost decomposition.",
        "failure_mode": "If the state omits hidden variables, the next-state value is not enough.",
        "recognition_test": "Use it when a decision can be split into now plus the best continuation.",
    },
    {
        "id": "stochastic-dynamic-programming",
        "name": "Stochastic Dynamic Programming",
        "lecture": 9,
        "keywords": ["stochastic dynamic programming", "expectation", "random"],
        "family": "dynamic programming",
        "plain_language_definition": "Dynamic programming when the next state is uncertain and future value must be averaged over possible outcomes.",
        "ordinary_problem": "A controller often does not know exactly what will happen after an action because noise, disturbances, or environment changes intervene.",
        "naive_approach": "Plan for the most likely next state only.",
        "why_naive_fails": "Rare but costly outcomes can dominate safety and expected cost.",
        "mathematical_object": "An expected-value Bellman equation.",
        "operation": "Add immediate cost to the expectation of next-state value under the transition distribution.",
        "worked_example": "A delivery robot crossing a wet floor must account for possible slip, not only the nominal wheel motion.",
        "assumption_boundary": "The uncertainty model must describe the relevant randomness.",
        "failure_mode": "The policy is brittle because it ignores low-probability dangerous states.",
        "recognition_test": "Use it when the same action can lead to several next states.",
    },
    {
        "id": "lqr",
        "name": "LQR",
        "lecture": 8,
        "keywords": ["LQR", "linear quadratic"],
        "family": "local structure",
        "plain_language_definition": "A control method for linear dynamics and quadratic costs that produces a structured feedback law.",
        "ordinary_problem": "Near a nominal operating point, the controller needs fast feedback that trades state error against control effort.",
        "naive_approach": "Re-solve a full nonlinear trajectory problem at every tiny deviation.",
        "why_naive_fails": "That is too slow when the system only needs local corrections.",
        "mathematical_object": "Linear dynamics, quadratic cost, Riccati recursion, and feedback gain.",
        "operation": "Use quadratic value structure to compute how the control should respond to state error.",
        "worked_example": "A drone hovering near level flight can use local feedback to correct small position and velocity errors.",
        "assumption_boundary": "The local linear-quadratic approximation must be valid for the deviations seen.",
        "failure_mode": "Large nonlinear motion breaks the local model and the feedback becomes unsafe.",
        "recognition_test": "Look for small deviations around a nominal trajectory with quadratic penalties.",
    },
    {
        "id": "local-quadratic-approximation",
        "name": "Local Quadratic Approximation",
        "lecture": 8,
        "keywords": ["quadratic", "approximate", "linearize"],
        "family": "local structure",
        "plain_language_definition": "Replace a hard problem near a point with a simpler curved bowl that is easier to optimize.",
        "ordinary_problem": "Nonlinear control can be too hard globally, but near a candidate trajectory its local shape may be usable.",
        "naive_approach": "Trust the local approximation everywhere.",
        "why_naive_fails": "A local bowl only describes nearby behavior; far away the real dynamics and cost may bend differently.",
        "mathematical_object": "A Taylor approximation, linearized dynamics, or quadratic cost model.",
        "operation": "Approximate locally, solve the easier problem, and update around a new point.",
        "worked_example": "A walking robot can locally linearize around a planned footstep, but not around a fall.",
        "assumption_boundary": "The update must stay within the region where the approximation is credible.",
        "failure_mode": "The optimizer takes a step that is good for the approximation and bad for the real system.",
        "recognition_test": "Use it when a hard nonlinear problem is solved through repeated local models.",
    },
    {
        "id": "reachability",
        "name": "Reachability",
        "lecture": 10,
        "keywords": ["reachability", "reachable", "reach"],
        "family": "safety and feasibility",
        "plain_language_definition": "The set of states a system can get to, or must avoid, under allowed actions and disturbances.",
        "ordinary_problem": "Before optimizing a path, the controller must know which futures are even possible or unsafe.",
        "naive_approach": "Assume the target is reachable because it is nearby in space.",
        "why_naive_fails": "Dynamics, speed, actuator limits, and disturbances decide reachability, not visual distance alone.",
        "mathematical_object": "A reachable set or backward reachable set.",
        "operation": "Propagate sets through dynamics under allowed actions and possible disturbances.",
        "worked_example": "A fast car near a wall may be physically unable to stop before collision even if the wall is still several meters away.",
        "assumption_boundary": "Reachability depends on a model of dynamics, controls, constraints, and disturbances.",
        "failure_mode": "A safety controller trusts an escape route that the system cannot actually execute.",
        "recognition_test": "Ask whether the state can still reach safety under legal actions.",
    },
    {
        "id": "model-predictive-control",
        "name": "Model Predictive Control",
        "lecture": 11,
        "keywords": ["MPC", "model predictive control", "receding horizon"],
        "family": "replanning",
        "plain_language_definition": "Repeatedly solve a finite-horizon control problem, apply the first action, observe the new state, and solve again.",
        "ordinary_problem": "A controller needs future planning but cannot perfectly trust a long open-loop plan.",
        "naive_approach": "Compute the whole plan once and execute it blindly.",
        "why_naive_fails": "Disturbances and model errors make the real state drift from the planned trajectory.",
        "mathematical_object": "A receding-horizon optimization problem.",
        "operation": "Optimize over a horizon, apply the first control, shift the horizon, and replan.",
        "worked_example": "An autonomous car plans a few seconds ahead, drives the first fraction, then replans after seeing traffic move.",
        "assumption_boundary": "The optimizer must solve fast enough and the horizon/terminal conditions must protect future feasibility.",
        "failure_mode": "The controller makes locally feasible moves that paint it into a corner later.",
        "recognition_test": "Look for repeated short-horizon optimization in a feedback loop.",
    },
    {
        "id": "recursive-feasibility",
        "name": "Recursive Feasibility",
        "lecture": 12,
        "keywords": ["recursive feasibility", "feasibility", "feasible"],
        "family": "replanning",
        "plain_language_definition": "The property that after applying today&apos;s MPC action, tomorrow&apos;s optimization problem is still feasible.",
        "ordinary_problem": "Replanning is only useful if today&apos;s legal move does not leave the controller with no legal move next time.",
        "naive_approach": "Check only that the current MPC problem has a solution.",
        "why_naive_fails": "The first action of a feasible plan can lead to a state where the next problem is infeasible.",
        "mathematical_object": "A recursively feasible set or terminal condition.",
        "operation": "Design the MPC problem so feasibility propagates from one solve to the next.",
        "worked_example": "A car must not enter a narrow lane unless it can still brake or steer safely in the next planning step.",
        "assumption_boundary": "The guarantee depends on model accuracy, constraints, and terminal set design.",
        "failure_mode": "The controller works for a few replans and then hits an infeasible optimization.",
        "recognition_test": "Ask whether solving now preserves the ability to solve later.",
    },
    {
        "id": "stability-under-replanning",
        "name": "Stability Under Replanning",
        "lecture": 12,
        "keywords": ["stability", "stable", "MPC"],
        "family": "replanning",
        "plain_language_definition": "The property that repeated replanning moves the system toward controlled behavior rather than causing drift or oscillation.",
        "ordinary_problem": "A controller can solve every short-horizon problem and still behave badly over many replans.",
        "naive_approach": "Assume repeated optimization automatically stabilizes the system.",
        "why_naive_fails": "Each short plan may postpone hard work or reverse earlier choices.",
        "mathematical_object": "A Lyapunov-like decrease condition, terminal cost, or terminal set.",
        "operation": "Constrain or score the finite-horizon problem so each replan preserves long-run progress.",
        "worked_example": "A quadrotor should not keep making short corrections that reduce immediate error while building velocity oscillations.",
        "assumption_boundary": "Stability claims require conditions beyond mere feasibility.",
        "failure_mode": "The system remains feasible but jitters, diverges, or cycles.",
        "recognition_test": "Ask what prevents the next replan from undoing the current one.",
    },
    {
        "id": "imitation-learning",
        "name": "Imitation Learning",
        "lecture": 15,
        "keywords": ["imitation learning", "imitate", "demonstration"],
        "family": "learning-based control",
        "plain_language_definition": "Learn a policy from demonstrations of someone or something already doing the task.",
        "ordinary_problem": "Sometimes it is easier to show good behavior than to write the reward or model that would produce it.",
        "naive_approach": "Copy the demonstrated action for every observed state.",
        "why_naive_fails": "Small mistakes move the learner into states the demonstrator never showed.",
        "mathematical_object": "A dataset of state-action demonstrations and a learned policy.",
        "operation": "Fit a policy that maps observations or states to demonstrated actions.",
        "worked_example": "A robot learns drawer opening from human teleoperation traces instead of a hand-written contact model.",
        "assumption_boundary": "The demonstration distribution must cover states the learned policy will visit.",
        "failure_mode": "The learned policy drifts off-demo and has no training signal for recovery.",
        "recognition_test": "Use it when examples of good behavior are easier to obtain than a reliable reward or dynamics model.",
    },
    {
        "id": "behavioral-cloning",
        "name": "Behavioral Cloning",
        "lecture": 15,
        "keywords": ["behavioral cloning", "supervised learning", "clone"],
        "family": "learning-based control",
        "plain_language_definition": "The simplest imitation-learning setup: treat expert actions as labels and train a policy by supervised learning.",
        "ordinary_problem": "The learner has examples of what action the expert took in each state and wants to mimic that mapping.",
        "naive_approach": "Assume high supervised accuracy means good closed-loop control.",
        "why_naive_fails": "A small prediction error changes the next state, and errors accumulate because future inputs are policy-generated.",
        "mathematical_object": "A supervised policy model trained on expert state-action pairs.",
        "operation": "Minimize prediction error between policy actions and expert actions.",
        "worked_example": "A lane-following policy trained on expert driving images may fail after drifting slightly toward the lane edge.",
        "assumption_boundary": "The training data must represent the states induced by the learned policy.",
        "failure_mode": "Compounding errors move the policy outside the expert dataset.",
        "recognition_test": "Look for imitation framed as ordinary supervised prediction of expert actions.",
    },
    {
        "id": "distribution-shift-imitation",
        "name": "Distribution Shift in Imitation",
        "lecture": 15,
        "keywords": ["distribution", "shift", "covariate"],
        "family": "learning-based control",
        "plain_language_definition": "The gap between states in the expert dataset and states the learned policy actually visits.",
        "ordinary_problem": "A policy&apos;s own mistakes change the inputs it sees next.",
        "naive_approach": "Evaluate the policy only on held-out expert states.",
        "why_naive_fails": "Closed-loop execution creates new states that were rare or absent in the demonstrations.",
        "mathematical_object": "A state distribution induced by a policy.",
        "operation": "Compare or correct the mismatch between expert data and learner rollouts.",
        "worked_example": "A robot trained only on centered object grasps may fail when its first motion nudges the object aside.",
        "assumption_boundary": "The issue matters most when actions affect future observations.",
        "failure_mode": "Errors compound until the policy reaches states where it has no competent behavior.",
        "recognition_test": "Ask whether the learner will see the same state distribution as the expert data.",
    },
    {
        "id": "reinforcement-learning",
        "name": "Reinforcement Learning",
        "lecture": 16,
        "keywords": ["reinforcement learning", "RL"],
        "family": "learning-based control",
        "plain_language_definition": "Learn a policy through interaction by using reward feedback from actions and their consequences.",
        "ordinary_problem": "The designer may not know the best action labels, but the system can try actions and receive feedback.",
        "naive_approach": "Try actions randomly until reward improves.",
        "why_naive_fails": "Feedback can be delayed, sparse, unsafe, or expensive, so exploration and credit assignment matter.",
        "mathematical_object": "A policy, reward, value function, and transition process.",
        "operation": "Collect experience and update the policy or value estimates to increase expected return.",
        "worked_example": "A robot learns a manipulation strategy by trying motions and improving actions that lead to successful grasps.",
        "assumption_boundary": "RL needs a reward signal and interaction process that match the real task.",
        "failure_mode": "The agent exploits reward loopholes or learns unsafe exploration behavior.",
        "recognition_test": "Use it when behavior is learned from trial, consequence, and reward rather than expert labels alone.",
    },
    {
        "id": "reward",
        "name": "Reward",
        "lecture": 16,
        "keywords": ["reward", "return"],
        "family": "learning-based control",
        "plain_language_definition": "The feedback signal that tells an RL agent which consequences are desirable.",
        "ordinary_problem": "An agent needs a scalar learning signal, but real tasks often have many values: safety, speed, smoothness, cost, and success.",
        "naive_approach": "Reward the easiest measurable outcome.",
        "why_naive_fails": "The agent may maximize the measurement while violating the intended behavior.",
        "mathematical_object": "A reward function and return.",
        "operation": "Accumulate reward over time and update behavior toward higher expected return.",
        "worked_example": "Rewarding a robot only for reaching an object can make it slam into the table unless impact is also penalized.",
        "assumption_boundary": "The reward must align with the real task and safety constraints.",
        "failure_mode": "Reward hacking produces high score and bad behavior.",
        "recognition_test": "Ask what behavior the scalar feedback would encourage if exploited literally.",
    },
    {
        "id": "policy",
        "name": "Policy",
        "lecture": 16,
        "keywords": ["policy", "policies"],
        "family": "learning-based control",
        "plain_language_definition": "A rule that maps what the agent knows about the current situation to an action.",
        "ordinary_problem": "The controller needs a repeatable decision rule, not a separate hand-picked action for every moment.",
        "naive_approach": "Store a fixed action sequence.",
        "why_naive_fails": "Disturbances and uncertainty mean the state may differ from the planned path.",
        "mathematical_object": "A deterministic or stochastic policy.",
        "operation": "Given a state or observation, output an action or action distribution.",
        "worked_example": "A drone policy maps position and velocity errors to thrust commands.",
        "assumption_boundary": "A policy can only react to information available in its input.",
        "failure_mode": "The policy cannot recover from unseen states or missing observations.",
        "recognition_test": "Look for the object that chooses actions during execution.",
    },
    {
        "id": "value-based-rl",
        "name": "Value-Based RL",
        "lecture": 17,
        "keywords": ["value based", "Q learning", "value function"],
        "family": "learning-based control",
        "plain_language_definition": "Learn how good states or state-action pairs are, then choose actions using those learned values.",
        "ordinary_problem": "Instead of directly learning the action rule, the agent can learn a future-return scoreboard.",
        "naive_approach": "Estimate immediate reward only.",
        "why_naive_fails": "The best action may have low immediate reward but lead to high future return.",
        "mathematical_object": "A state-value or action-value function.",
        "operation": "Update value estimates from experience and act greedily or near-greedily with respect to them.",
        "worked_example": "A maze agent learns that moving away from the goal now can be valuable if it avoids a dead end.",
        "assumption_boundary": "The value representation must generalize correctly across the visited state-action space.",
        "failure_mode": "Function approximation error makes the agent overvalue bad actions.",
        "recognition_test": "Look for RL methods where action choice is derived from learned values.",
    },
    {
        "id": "policy-optimization",
        "name": "Policy Optimization",
        "lecture": 18,
        "keywords": ["policy optimization", "policy gradient", "gradient"],
        "family": "learning-based control",
        "plain_language_definition": "Directly adjust policy parameters to improve expected return.",
        "ordinary_problem": "Sometimes it is more practical to tune the decision rule itself than to build a complete value table.",
        "naive_approach": "Change policy parameters blindly and keep lucky improvements.",
        "why_naive_fails": "Random changes are sample-inefficient and can destroy useful behavior.",
        "mathematical_object": "A parameterized policy and objective over expected return.",
        "operation": "Estimate a gradient or improvement direction and update policy parameters.",
        "worked_example": "A robot gait policy is adjusted so parameter changes that increase forward progress become more likely.",
        "assumption_boundary": "Gradient estimates can be noisy and depend on exploration and reward quality.",
        "failure_mode": "The update overfits noisy returns or collapses exploration.",
        "recognition_test": "Use it when the learning rule modifies the policy directly.",
    },
    {
        "id": "exploration",
        "name": "Exploration",
        "lecture": 16,
        "keywords": ["exploration", "explore"],
        "family": "learning-based control",
        "plain_language_definition": "Trying actions to discover consequences the agent does not yet know.",
        "ordinary_problem": "An agent cannot improve only from familiar behavior if better actions have never been tested.",
        "naive_approach": "Always take the action that currently looks best.",
        "why_naive_fails": "Early estimates are wrong or incomplete, so greed locks in mediocre behavior.",
        "mathematical_object": "An exploration strategy or stochastic policy.",
        "operation": "Trade off exploiting known reward against collecting information from uncertain actions.",
        "worked_example": "A robot may need to try a different grasp angle to learn that it is more reliable.",
        "assumption_boundary": "Exploration must respect safety and data-collection cost.",
        "failure_mode": "Unsafe exploration damages hardware or learns from unrepresentative trials.",
        "recognition_test": "Ask what the learner must try before it can know which action is best.",
    },
    {
        "id": "model-based-rl",
        "name": "Model-Based RL",
        "lecture": 19,
        "keywords": ["model based", "model-based", "learned model"],
        "family": "learning-based control",
        "plain_language_definition": "Learn or use a model of the environment so the agent can plan, simulate, or improve from imagined consequences.",
        "ordinary_problem": "Real interaction can be expensive, so the agent benefits from predicting what actions would do before trying all of them.",
        "naive_approach": "Learn only from real trial-and-error.",
        "why_naive_fails": "Hardware, safety, and sample cost can make pure trial-and-error impractical.",
        "mathematical_object": "A learned transition model, planner, and policy or value update.",
        "operation": "Use the model to simulate futures, plan actions, or generate training targets.",
        "worked_example": "A robot learns a dynamics model from limited pushes and uses it to plan a manipulation sequence before executing.",
        "assumption_boundary": "The learned model must be accurate enough in the states used for planning.",
        "failure_mode": "The planner exploits model errors and chooses actions that work only in simulation.",
        "recognition_test": "Look for RL that learns or uses a predictive model rather than relying only on direct experience.",
    },
]


PRIMITIVES = [
    {
        "id": "state",
        "name": "State",
        "plain_language": "The compact description carried forward because it decides what can happen next.",
        "used_by": ["state", "dynamics", "value-function", "policy", "reachability"],
    },
    {
        "id": "action",
        "name": "Action",
        "plain_language": "The move the controller can legally choose.",
        "used_by": ["action-control-input", "optimal-control-problem", "policy", "reinforcement-learning"],
    },
    {
        "id": "dynamics",
        "name": "Dynamics",
        "plain_language": "The rule that turns state plus action into the next state.",
        "used_by": ["dynamics", "trajectory-optimization", "model-predictive-control", "model-based-rl"],
    },
    {
        "id": "cost",
        "name": "Cost",
        "plain_language": "The future consequence accounting that lets candidate actions be compared.",
        "used_by": ["objective-cost-function", "value-function", "bellman-recursion", "lqr"],
    },
    {
        "id": "constraint",
        "name": "Constraint",
        "plain_language": "A boundary that a solution must obey even when violation would lower cost.",
        "used_by": ["constraints", "feasibility", "recursive-feasibility", "model-predictive-control"],
    },
    {
        "id": "value",
        "name": "Value",
        "plain_language": "A compressed price for the future from a state or action.",
        "used_by": ["value-function", "dynamic-programming", "value-based-rl"],
    },
    {
        "id": "policy",
        "name": "Policy",
        "plain_language": "The rule that selects actions during execution.",
        "used_by": ["policy", "policy-optimization", "imitation-learning", "reinforcement-learning"],
    },
    {
        "id": "uncertainty",
        "name": "Uncertainty",
        "plain_language": "The gap between what the controller expects and what may happen.",
        "used_by": ["stochastic-dynamic-programming", "reachability", "reinforcement-learning", "model-based-rl"],
    },
]

FAMILIES = [
    {
        "id": "problem-setup",
        "name": "Problem Setup",
        "problem": "Name the moving system, legal choices, future score, and limits before choosing a method.",
        "concepts": ["optimal-control-problem", "state", "action-control-input", "dynamics", "objective-cost-function", "horizon", "constraints", "feasibility"],
    },
    {
        "id": "optimization-foundations",
        "name": "Optimization Foundations",
        "problem": "Use local and constrained optimization tools as the base grammar for control.",
        "concepts": ["static-optimization", "gradient-first-order-condition"],
    },
    {
        "id": "trajectory-optimization",
        "name": "Trajectory Optimization",
        "problem": "Choose a whole path while obeying dynamics and constraints.",
        "concepts": ["calculus-of-variations", "costate-adjoint-variable", "hamiltonian-optimal-control", "indirect-methods", "direct-transcription", "shooting-methods", "collocation", "trajectory-optimization"],
    },
    {
        "id": "dynamic-programming",
        "name": "Dynamic Programming",
        "problem": "Compress future consequences into value so decisions can be solved recursively.",
        "concepts": ["dynamic-programming", "value-function", "bellman-recursion", "stochastic-dynamic-programming"],
    },
    {
        "id": "local-structure",
        "name": "Local Structure",
        "problem": "Exploit linear and quadratic approximations when the system stays near a nominal plan.",
        "concepts": ["lqr", "local-quadratic-approximation"],
    },
    {
        "id": "replanning",
        "name": "Replanning and Safety",
        "problem": "Keep solving as the state changes without losing feasibility or stability.",
        "concepts": ["reachability", "model-predictive-control", "recursive-feasibility", "stability-under-replanning"],
    },
    {
        "id": "learning-based-control",
        "name": "Learning-Based Control",
        "problem": "Use data, demonstrations, rewards, or learned models when hand-written structure is incomplete.",
        "concepts": ["imitation-learning", "behavioral-cloning", "distribution-shift-imitation", "reinforcement-learning", "reward", "policy", "value-based-rl", "policy-optimization", "exploration", "model-based-rl"],
    },
]


def concept_text(concept: dict[str, Any]) -> str:
    return " ".join(str(concept.get(key, "")) for key in [
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
    ])


def main() -> int:
    manifest = json.loads((RAW / "course-manifest.json").read_text(encoding="utf-8"))
    transcript_index = json.loads((RAW / "transcript-index.json").read_text(encoding="utf-8"))
    transcripts = load_transcripts(transcript_index)
    manifest_by_lecture = {row["lecture"]: row for row in manifest["videos"]}

    evidence: list[dict[str, Any]] = []
    concepts: list[dict[str, Any]] = []
    for concept in CONCEPTS:
        transcript = transcripts.get(concept["lecture"])
        if not transcript:
            # Fall back to a nearby transcript that has the keyword, while keeping the record honest.
            for candidate in transcripts.values():
                haystack = candidate["text"]
                if any(re.search(re.escape(k), haystack, re.I) for k in concept["keywords"]):
                    transcript = candidate
                    break
        if transcript:
            pattern = "|".join(re.escape(k) for k in concept["keywords"])
            transcript, cue = find_evidence_transcript(transcript, transcripts, pattern)
            clean_window = sentence_window(transcript["text"], pattern)
            window = clean_window if re.search(pattern, clean_window, re.I) else (cue["local_transcript_window"] if cue else clean_window)
            lecture = transcript["lecture"]
            video = manifest_by_lecture[lecture]
            evidence_id = f"ev-{concept['id']}-01"
            timestamp_seconds = cue["timestamp_seconds"] if cue else None
            timestamp_url = (
                f"https://www.youtube.com/watch?v={video['id']}&t={timestamp_seconds}s"
                if timestamp_seconds is not None
                else f"https://www.youtube.com/watch?v={video['id']}"
            )
            evidence.append(
                {
                    "id": evidence_id,
                    "lecture": lecture,
                    "lecture_title": video["title"],
                    "video_id": video["id"],
                    "url": f"https://www.youtube.com/watch?v={video['id']}",
                    "timestamp_url": timestamp_url,
                    "timestamp_start": cue["timestamp_start"] if cue else None,
                    "timestamp_end": cue["timestamp_end"] if cue else None,
                    "timestamp_seconds": timestamp_seconds,
                    "local_transcript": transcript["clean_text"],
                    "raw_vtt": transcript.get("raw_vtt"),
                    "local_transcript_window": window,
                    "supports_concepts": [concept["id"]],
                    "what_transcript_supports": f"The lecture explicitly discusses {concept['name']} or its surrounding method vocabulary in the local window, grounding the concept in the AA203 course arc.",
                    "synthesis_beyond_transcript": "The first-principles prose turns the transcript cue into a learner-facing explanation and still needs manual timestamp-level review.",
                    "confidence_status": "needs_review",
                }
            )
            evidence_ids = [evidence_id]
        else:
            evidence_ids = []

        concepts.append(
            {
                **concept,
                "course_evidence_ids": evidence_ids,
                "word_count": len(words(concept_text(concept))),
            }
        )

    CONCEPT_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    THROUGHLINE_DIR.mkdir(parents=True, exist_ok=True)
    (CONCEPT_DIR / "concept-atlas.json").write_text(json.dumps(concepts, indent=2) + "\n", encoding="utf-8")
    (EVIDENCE_DIR / "evidence-ledger.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (THROUGHLINE_DIR / "primitives.json").write_text(json.dumps(PRIMITIVES, indent=2) + "\n", encoding="utf-8")
    (THROUGHLINE_DIR / "method-families.json").write_text(json.dumps(FAMILIES, indent=2) + "\n", encoding="utf-8")
    print(f"built {len(concepts)} concepts, {len(evidence)} evidence records, {len(FAMILIES)} families, {len(PRIMITIVES)} primitives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
