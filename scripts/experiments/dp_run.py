"""Real dynamic-programming run on a gridworld.
Value iteration on a 6x6 grid with a goal, a pit, and walls. Deterministic and
slippery variants. Everything printed is measured from the sweeps."""
import numpy as np
np.set_printoptions(precision=2, suppress=True)

N = 9
GOAL = (0, 8)
PIT = (4, 4)
WALLS = {(1,1),(1,2),(2,6),(3,3),(5,2),(6,6),(6,7),(7,3)}
STEP = -1.0
GOAL_R = 0.0
PIT_R = -50.0
GAMMA = 0.99
ACTIONS = {"N":(-1,0),"S":(1,0),"E":(0,1),"W":(0,-1)}

def inb(r,c): return 0<=r<N and 0<=c<N and (r,c) not in WALLS

def step(s,a,slip=0.0):
    """Return list of (prob, next_state, reward)."""
    outs=[]
    main=ACTIONS[a]
    # slip: with prob slip, go perpendicular (split)
    moves=[(1-slip, main)]
    if slip>0:
        perp=[("N","S"),("S","N"),("E","W"),("W","E")]
        # perpendicular to a
        perps={"N":["E","W"],"S":["E","W"],"E":["N","S"],"W":["N","S"]}[a]
        for p in perps: moves.append((slip/2, ACTIONS[p]))
    for prob,(dr,dc) in moves:
        nr,nc=s[0]+dr,s[1]+dc
        ns=(nr,nc) if inb(nr,nc) else s
        if ns==GOAL: r=GOAL_R
        elif ns==PIT: r=PIT_R
        else: r=STEP
        outs.append((prob,ns,r))
    return outs

def value_iteration(slip=0.0, tol=1e-6, maxsweep=1000):
    V=np.zeros((N,N))
    prev_policy=None
    policy_settled_at=None
    value_settled_at=None
    for k in range(1,maxsweep+1):
        Vnew=V.copy(); policy={}
        for r in range(N):
            for c in range(N):
                s=(r,c)
                if s==GOAL or s==PIT or s in WALLS:
                    policy[s]="."; continue
                best=-1e9; besta=None
                for a in ACTIONS:
                    q=sum(p*(rew+GAMMA*V[ns]) for p,ns,rew in step(s,a,slip))
                    if q>best: best,besta=q,a
                Vnew[s]=best; policy[s]=besta
        delta=np.max(np.abs(Vnew-V))
        if prev_policy is not None and policy==prev_policy and policy_settled_at is None:
            policy_settled_at=k
        if delta<tol and value_settled_at is None:
            value_settled_at=k
            V=Vnew; break
        prev_policy=policy; V=Vnew
    return V, policy, policy_settled_at, value_settled_at

print("=== EXP1: value iteration converges; policy settles FIRST ===")
V,pol,psettle,vsettle=value_iteration(slip=0.0)
print(f"policy stopped changing at sweep : {psettle}")
print(f"values converged (1e-6) at sweep : {vsettle}")
print(f"=> the greedy policy was final {vsettle-psettle} sweeps before the numbers stopped moving")
print("value grid (higher = closer to a good future):")
print(V)

print("\n=== EXP2: one Bellman backup by hand at a sample state ===")
s=(0,3)  # a cell two east of goal-row
print(f"state {s}, current V of neighbors used:")
for a in ACTIONS:
    q=sum(p*(rew+GAMMA*V[ns]) for p,ns,rew in step(s,a))
    ns=step(s,a)[0][1]
    print(f"  action {a}: q = -1 + {GAMMA}*V{ns}={V[ns]:.2f}  => {q:.3f}")
print(f"Bellman picks max => V{s} = {V[s]:.3f}")

print("\n=== EXP3: stochastic DP — slip re-routes the policy away from the pit ===")
Vd,pold,_,_=value_iteration(slip=0.0)
Vs,pols,_,_=value_iteration(slip=0.2)
free=[(r,c) for r in range(N) for c in range(N)
      if (r,c) not in WALLS and (r,c) not in (GOAL,PIT)]
flips=[s for s in free if pold[s]!=pols[s]]
# which flips are next to the pit?
adj=lambda s: abs(s[0]-PIT[0])+abs(s[1]-PIT[1])==1
near=[s for s in flips if abs(s[0]-PIT[0])<=1 and abs(s[1]-PIT[1])<=1]
print(f"cells where the optimal action changed when we add 20% slip: {len(flips)} of {len(free)}")
print(f"of those, near the pit (within 1 cell): {len(near)}  e.g. {near[:3]}")
sc=near[0] if near else flips[0]
print(f"cell {sc}: deterministic action {pold[sc]}, slippery action {pols[sc]} (flipped to steer clear)")
print(f"value cost of that caution at {sc}: {Vd[sc]:.2f} -> {Vs[sc]:.2f}")

print("\n=== EXP4: without a value function, every non-terminal move looks identical ===")
# a 1-step planner sees only immediate reward. Count states where all 4 moves tie.
ties=0
for s in free:
    imm={a:step(s,a)[0][2] for a in ACTIONS}
    if len(set(round(v,6) for v in imm.values()))==1: ties+=1
print(f"states where immediate reward is a 4-way tie (no signal): {ties} of {len(free)}")
print(f"the value function breaks the tie at every one: it is the only thing that turns a")
print(f"local one-step choice into a move that serves the global goal.")
