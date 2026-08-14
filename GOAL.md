# End-To-End Goal

Build Stanford AA203 Optimal and Learning-Based Control into a transcript-backed, first-principles course companion with the same depth standard as the strongest local course sites: Topology & Geometry, Physics-Informed ML, MIT Game Theory, Gravity and Light, and Eigensteve.

The finished site should not be a playlist mirror, transcript dump, or lecture summary. It should help a serious learner understand optimal and learning-based control as one connected way of thinking: choose actions over time, respect dynamics and constraints, account for future cost, replan under uncertainty, and use learning only where model-based reasoning is incomplete or too expensive.

## Reference Richness Target

The quality bar is not "all pages exist." The quality bar is the richer explainer style shown by local reference pages such as:

- `http://127.0.0.1:8050/vt-explained.html`
- `http://127.0.0.1:8050/the-machine.html`

Those pages work because they teach from first principles in plain everyday language. They do not start with vocabulary. They start with a real failure in the world, show why the simple idea breaks, introduce the mathematical object only after the need is felt, show the operation on that object, give a concrete run, and then expose the math one level deeper.

AA203 must reach that standard. A reviewer should feel that each page was written by someone trying to teach the idea to a serious learner at a whiteboard, not by someone filling a template.

Every major page should have:

- A short, forceful thesis in ordinary words.
- A concrete physical or decision problem before any formal name.
- A "what breaks" paragraph that makes the naive approach visibly fail.
- A named mathematical object introduced as the thing that carries the burden.
- A plain-language operation: what gets updated, minimized, propagated, priced, constrained, sampled, or replanned.
- A worked run with concrete quantities, time steps, states, actions, constraints, or failure signals.
- A collapsible or separated "actual math, one level deeper" explanation for readers ready for symbols.
- A failure boundary that tells the learner where the method should not be trusted.
- Links into transcript evidence without pretending the transcript proves synthesis it does not prove.

The site should avoid cliche, vague praise, and decorative jargon. Do not write:

- "This is important."
- "This is useful."
- "This improves performance."
- "This captures the objective."
- "This method optimizes the system."
- "This is a powerful framework."
- "This enables better control."

Write instead:

- Which state changes.
- Which action is available.
- Which future consequence is being priced.
- Which rule moves the state forward.
- Which constraint can be violated.
- Which approximation makes the computation small enough.
- Which real failure the learner would see if the assumption is false.

Use course vocabulary only after the everyday problem is already clear. Words such as value function, Hamiltonian, costate, collocation, recursive feasibility, policy gradient, and model-based RL should arrive as names for objects the learner already needs, not as labels dropped first.

## Source Backbone

Preserve the full AA203 source layer before deep synthesis.

- Keep `raw-material/youtube/course-manifest.json` as the canonical course definition.
- Capture captions, cleaned transcripts, and word counts for all 19 lectures.
- Keep raw VTT files separate from cleaned text.
- Maintain `raw-material/youtube/transcript-index.json` as the audit source for transcript availability.
- Maintain complete caption coverage for all 19 lectures, including Lecture 13.
- Never write a concept claim as transcript-backed unless it has a lecture, timestamp or local transcript window, and a clear statement of what the transcript actually supports.

## Course Thesis

The site should make this thesis legible across every page:

Optimal control is the discipline of choosing actions whose consequences unfold through time. Learning-based control extends that discipline when the model, cost, environment, or feedback signal cannot be fully written down in advance. The central tradeoff is not "optimization versus learning." It is how much structure to trust, how much to compute, how much to replan, and how much to learn from data while still protecting feasibility, stability, and decision quality.

## Reader Promise

A learner who finishes the site should be able to:

- Recognize a control problem in ordinary language before seeing equations.
- Name the state, action, dynamics, objective, horizon, constraints, and uncertainty in a new problem.
- Explain why optimizing one action at a time is not enough when actions change future states.
- Derive the need for value functions and Bellman recursion from future consequence accounting.
- Explain the difference between indirect methods, direct methods, dynamic programming, MPC, imitation learning, and RL as different responses to the same action-over-time pressure.
- Read core formulas as operations on a problem, not as symbols to memorize.
- Diagnose when a method fails because of bad modeling, bad discretization, infeasible constraints, poor exploration, distribution shift, or a broken reward signal.

## Required HTML Surfaces

The finished `site/` should include at least these reader-facing pages:

- `index.html`: course thesis, source counts, strongest entry points, and review state.
- `lectures.html`: one card per lecture with the lecture problem, main move, concept links, and transcript support.
- `transcripts.html`: transcript availability, word counts, source links, and missing-caption status.
- `concepts.html`: complete concept atlas.
- `concepts/<concept>.html`: individual first-principles concept pages.
- `course-spine.html`: one coherent path from course overview to model-based RL.
- `families.html`: method families such as trajectory optimization, dynamic programming, MPC, and learning-based control.
- `primitives.html`: reusable mathematical primitives: state, action, dynamics, cost, constraint, gradient, value, policy, uncertainty, feasibility.
- `formula-reader.html`: formulas translated into problem, object, operation, assumption, and failure test.
- `derivations.html`: slow derivations for Bellman recursion, costates, LQR local quadratic reasoning, direct transcription, MPC replanning, value learning, and policy gradients.
- `worked-examples.html`: concrete examples from rockets, robotic arms, autonomous cars, option pricing, macroeconomics, and robot learning.
- `drills.html`: learner practice problems with recognition, setup, method choice, and failure diagnosis.
- `solutions.html`: full worked solutions for the drills.
- `misconceptions.html`: false pictures and repairs.
- `evidence.html`: transcript-backed evidence ledger.
- `review-guide.html`: reviewer path through strongest and riskiest pages.
- `quality.html`: editorial quality rubric.
- `completion-audit.html`: proof that required artifacts exist and link correctly.
- `provenance.html`: source, extraction, build, and reproduction instructions.

## Concept Atlas Minimum

The concept atlas should cover at least:

- Optimal control problem
- State
- Action / control input
- Dynamics
- Objective / cost function
- Horizon
- Constraints
- Feasibility
- Static optimization
- Gradient and first-order condition
- Calculus of variations
- Costate / adjoint variable
- Hamiltonian for optimal control
- Indirect methods
- Direct transcription
- Shooting methods
- Collocation
- Trajectory optimization
- Dynamic programming
- Value function
- Bellman recursion
- Stochastic dynamic programming
- LQR
- Local quadratic approximation
- Reachability
- Model predictive control
- Recursive feasibility
- Stability under replanning
- Imitation learning
- Behavioral cloning
- Distribution shift in imitation
- Reinforcement learning
- Reward
- Policy
- Value-based RL
- Policy optimization
- Exploration
- Model-based RL

Each concept page must include:

- The ordinary problem that forces the concept to exist.
- The naive approach and why it fails.
- The mathematical object introduced.
- The operation performed on that object.
- A concrete worked run, preferably with numbers, time steps, state/action values, constraints, or a visible failure.
- A one-level-deeper math block that explains the symbols as operations.
- The assumption boundary.
- A failure mode.
- Transcript-backed evidence.
- A "recognize this in a new problem" diagnostic.
- Links to prerequisite and downstream concepts.

Core concept pages should not be short cards. They should read as compact essays with the same progression as the reference pages:

1. The physical or decision problem.
2. The tempting shortcut.
3. Why that shortcut fails.
4. The mathematical object.
5. The operation.
6. One concrete run.
7. The actual math, one level deeper.
8. Where it fails.
9. Transcript evidence.

At minimum, these pages must receive especially rich treatment:

- `concepts/optimal-control-problem.html`
- `concepts/state.html`
- `concepts/action-control-input.html`
- `concepts/dynamics.html`
- `concepts/objective-cost-function.html`
- `concepts/value-function.html`
- `concepts/bellman-recursion.html`
- `concepts/direct-transcription.html`
- `concepts/lqr.html`
- `concepts/reachability.html`
- `concepts/model-predictive-control.html`
- `concepts/imitation-learning.html`
- `concepts/reinforcement-learning.html`
- `concepts/model-based-rl.html`

## Evidence Standard

Evidence records should be useful, not decorative.

Each evidence record must include:

- Lecture number and title.
- Video id and source URL.
- Timestamp or local transcript window.
- Transcript excerpt or compact local window.
- Supported concepts.
- What the transcript directly supports.
- What the site is synthesizing beyond the transcript.
- Confidence status: `manual_deepened`, `needs_review`, or `discarded`.

Do not let keyword matches become evidence. A timestamp is not enough; the record must identify the lecture argument.

## Writing Standard

The writing must start from control problems, not formal vocabulary.

A strong sentence says what is being controlled, what future consequence matters, what information is missing or expensive, what mathematical object carries that burden, and what breaks if the method is used outside its assumptions.

Avoid filler such as:

- "This is important for control."
- "This improves performance."
- "This captures the objective."
- "This is useful in robotics."
- "The method optimizes the system."

Replace those with concrete statements:

- What state is changing?
- What action is being chosen?
- What future cost is being traded off?
- What constraint must not be violated?
- What approximation makes the computation possible?
- What failure would a practitioner see?

## Practice Standard

The finished site should train recognition and transfer, not only reading.

Include drills that ask the learner to:

- Convert a real scenario into state, action, dynamics, cost, and constraints.
- Choose between direct transcription, dynamic programming, MPC, imitation learning, and RL.
- Identify when Bellman recursion is the right move.
- Spot infeasible MPC setups.
- Diagnose reward hacking and distribution shift.
- Explain why a local LQR approximation is reasonable or unsafe.
- Repair weak explanations into first-principles explanations.

Every drill should have a full solution that names the wrong turns, not just the final answer.

## Page-Level Richness Standard

The required HTML surfaces should not be shallow indexes.

- `index.html` should introduce the course as one live problem: how to choose actions whose consequences arrive later.
- `course-spine.html` should read like a guided essay through the course, with each move tied to a concrete example.
- `lectures.html` should explain what problem each lecture adds to the course, not only list video metadata.
- `families.html` should compare method families by what pressure forced them to exist: path choice, future pricing, local feedback, replanning, demonstration, reward, or model learning.
- `primitives.html` should teach state, action, dynamics, cost, constraint, value, policy, uncertainty, and feasibility as reusable objects in everyday control stories.
- `formula-reader.html` should make every formula readable as an operation on a state, action, future cost, or constraint.
- `derivations.html` should be slow enough that a learner can see why the equation appears.
- `worked-examples.html` should include concrete quantities or at least precise state/action/cost/constraint choices.
- `drills.html` and `solutions.html` should train transfer. Solutions must explain the wrong answer, not only provide the right one.
- `misconceptions.html` should repair weak sentences into first-principles explanations.
- `evidence.html` should keep transcript evidence honest and useful.

## Audit And Validation

The repo should have scripts that prove the site is structurally coherent.

Validation should check:

- All required HTML pages exist.
- All local links resolve.
- Every concept has required fields.
- Every concept has at least one evidence record.
- Every evidence record points to an existing transcript.
- Every lecture appears in the lecture index.
- Every transcript-backed claim declares its evidence basis.
- The completion audit matches local artifact counts.
- Richness gates for core pages: minimum prose depth, required explainer sections, worked-run blocks, math-deeper blocks, and failure-boundary blocks.
- Forbidden vague phrases and cliches do not appear in generated pages.
- Core concept pages contain concrete nouns from the domain, such as car, drone, rocket, robot arm, rover, shelf, wall, traffic, fuel, thrust, torque, velocity, battery, disturbance, or reward, rather than only abstract control words.

The final handoff should include:

- transcript coverage count,
- concept count,
- evidence count,
- HTML page count,
- known source gaps,
- validation commands,
- latest git commit,
- and remaining editorial gaps.

## Completion Definition

This goal is complete when a reviewer can open `site/index.html`, follow a coherent route through the course, inspect transcript evidence, study concepts from first principles, practice with drills, check solutions, and verify through audit pages that the package is locally reproducible.

It is not complete merely because the validator passes. It is complete only when the main pages feel comparable in richness and clarity to `vt-explained.html` and `the-machine.html`: first-principles, concrete, simple, non-cliche, low-jargon, and deep enough that a learner can transfer the ideas to a new control problem.
