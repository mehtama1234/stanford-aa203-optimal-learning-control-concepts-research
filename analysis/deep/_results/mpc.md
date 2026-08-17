# MPC / safety family — verified measured results (braking cart before a wall)

Testbed: a cart on a line, state = [position, velocity], force limited to [-1, 1], dt=0.2.
A wall sits at position 0; the cart must stop before it. We plan a short list of forces,
apply the first, re-measure, replan. Script: scripts/experiments/mpc_run.py. Cite verbatim.

## EXP1 — feasibility: does ANY safe plan exist right now? (concept: feasibility)
- start 3.0 m before wall, speed 1.0 m/s: shortest possible stopping distance ≈ 0.50 m < 3.0 m
  → **a safe plan EXISTS**.
- start 1.0 m before wall, speed 2.0 m/s: needs ≈ 2.00 m to stop, only 1.0 m left
  → **NO safe plan (infeasible)**.
- start 0.5 m before wall, speed 2.5 m/s: needs ≈ 3.12 m, only 0.5 m left → **infeasible**.
- Insight: feasibility is a yes/no question asked BEFORE "what's cheapest" — is there even one legal
  plan? A cheap-looking path that crosses the wall is not a low-cost plan, it is no plan at all.

## EXP2 — recursive feasibility: a short horizon walks into a trap (concept: recursive-feasibility)
- Same cart starting 3.0 m out, driven by replanning with different look-ahead lengths:
  - look-ahead H=2: **declared stuck (infeasible) at step 11**, final position −0.46 m, still moving +1.88 m/s.
  - look-ahead H=4: **stuck at step 10**, final −0.89 m, still moving +1.64 m/s.
  - look-ahead H=8: **stopped safely**, final 0.00 m, speed 0.00 m/s (40 steps).
- Insight: each short-horizon plan looked fine at the time, so the cart kept racing toward position 0
  (low cost) — until suddenly it was too close and too fast, and NO plan could stop it. Being feasible
  now does not guarantee feasible next. A long-enough horizon (H=8) foresees the stop it will need and
  never enters the trap.

## EXP3 — reachability: which starting speeds can still stop? (concept: reachability)
- Cart 2.0 m before the wall, look-ahead 10:
  - speeds that CAN still stop safely: **0.5, 1.0, 1.5, 2.0 m/s**
  - speeds already doomed (no plan stops in time): **2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0 m/s**
  - the safe/doomed boundary sits **between 2.0 and 2.5 m/s** — the edge of the safe set.
- Insight: from a given spot there is a sharp line between states from which a safe stop is still
  reachable and states already lost. Being close in space is not the same as being able to stop.

## EXP4 — stability under replanning: does the gap actually shrink? (concept: stability-under-replanning)
- Cart 3.0 m out, look-ahead 8, "distance-to-target" (how far from position 0 still) each step:
  steps 0,1,2,3 = **9.0, 8.76, 8.29, 7.62**, reaching **0.0 at step 40**.
- The gap went DOWN (or held) on **40 of 40 steps**.
- Insight: replanning every step is not automatically safe — but with a long enough horizon the
  "how far left" number shrinks steadily every step. That monotone shrink is what "stable" means here:
  steady progress to the goal, no drift, no oscillation.

## For the MPC page itself (concept: model-predictive-control)
- Use EXP2 (H=8 stops safely while H=2/H=4 crash into infeasibility) as the headline: MPC = plan a
  short horizon, apply only the first force, re-measure, replan — and the horizon length is the whole
  game. Pair with EXP4 (40/40 steps of progress) to show the closed loop works.
