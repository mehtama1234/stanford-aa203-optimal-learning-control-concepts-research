# Trajectory-optimization family — verified measured results (least-effort cart move)

Testbed: move a cart from (position 0, speed 0) to (position 1, speed 0) in fixed time (20 steps,
dt=0.1), using the least total push-effort (sum of squared force). Double integrator.
Script: scripts/experiments/traj_run.py. Cite numbers verbatim; do NOT invent new ones.

## EXP1 — the least-effort whole path (concept: trajectory-optimization)
- Optimizing the ENTIRE push sequence at once: total effort J* = **15.038**.
- A sensible hand plan (push hard, then brake hard — "bang-bang") reaching the same target: J = **20.000**.
- The optimized whole-path plan uses **25% less effort** than the hand plan.
- Insight: a path is not a drawing you sketch and then track; making the whole sequence the decision,
  and letting a solver trade off every step together, beats any locally-sensible hand rule.

## EXP2 — the indirect (optimality-conditions) route agrees with the direct one
##   (concepts: indirect-methods, calculus-of-variations, hamiltonian-optimal-control, costate-adjoint-variable)
- Pontryagin's conditions (the "indirect" route) predict the least-effort push must be a STRAIGHT LINE
  in time. The directly-optimized push sequence fits a straight line with **R² = 1.00000** (1.0 = perfect).
- First-step push = **+1.429**, last-step push = **−1.429** (a mirror image, as the theory says).
- calculus-of-variations angle: you are optimizing over a whole function (the path); the best one is
  where any small wiggle no longer lowers cost — a stationarity condition — and that pins the shape.
- hamiltonian angle: bundle running cost + (a price) × (dynamics) into one quantity H; requiring H be
  smallest in the push at every instant gives push = −(one of the prices).
- costate angle: that "price" is the costate — a backward-in-time sensitivity; here it runs linearly,
  which is exactly why the push is a straight line.
- indirect-methods angle: instead of searching paths, solve the optimality equations directly; the
  R²=1.0 match with the direct optimizer shows the two routes reach the identical answer.

## EXP3 — shooting: guess the launch, measure the miss, correct (concept: shooting-methods)
- Parametrize the push by two unknown launch numbers; simulate forward; measure how far the endpoint
  lands from the target; correct.
- Endpoint miss per iteration: **1.000 → 0.000** — one correction is exact here (the problem is linear;
  a curved problem takes a few iterations).
- Insight: turn a hard "both ends fixed" problem into a repeated "guess a start, see where it lands,
  adjust" loop — like aiming a cannon by watching the shots.

## EXP4 — transcription/collocation defect: a path must obey the physics (concepts: direct-transcription, collocation)
- A hand-drawn path that claims near-zero speed while its position marches 0→1 has a worst "defect"
  (mismatch between the drawing's implied motion and the physics) of **0.500**.
- The optimized path's worst defect is **4.44e-16** — essentially zero: every knot hands the next a
  physically reachable state.
- direct-transcription angle: chop the path into knot points, make the states/pushes the variables,
  and add a defect = 0 constraint between neighbors so the drawing is a real motion.
- collocation angle: enforce that the curve's own slope matches the physics at chosen interior points;
  checking only the endpoints would miss a mid-path violation.

## EXP5 — gradient and the first-order condition (concept: gradient-first-order-condition)
- Minimizing a simple bowl cost by stepping downhill: the gradient (steepness) shrank from **6.00 to
  0.000** over 60 steps, landing at **z = 2.500** — the exact bottom, where the slope is zero.
- Insight: "gradient zero" is the signature of a flat bottom; you step downhill until the ground is level.

## EXP6 — static optimization with an active limit (concept: static-optimization)
- Same bowl, now with a cap z ≤ 1.5. Unconstrained best is z = 2.5 (cost 1.500); the best LEGAL point
  is pinned at the cap, **z = 1.5 (cost 2.700)**.
- The cap is "active": the downhill pull wants 2.5 but the boundary holds it at 1.5.
- Insight: static optimization picks one point, not a path; the answer is either where the ground is
  level, or pressed against a boundary.

## EXP7 — local quadratic approximation: good near, bad far (concept: local-quadratic-approximation)
- Approximating a curved cost by a simple bowl at one point, then checking the error as you move away:
  offset 0.2 → **0.3%** error, 0.5 → **2.1%**, 1.0 → **8.8%**, 2.0 → **41.2%**.
- Insight: the bowl fits almost perfectly close in and drifts badly far out — which is exactly why
  methods that trust it (like iLQR) must keep each step small.
