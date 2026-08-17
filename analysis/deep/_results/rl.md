# RL family — verified measured results (model-free & model-based on the gridworld)

Testbed: the same 9×9 gridworld (goal (0,8), −50 pit (4,4), 8 walls, step −1), but now the
agent does NOT know the rewards or where moves lead — it learns by trying. Start (8,0), optimal
path = 16 steps. Fixed seed. Script: scripts/experiments/rl_run.py. Cite numbers verbatim.

## EXP1 — learning from reward alone (concepts: reinforcement-learning, value-based-rl)
- Q-learning (keeps a running score for each move in each cell, nudged toward reward + slightly-
  discounted best next score). ε=0.1 (tries a random move 10% of the time).
- First episode it reaches the goal: **episode 3**.
- Success rate: episodes 1–100 = **88%**; episodes 500–600 = **100%**.
- Average steps to goal, episodes 500–600 = **18.0** (optimal is 16 — nearly optimal).
- reinforcement-learning angle: the reward signal is the ONLY teacher; no one labels the right move.
- value-based-rl angle: it never stores "the plan" — it stores a number per move, and acts by
  picking the highest-scoring move. The plan is implied by the scores.

## EXP2 — exploration: pure greedy locks onto the nearby crumb (concept: exploration)
- A 6-spot corridor. Start in the middle. Two steps left = a small **+1** exit; four steps right
  = a big **+10** exit.
- Greedy policy after training reaches the big +10 exit?
  - ε=0.0 → **False** (found the +10 during training in 0/200 episodes)
  - ε=0.1 → **False** (0/200)
  - ε=0.3 → **True** (found it in 120/200 episodes)
- Insight: an agent that always takes its current best guess walks to the near +1 and never even
  sees the +10. Only enough random trying (30%) uncovers the better exit. Too little exploration
  misses it just like none.

## EXP3 — reward hacking: a proxy bonus gets gamed (concept: reward)
- We added a well-meant +3 bonus for entering a "charge" cell near the start, hoping to guide the agent.
- Trained greedy rollout: reaches goal = **False**; it re-enters the charge cell **200 times** (the
  whole 200-step budget), never finishing.
- Insight: the agent optimizes exactly what you wrote down, not what you meant. A helper bonus with
  a loophole becomes the whole behavior — it farms the +3 forever instead of reaching the goal.

## EXP4 — model-based RL is far more sample-efficient (concept: model-based-rl)
- Instead of learning by trial, first WATCH: take random steps, remember "from here, that move led
  there and paid this," then plan a route on the remembered map.
- Random real steps → moves learned → does the planned route reach the goal?
  - 200 steps → 97 of 284 moves → **False**
  - 500 steps → 170 of 284 → **False**
  - 1000 steps → 244 of 284 → **True**
  - 2000 steps → 277 of 284 → **True**
- Insight: once the map is mostly known (~1000 remembered steps), one round of planning finds the
  goal. Plain Q-learning backs up only ONE move per real step, so it needs far more trial and error.
  Remembering and reusing beats blind repetition.

## EXP5 — policy optimization sharpens a probability (concepts: policy-optimization, policy)
- A tiny corridor. The agent's rule is a set of move-probabilities per spot (a "policy"). Start it
  at 50/50. After each try, it nudges the probabilities of the moves that paid off upward.
- Probability of stepping toward the goal at the start spot: **0.50 (random) → 0.88 (trained)**.
- policy angle: a policy is just the current rule — here a set of odds for each move — not a fixed
  script; it can be sharp (almost always one move) or soft (spread across moves).
- policy-optimization angle: you improve the SAME rule directly by pushing up whatever led to reward,
  instead of building a full table of scores first.
