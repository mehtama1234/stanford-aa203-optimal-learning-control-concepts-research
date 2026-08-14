#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
TEACHING = ANALYSIS / "teaching"


DERIVATIONS: list[dict[str, Any]] = [
    {
        "id": "bellman-recursion",
        "title": "Bellman Recursion From Future Consequence Accounting",
        "problem": "A controller must choose the next action, but the quality of that action depends on the state it creates and all later decisions.",
        "starting_point": "Begin with a state, a set of legal actions, a one-step cost, and a transition rule.",
        "steps": [
            "For each legal action, compute the immediate cost of taking that action now.",
            "Use the dynamics or transition model to identify the next state or distribution over next states.",
            "Attach to that next state the best future cost already assigned by the value function.",
            "Add immediate cost and future value so each action is judged by the same full-future accounting rule.",
            "Choose the action with the smallest combined cost, or largest combined reward in reward notation.",
        ],
        "formula_shape": "V(state) = best over actions of immediate cost plus value(next state).",
        "why_it_works": "The future after the next state is itself a smaller instance of the same problem, so the controller does not need to enumerate every full trajectory from scratch.",
        "failure_test": "If the state does not contain the information needed to predict future consequences, the recursion prices the wrong future.",
        "linked_concepts": ["dynamic-programming", "value-function", "bellman-recursion", "stochastic-dynamic-programming"],
    },
    {
        "id": "costate",
        "title": "Costates As Backward Prices On State Errors",
        "problem": "A small state error now can change later dynamics and later cost, so the controller needs a local price for that downstream effect.",
        "starting_point": "Begin with a trajectory, a path cost, dynamics, and endpoint or path constraints.",
        "steps": [
            "Nudge the state at one time and ask how that nudge changes all later states through the dynamics.",
            "Track how the changed later states alter future cost and terminal cost.",
            "Move that future sensitivity backward through time so it can be attached to the current state.",
            "Use the backward sensitivity together with immediate cost to judge whether a control perturbation helps.",
            "Solve the resulting state, costate, and stationarity equations as necessary conditions for an optimum.",
        ],
        "formula_shape": "Costate evolves backward as the derivative of future cost with respect to state.",
        "why_it_works": "It turns a distributed future consequence into a local signal that can be combined with the current control decision.",
        "failure_test": "If the model is wrong or the optimum is nonsmooth, the backward sensitivity can be misleading or undefined.",
        "linked_concepts": ["calculus-of-variations", "costate-adjoint-variable", "hamiltonian-optimal-control", "indirect-methods"],
    },
    {
        "id": "direct-transcription",
        "title": "Direct Transcription As Finite Path Optimization",
        "problem": "A computer cannot choose infinitely many points of a continuous trajectory, but the path still has to obey dynamics and constraints.",
        "starting_point": "Begin with continuous dynamics, a horizon, state and action limits, and a cost over the path.",
        "steps": [
            "Choose a time grid or collection of collocation points.",
            "Create decision variables for states and actions at those points.",
            "Write constraints that force neighboring points to satisfy an approximation of the dynamics.",
            "Add path constraints, boundary conditions, and the discretized cost.",
            "Solve the resulting finite nonlinear program and then check whether the grid was fine enough.",
        ],
        "formula_shape": "Continuous trajectory problem becomes variables plus defect constraints plus discretized cost.",
        "why_it_works": "The method converts a path problem into a finite optimization problem while keeping dynamics visible as constraints.",
        "failure_test": "A coarse discretization can hide collisions, actuator spikes, or fast dynamics between grid points.",
        "linked_concepts": ["direct-transcription", "collocation", "shooting-methods", "trajectory-optimization"],
    },
    {
        "id": "lqr-local-reasoning",
        "title": "LQR From Local Linear And Quadratic Structure",
        "problem": "Near a nominal state, the controller needs fast feedback without solving a full nonlinear problem at every small deviation.",
        "starting_point": "Begin with dynamics near an operating point and a cost that penalizes state error and control effort.",
        "steps": [
            "Approximate the dynamics locally as a linear map from state and action to next state.",
            "Approximate the cost locally as a quadratic bowl around the desired behavior.",
            "Assume the future value also has a quadratic shape.",
            "Propagate that quadratic value shape backward to compute feedback gains.",
            "Apply the feedback only while the system remains inside the region where the local approximation is credible.",
        ],
        "formula_shape": "Linear dynamics plus quadratic cost gives a quadratic value function and linear feedback.",
        "why_it_works": "The quadratic form stores exactly the curvature needed to trade state error against control effort locally.",
        "failure_test": "Large deviations, saturating actuators, impacts, and contact changes can make the local model false.",
        "linked_concepts": ["lqr", "local-quadratic-approximation", "value-function", "dynamics"],
    },
    {
        "id": "mpc-replanning",
        "title": "MPC As Planning Turned Into Feedback",
        "problem": "A long open-loop plan becomes stale when disturbances, modeling errors, or moving obstacles change the state.",
        "starting_point": "Begin with a model, current state estimate, finite horizon, constraints, cost, and solver fast enough to run repeatedly.",
        "steps": [
            "At the current state, solve a finite-horizon constrained optimal-control problem.",
            "Apply only the first action from the planned sequence.",
            "Measure or estimate the new state after that action.",
            "Shift the horizon forward and solve a new problem from the updated state.",
            "Design terminal costs, terminal sets, or backup policies so repeated replanning preserves feasibility and stability.",
        ],
        "formula_shape": "Solve horizon, apply first action, observe, shift, repeat.",
        "why_it_works": "The optimizer looks ahead, while the repeated solve makes the plan responsive to what actually happened.",
        "failure_test": "A short horizon without terminal structure can make locally good moves that leave no feasible plan later.",
        "linked_concepts": ["model-predictive-control", "recursive-feasibility", "stability-under-replanning", "constraints"],
    },
    {
        "id": "policy-gradient",
        "title": "Policy Gradients As Direct Policy Improvement",
        "problem": "The learner may not have a reliable model or action labels, but can observe returns after executing a parameterized policy.",
        "starting_point": "Begin with a policy, parameters, rollouts, rewards, and an objective that is expected return.",
        "steps": [
            "Run the current policy to generate trajectories and returns.",
            "Estimate which actions or action probabilities were associated with higher return.",
            "Convert that estimate into a direction for changing policy parameters.",
            "Update parameters so actions that led to higher return become more likely in similar states.",
            "Control update size and exploration so noisy returns do not destroy useful behavior.",
        ],
        "formula_shape": "Move policy parameters in the direction that increases expected return.",
        "why_it_works": "It optimizes the decision rule directly when a value table or exact model is not the main object.",
        "failure_test": "Sparse rewards, unsafe exploration, or high-variance estimates can make the update unreliable.",
        "linked_concepts": ["policy-optimization", "policy", "reward", "exploration", "reinforcement-learning"],
    },
]


WORKED_EXAMPLES: list[dict[str, Any]] = [
    {
        "id": "rocket-landing",
        "title": "Rocket Landing",
        "setup": "A vertical rocket must land softly with limited fuel and bounded thrust.",
        "state": "Height, vertical velocity, mass or fuel, and possibly engine state.",
        "action": "Thrust command at each time.",
        "cost": "Terminal landing error, velocity at touchdown, fuel use, and excessive control effort.",
        "constraints": "Thrust limits, no underground states, structural load limits, and safe touchdown velocity.",
        "method_route": "Start with trajectory optimization or direct transcription. Use MPC if disturbances or model mismatch require replanning.",
        "failure_signal": "A plan that saves fuel but reaches the ground too fast reveals a cost or constraint error.",
        "linked_concepts": ["optimal-control-problem", "direct-transcription", "model-predictive-control", "constraints"],
    },
    {
        "id": "robot-arm",
        "title": "Robot Arm Around An Obstacle",
        "setup": "A robot arm must move from one configuration to another without hitting a fixture.",
        "state": "Joint angles and joint velocities.",
        "action": "Joint torques or desired velocity commands.",
        "cost": "Tracking error, motion time, smoothness, and control effort.",
        "constraints": "Joint limits, torque limits, collision constraints, and endpoint requirements.",
        "method_route": "Use trajectory optimization with collocation when the model is trusted; use imitation learning if expert demonstrations are easier than writing the contact-rich objective.",
        "failure_signal": "A visually short path that requires impossible torque shows why geometric planning alone is incomplete.",
        "linked_concepts": ["trajectory-optimization", "collocation", "imitation-learning", "action-control-input"],
    },
    {
        "id": "autonomous-car",
        "title": "Autonomous Car In Traffic",
        "setup": "A car must follow a route while reacting to nearby vehicles and lane constraints.",
        "state": "Position, velocity, heading, lane context, and nearby vehicle estimates.",
        "action": "Steering, acceleration, braking, or higher-level maneuver commands.",
        "cost": "Progress, comfort, lane keeping, safety margin, and control smoothness.",
        "constraints": "Road boundaries, collision avoidance, acceleration limits, and traffic rules.",
        "method_route": "Use MPC for repeated constrained replanning and reachability for safety envelopes.",
        "failure_signal": "A legal plan now that leaves no legal braking or steering option next step is not recursively feasible.",
        "linked_concepts": ["model-predictive-control", "reachability", "recursive-feasibility", "stability-under-replanning"],
    },
    {
        "id": "warehouse-robot-learning",
        "title": "Warehouse Robot Learning",
        "setup": "A mobile manipulator must learn picking behavior across shelves and object poses.",
        "state": "Robot pose, arm state, object pose estimate, gripper state, and local scene features.",
        "action": "Base motion, arm motion, gripper command, or learned policy output.",
        "cost": "Task success, time, collisions, dropped objects, and wear.",
        "constraints": "Shelf geometry, collision constraints, payload limits, and safe exploration boundaries.",
        "method_route": "Use imitation learning for initial behavior, RL for improvement from reward, and model-based RL if real trials are expensive.",
        "failure_signal": "A policy that works on demonstrated centered objects but fails after nudging an object sideways shows distribution shift.",
        "linked_concepts": ["behavioral-cloning", "distribution-shift-imitation", "reinforcement-learning", "model-based-rl"],
    },
    {
        "id": "option-pricing",
        "title": "Option Pricing As Dynamic Decision Accounting",
        "setup": "A financial decision depends on uncertain future prices and choices made over time.",
        "state": "Current price, time, volatility estimate, and portfolio state.",
        "action": "Exercise, hold, hedge, or rebalance decision.",
        "cost": "Expected payoff, risk exposure, transaction cost, and terminal value.",
        "constraints": "Market rules, liquidity, budget, and admissible trading choices.",
        "method_route": "Use dynamic programming or stochastic dynamic programming when future value depends on uncertain transitions.",
        "failure_signal": "A decision rule that ignores rare but high-loss outcomes is a sign that the stochastic model or objective is incomplete.",
        "linked_concepts": ["stochastic-dynamic-programming", "bellman-recursion", "value-function", "policy"],
    },
    {
        "id": "macro-policy",
        "title": "Macroeconomic Policy",
        "setup": "A policy maker chooses interventions whose effects unfold through delayed system dynamics.",
        "state": "Inflation, unemployment, output gap, debt, and expectation summaries.",
        "action": "Interest-rate change, spending decision, or policy lever.",
        "cost": "Inflation deviation, unemployment, volatility, debt burden, and political or welfare loss.",
        "constraints": "Institutional limits, budget constraints, delayed observability, and uncertainty.",
        "method_route": "Use optimal-control framing to expose the state, action, dynamics, and objective before arguing about a policy.",
        "failure_signal": "A one-period improvement that worsens later inflation or debt shows why horizon and dynamics matter.",
        "linked_concepts": ["horizon", "dynamics", "objective-cost-function", "optimal-control-problem"],
    },
]


DRILLS: list[dict[str, Any]] = [
    {
        "id": "drone-delivery-setup",
        "title": "Set Up A Drone Delivery Control Problem",
        "prompt": "A drone must carry a small package across a windy campus and land on a marked pad. Name the state, action, dynamics, cost, constraints, and horizon.",
        "wrong_turn": "Saying only 'minimize delivery time' skips the physical state, legal actions, wind-disturbed dynamics, and safety constraints.",
        "strong_answer": "State includes position, velocity, attitude, battery, and package state. Action is rotor thrust or a lower-level velocity command. Dynamics include motion under wind and gravity. Cost trades time, energy, tracking, and landing accuracy. Constraints include thrust limits, no-fly zones, battery reserve, payload safety, and safe touchdown. The horizon must cover enough time for approach, descent, and landing.",
        "linked_concepts": ["state", "action-control-input", "dynamics", "objective-cost-function", "constraints", "horizon"],
    },
    {
        "id": "warehouse-method-choice",
        "title": "Choose A Method For A Warehouse Robot",
        "prompt": "A robot has a known arm model, cluttered shelves, and thousands of human teleoperation demonstrations. Which methods would you combine and why?",
        "wrong_turn": "Picking only RL ignores the useful known model and the demonstration data.",
        "strong_answer": "Use trajectory optimization or MPC for model-based motion under constraints, imitation learning or behavioral cloning to initialize task behavior from demonstrations, and RL or model-based RL only for improvement where reward feedback and safe exploration are available.",
        "linked_concepts": ["trajectory-optimization", "model-predictive-control", "imitation-learning", "behavioral-cloning", "model-based-rl"],
    },
    {
        "id": "bellman-recognition",
        "title": "Recognize Bellman Structure",
        "prompt": "A rover must choose whether to cross rough terrain now or detour. The rough route is shorter but may damage wheels and reduce future mobility. Explain why this is a Bellman-style decision.",
        "wrong_turn": "Comparing only immediate travel distance misses that the next state changes future options.",
        "strong_answer": "Each action has immediate cost and creates a next state with its own future value. The rough path may look cheap now but can move the rover into a high-cost future state. The Bellman move is to compare immediate cost plus value of the resulting state.",
        "linked_concepts": ["bellman-recursion", "value-function", "dynamic-programming"],
    },
    {
        "id": "mpc-feasibility",
        "title": "Diagnose MPC Feasibility",
        "prompt": "An MPC controller for a car keeps choosing a narrow gap because it is collision-free for the next two seconds, then suddenly becomes infeasible. What is wrong?",
        "wrong_turn": "Saying the optimizer failed misses that the problem formulation may permit a move that destroys future feasibility.",
        "strong_answer": "The horizon or terminal condition is too weak. The current solve is feasible, but applying its first action leads to a state where the next optimization has no legal escape. The design needs recursive-feasibility structure, longer horizon, terminal set, backup policy, or reachability safety check.",
        "linked_concepts": ["model-predictive-control", "recursive-feasibility", "reachability"],
    },
    {
        "id": "reward-hacking",
        "title": "Repair A Reward Function",
        "prompt": "A robot is rewarded for moving an object to a target quickly. It learns to slap the object, often damaging it. What is missing?",
        "wrong_turn": "Adding more training without changing the reward can make the bad behavior more reliable.",
        "strong_answer": "The reward prices target arrival and speed but omits damage, contact force, smoothness, and safety constraints. The repair is to add the missing task values or hard constraints and inspect whether the scalar reward can still be exploited.",
        "linked_concepts": ["reward", "reinforcement-learning", "constraints"],
    },
    {
        "id": "lqr-boundary",
        "title": "Find The Boundary Of LQR Reasoning",
        "prompt": "A controller designed around small deviations from hover is used after a drone clips a branch and tumbles. Why is the LQR explanation no longer enough?",
        "wrong_turn": "Saying LQR is bad misses that it is a local method being used outside its local assumptions.",
        "strong_answer": "LQR relies on local linear dynamics and quadratic cost near the nominal operating point. After impact and tumbling, attitude, actuator limits, and aerodynamics are far from that region. The local approximation no longer prices the real dynamics.",
        "linked_concepts": ["lqr", "local-quadratic-approximation", "dynamics"],
    },
]


REPAIRS: list[dict[str, str]] = [
    {
        "weak": "MPC is useful because it optimizes the system.",
        "diagnosis": "This says nothing about time, feedback, constraints, or why repeated optimization is needed.",
        "strong": "MPC is useful when a controller needs to plan ahead under constraints but cannot trust one long open-loop plan; it repeatedly solves a finite-horizon problem, applies the first action, observes the new state, and replans.",
    },
    {
        "weak": "The value function captures the objective.",
        "diagnosis": "This hides what value actually stores and why it helps decisions.",
        "strong": "The value function stores the best future cost from a state, so the controller can judge a current action by the immediate cost plus the future burden of the state it creates.",
    },
    {
        "weak": "Imitation learning copies expert behavior.",
        "diagnosis": "This misses the closed-loop distribution problem.",
        "strong": "Imitation learning fits a policy from expert demonstrations, but the learned policy can drift into states the expert data did not cover, so action prediction accuracy is not the same as robust control.",
    },
    {
        "weak": "LQR works for robotics because it is efficient.",
        "diagnosis": "Efficiency is not the mathematical reason LQR is appropriate.",
        "strong": "LQR is appropriate near a nominal robotic motion when dynamics can be locally linearized and the cost can be treated as quadratic, giving fast feedback for small deviations while leaving large nonlinear events outside the guarantee.",
    },
    {
        "weak": "Reward tells the agent what to do.",
        "diagnosis": "Reward does not describe behavior directly; it creates incentives that can be exploited.",
        "strong": "Reward is the scalar feedback the agent optimizes over time; if it omits safety, smoothness, or task constraints, the agent can get high return by doing something the designer did not intend.",
    },
]


def main() -> int:
    TEACHING.mkdir(parents=True, exist_ok=True)
    (TEACHING / "derivations.json").write_text(json.dumps(DERIVATIONS, indent=2) + "\n", encoding="utf-8")
    (TEACHING / "worked-examples.json").write_text(json.dumps(WORKED_EXAMPLES, indent=2) + "\n", encoding="utf-8")
    (TEACHING / "drills.json").write_text(json.dumps(DRILLS, indent=2) + "\n", encoding="utf-8")
    (TEACHING / "weak-claim-repairs.json").write_text(json.dumps(REPAIRS, indent=2) + "\n", encoding="utf-8")
    print(
        f"built {len(DERIVATIONS)} derivations, {len(WORKED_EXAMPLES)} examples, "
        f"{len(DRILLS)} drills, {len(REPAIRS)} repairs"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

