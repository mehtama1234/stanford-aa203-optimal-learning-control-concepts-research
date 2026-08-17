# Imitation family — verified measured results (cloning an expert cart-driver)

Testbed: a cart (state = position, velocity), dt=0.2. An expert drives it to the target with a
slightly NONLINEAR rule (it eases off near the target). A learner copies the expert from
demonstrations recorded only from near-center starts (the demonstrator stayed within 1.00 m of
center). Script: scripts/experiments/imit_run.py. Cite verbatim.

## EXP1 — behavioral cloning: sharp on the demo, blurry off it (concept: behavioral-cloning)
- The clone is a straight-line fit of the expert's recorded moves.
- Clone's action vs the expert's action: **0.08 on the demonstrated band, 3.72 off it** (~46× worse).
- The demonstrations never went past **1.00 m** from center, so the copy never learned what to do
  beyond it.
- Insight: cloning treats each frame as a labeling task — copy the expert's action for this view.
  It is only trustworthy where the expert actually went; outside that band it is guessing.

## EXP2 — distribution shift: the learner's own errors carry it into unseen states (concept: distribution-shift-imitation)
- Starting at −4.0 m (outside the demo band), the clone spends **20%** of its steps beyond 1.00 m —
  outside everything the expert ever showed — and swings out to **4.00 m**.
- Its biggest single action error along the way is **4.74**, versus about **0.1** inside the band.
- Insight: a small copy error moves the learner somewhere less familiar, where its next action is
  worse, which moves it somewhere less familiar still. The error feeds itself — this compounding is
  the core reason cloning is fragile in a closed loop, and it is NOT visible from one-step accuracy.

## EXP3 — DAgger: label the learner's OWN states and the gap closes (concept: imitation-learning)
- We measure the action-gap between learner and expert ON THE LEARNER'S OWN path (from hard starts).
- Per DAgger round: plain clone **0.498** → after round 1 **0.277** → settling around **0.28–0.31**.
- DAgger roughly **halved** the on-its-own-path gap (0.50 → 0.28) by asking the expert what to do in
  the exact states the learner's mistakes create — states the original demonstrations never contained.
- Insight: imitation learning is not just "watch and copy." The fix is to gather expert labels on the
  states the LEARNER visits, not only the ones the expert liked to visit.

## Framing notes for distinctness
- imitation-learning = the whole idea of learning from demonstrations when a reward is hard to write,
  AND the DAgger fix (EXP3).
- behavioral-cloning = the specific supervised-copy method and why it is sharp on-band, blurry off (EXP1).
- distribution-shift-imitation = the failure mechanism: the learner's own errors move it off the
  demonstrated distribution, where errors compound (EXP2).
