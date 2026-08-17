# Problem-setup family — verified measured results (knock out one ingredient at a time)

Testbed: the cart (state = position, velocity), dt=0.1, driven by a full-horizon feedback controller
unless noted. Each experiment removes ONE ingredient of a control problem to show what it did.
Script: scripts/experiments/ps_run.py. Cite numbers verbatim; do NOT invent new ones.

## EXP1 — optimal-control-problem: one greedy step vs planning over time (concept: optimal-control-problem)
- A greedy "fix the error THIS step" controller overshoots to **−1.00 m** and rings, settling in **12.1 s**.
- The planning-ahead controller overshoots only **−0.04 m** and settles in **1.7 s**.
- Insight: an action changes the future (the speed you build up), so choosing one action at a time is
  not enough. Optimizing over the whole time is the reason the field exists.

## EXP2 — state: drop velocity and the same controller can't cope (concept: state)
- Full state [position, velocity]: overshoot **−0.04 m**, settles in **1.7 s**.
- Position only (blind to velocity): overshoot **−3.69 m**, settles in **12.1 s**.
- Insight: the state must carry everything you need to predict what happens next. Without velocity the
  controller can't tell it's about to overshoot, so it rings badly — same cart, same controller.

## EXP3 — action / control input: a real force limit changes what's achievable (concept: action-control-input)
- The controller asks for a peak force of **8.4** at the hard start. Delivered / settling:
  - no limit → delivers 8.36, settles **3.6 s**
  - force capped at 1.0 → delivers 1.00, settles **5.1 s**
  - force capped at 0.3 → delivers 0.30, settles **12.1 s**
- Insight: the action is the real lever, and it has limits. Below a certain force the same start simply
  takes much longer to fix — the plan must respect what the actuator can actually do.

## EXP4 — dynamics: plan with the wrong response and the move is miscalibrated (concept: dynamics)
- Correct model: settles in **1.7 s**. If the real cart delivers only **60%** of each push (the model
  is wrong), the same controller is sluggish and takes **4.1 s** to settle.
- Insight: the dynamics are the bridge from command to motion. Get that bridge wrong and every push is
  miscalibrated — here, far weaker than planned, so the whole move drags out.

## EXP5 — objective / cost function: the weights define what "best" means (concept: objective-cost-function)
- Nothing about the cart changes — only the written price of pushing:
  - cheap pushing (price 0.02): settles **1.2 s**, total effort **65.88**
  - middle (price 0.1): settles **1.7 s**, effort **19.80**
  - expensive pushing (price 2.0): settles **3.6 s**, effort **2.10**
- Insight: "best" is not a property of the cart; it is whatever the objective says. Rewrite the trade-off
  and the optimal behavior changes completely.

## EXP6 — constraints: a speed limit bends the optimal plan (concept: constraints)
- The unconstrained fast plan reaches a peak speed of **2.43 m/s** and settles in **3.6 s**.
- If a speed limit near **1.0 m/s** is required, the plan must slow down: a plan capped near **1.15 m/s**
  settles later, at **7.4 s**.
- Insight: a constraint removes options. The best plan that still obeys it is usually slower or costlier
  than the one that ignores the rule.

## EXP7 — horizon: how far ahead you look decides if you stop in time (concept: horizon)
- A 1-step horizon overshoots to **−1.00 m** (it can't foresee the stop it will need); a full horizon
  eases in with overshoot **−0.04 m**.
- Insight: the horizon is how far into the future the plan reasons. Too short, and the future arrives as
  a surprise you can no longer brake for.
