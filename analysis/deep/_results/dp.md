# DP family — verified measured results (gridworld value iteration)

Testbed: 9×9 gridworld, goal at (0,8), a −50 pit at (4,4), 8 walls, step cost −1,
γ=0.99. Value iteration (synchronous Bellman backups). Script: scripts/experiments/dp_run.py.
Every number below is printed by the run — cite them verbatim; do NOT invent new numbers.

## EXP1 — convergence + policy-settles-first (concept: dynamic-programming)
- Value iteration converged (max value change < 1e-6) at **sweep 16**.
- The greedy policy stopped changing at **sweep 14** — **2 sweeps before** the numbers stopped moving.
- Insight: value iteration is a contraction — each sweep shrinks the error by ≤ γ, so it always
  converges; and the *decisions* freeze before the *values* do. You can act optimally while the
  value estimate is still settling its last decimals.

## EXP2 — one Bellman backup by hand (concept: bellman-recursion)
- At state (0,3), using current neighbor values:
  - N: −1 + 0.99·V(0,3)=−3.94 ⇒ −4.901
  - S: −1 + 0.99·V(1,3)=−4.90 ⇒ −5.852
  - E: −1 + 0.99·V(0,4)=−2.97 ⇒ **−3.940 (max)**
  - W: −1 + 0.99·V(0,2)=−4.90 ⇒ −5.852
- Bellman picks the max ⇒ V(0,3) = −3.940, action E (toward the goal at (0,8)).
- Insight: one backup = immediate reward + γ·(best neighbor value). The whole global plan is
  assembled from this one local rule applied everywhere, repeatedly.

## EXP3 — stochastic DP re-routes the policy (concept: stochastic-dynamic-programming)
- Add 20% slip (perpendicular drift). **20 of 71** free cells change their optimal action.
- **4** of those flips are within one cell of the pit. Example: cell (4,3) flips from action **S**
  (deterministic, hugs the pit edge) to **W** (slippery, steers clear).
- The caution has a measured price: V(4,3) drops from −9.56 to −12.58.
- Insight: replacing the next-state value with its *expected* value (one number) re-routes the
  whole policy away from the −50 cell — the plan buys margin because a slip could be fatal.

## EXP4 — value function is the only tie-breaker (concept: value-function)
- If you look only at immediate reward, **65 of 71** non-terminal states are a 4-way tie (every
  move costs −1, no signal).
- The value function assigns each state a single number (its full future cost if you act well);
  that number breaks the tie at every one of the 65 states.
- Insight: the value function is exactly what turns a local one-step choice into a move that
  serves the distant goal. Without it, almost every cell looks directionless.
- Value grid shape: numbers grow smoothly worse (more negative) with distance from goal —
  V(0,7)=0 at goal edge down to V(8,0)=−13.99 in the far corner.
