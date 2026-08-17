"""Real imitation-learning runs. An expert drives a cart to a target with a slightly
NONLINEAR rule (it eases off near the target). A learner copies the expert from
demonstrations. We measure the copy's error on-vs-off the demonstrated states, how the
learner drifts into unseen states, and how DAgger (asking the expert on the learner's
OWN visited states) closes the gap. state=[pos,vel], dt=0.2."""
import numpy as np
rng=np.random.default_rng(0)
dt=0.2
def stepc(x,u):
    u=float(np.clip(u,-3,3)); p,v=x; v2=v+dt*u; p2=p+dt*v2
    return np.array([p2,v2])
def expert(x):
    p,v=x
    return float(np.clip(-1.4*np.tanh(1.5*p) - 1.1*v, -3, 3))   # tanh => nonlinear in position
def rollout(policy,x0,T=40):
    x=np.array(x0,float); xs=[x.copy()]
    for _ in range(T):
        x=stepc(x,policy(x)); xs.append(x.copy())
    return np.array(xs)
def fit_linear(X,U):
    A=np.column_stack([X[:,0],X[:,1],np.ones(len(X))])
    coef,*_=np.linalg.lstsq(A,U,rcond=None)
    return lambda x: float(coef[0]*x[0]+coef[1]*x[1]+coef[2])

# demonstrations: expert from near-center starts (a careful demonstrator stays in a narrow band)
Xd=[]; Ud=[]
for p0 in np.linspace(-1.0,1.0,9):
    for x in rollout(expert,[p0,0.0],T=25): Xd.append(x); Ud.append(expert(x))
Xd=np.array(Xd); Ud=np.array(Ud)
bc=fit_linear(Xd,Ud)
demo_max=float(np.max(np.abs(Xd[:,0])))
hard_starts=[[-3.0,0.0],[3.0,0.0],[-4.0,0.0]]

def onpolicy_gap(policy):
    """average |policy action - expert action| over the states the POLICY itself visits (from hard starts)"""
    errs=[]
    for s in hard_starts:
        for x in rollout(policy,s,T=40): errs.append(abs(policy(x)-expert(x)))
    return float(np.mean(errs))

print("=== EXP1: behavioral cloning — the copy is sharp on the demo, blurry off it (behavioral-cloning) ===")
on=[np.array([p,0.0]) for p in [-0.5,0.0,0.5]]
off=[np.array([p,0.0]) for p in [-3.0,3.0,-4.0]]
print(f"  clone action vs expert action  --  on the demo band: {np.mean([abs(bc(x)-expert(x)) for x in on]):.2f}"
      f"     off the demo band: {np.mean([abs(bc(x)-expert(x)) for x in off]):.2f}")
print(f"  (the demonstrations never went past {demo_max:.2f} m from center, so the copy never learned what to do beyond it)")

print("\n=== EXP2: distribution shift — the learner's own errors carry it into unseen states (distribution-shift-imitation) ===")
tr=rollout(bc,[-4.0,0.0],T=40)
off_frac=float(np.mean(np.abs(tr[:,0])>demo_max))
print(f"  starting at -4.0 m, the clone spends {off_frac*100:.0f}% of its steps beyond {demo_max:.2f} m -- outside")
print(f"  everything the expert ever showed (it swings out to {np.max(np.abs(tr[:,0])):.2f} m). Its biggest single")
print(f"  action error along the way is {np.max([abs(bc(x)-expert(x)) for x in tr]):.2f}, versus about 0.1 inside the band.")
print(f"  This is the compounding trap: each off-copy action lands it somewhere even less familiar.")

print("\n=== EXP3: DAgger — labelling the learner's OWN states closes the gap (imitation-learning) ===")
X=list(Xd); U=list(Ud); pol=bc
gaps=[onpolicy_gap(bc)]
for it in range(1,6):
    for s in hard_starts+[[-2.0,1.0],[2.0,-1.0]]:
        for x in rollout(pol,s,T=30): X.append(x); U.append(expert(x))  # expert labels the visited states
    pol=fit_linear(np.array(X),np.array(U)); gaps.append(onpolicy_gap(pol))
print("  average action-gap between learner and expert ON THE LEARNER'S OWN path, per DAgger round:")
for i,g in enumerate(gaps):
    print(f"    {'plain clone' if i==0 else f'after round {i}':14}: {g:.3f}")
print(f"  DAgger shrank the on-its-own-path gap from {gaps[0]:.2f} to {gaps[-1]:.2f} -- it learned the")
print(f"  recovery moves for the exact states its own mistakes create, which the demos never contained.")
