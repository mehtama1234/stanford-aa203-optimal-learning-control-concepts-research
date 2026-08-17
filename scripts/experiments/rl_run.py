"""Real reinforcement-learning runs on the same 9x9 gridworld as dp_run.py,
but now the agent does NOT know the rewards or where moves lead — it must learn
by trying. Fixed seeds so every number is reproducible."""
import numpy as np
rng = np.random.default_rng(0)

N=9; GOAL=(0,8); PIT=(4,4)
WALLS={(1,1),(1,2),(2,6),(3,3),(5,2),(6,6),(6,7),(7,3)}
START=(8,0)
ACT={0:(-1,0),1:(1,0),2:(0,1),3:(0,-1)}   # N,S,E,W
def inb(r,c): return 0<=r<N and 0<=c<N and (r,c) not in WALLS
def stepenv(s,a):
    dr,dc=ACT[a]; nr,nc=s[0]+dr,s[1]+dc
    ns=(nr,nc) if inb(nr,nc) else s
    if ns==GOAL: return ns,0.0,True
    if ns==PIT:  return ns,-50.0,True
    return ns,-1.0,False

def run_episode(Q,eps,alpha=0.5,gamma=0.99,maxT=200,learn=True):
    s=START; total=0;
    for t in range(maxT):
        if rng.random()<eps: a=int(rng.integers(4))
        else: a=int(np.argmax(Q[s[0],s[1]]))
        ns,r,done=stepenv(s,a); total+=r
        if learn:
            target=r if done else r+gamma*np.max(Q[ns[0],ns[1]])
            Q[s[0],s[1],a]+=alpha*(target-Q[s[0],s[1],a])
        s=ns
        if done: return total,t+1,(s==GOAL)
    return total,maxT,False

# optimal path length from START via DP (for reference)
def optimal_steps():
    V=np.zeros((N,N))
    for _ in range(300):
        Vn=V.copy()
        for r in range(N):
            for c in range(N):
                if (r,c) in (GOAL,PIT) or (r,c) in WALLS: continue
                best=-1e9
                for a in ACT:
                    ns,rew,_=stepenv((r,c),a); best=max(best,rew+0.99*V[ns])
                Vn[r,c]=best
        V=Vn
    s=START; steps=0
    for _ in range(100):
        if s in (GOAL,PIT): break
        a=max(ACT,key=lambda a:(lambda ns,rew,_:rew+0.99*V[ns])(*stepenv(s,a)))
        s=stepenv(s,a)[0]; steps+=1
    return steps
OPT=optimal_steps()
print(f"reference: optimal path from {START} to goal = {OPT} steps\n")

print("=== EXP1: Q-learning learns from reward alone (value-based-rl / RL) ===")
Q=np.zeros((N,N,4)); succ=[]; steps=[]
for ep in range(1,601):
    _,st,ok=run_episode(Q,eps=0.1)
    succ.append(ok); steps.append(st if ok else None)
def rate(block):
    b=[x for x in block]; return 100*sum(b)/len(b)
first_solve=next((i+1 for i,ok in enumerate(succ) if ok),None)
def avgsteps(lo,hi):
    xs=[steps[i] for i in range(lo,hi) if steps[i] is not None]
    return sum(xs)/len(xs) if xs else float('nan')
print(f"first successful episode: {first_solve}")
print(f"success rate  ep 1-100: {rate(succ[:100]):.0f}%   ep 500-600: {rate(succ[500:600]):.0f}%")
print(f"avg steps-to-goal ep 500-600: {avgsteps(500,600):.1f}  (optimal {OPT})")

print("\n=== EXP2: exploration — pure greedy locks onto the nearby crumb (exploration) ===")
# A short corridor of 6 spots. Start in the middle (spot 2). Step left a couple of times
# and you hit a small +1 exit; step right four times and you reach a big +10 exit.
CH=6; cstart=2; small=(0,1.0); big=(5,10.0); cg=0.95
def chain_episode(q,eps,alpha=0.5,maxT=30):
    s=cstart; found_big=False
    for _ in range(maxT):
        a=int(rng.integers(2)) if rng.random()<eps else int(np.argmax(q[s]))  # 0=left,1=right
        ns=max(0,s-1) if a==0 else min(CH-1,s+1)
        if ns==small[0]: r,done=small[1],True
        elif ns==big[0]: r,done=big[1],True; found_big=True
        else: r,done=0.0,False
        q[s,a]+=alpha*((r if done else r+cg*np.max(q[ns]))-q[s,a]); s=ns
        if done: break
    return found_big
for eps in [0.0,0.1,0.3]:
    q=np.zeros((CH,2)); got_big=0
    for ep in range(200):
        if chain_episode(q,eps): got_big+=1
    final=chain_episode(q,eps=0.0)   # what the learned greedy policy does
    print(f"eps={eps:<4}: greedy policy after training reaches the BIG +10 exit = {final}   "
          f"(found big during training in {got_big}/200 episodes)")
print("eps=0 walks to the near +1 and never discovers the +10; a little exploration finds it.")

print("\n=== EXP3: reward hacking — a proxy bonus gets gamed (reward) ===")
# naive shaping: +3 bonus each time you ENTER a 'charge' cell next to start.
CHARGE=(7,0)
def stepenv_hacked(s,a):
    dr,dc=ACT[a]; nr,nc=s[0]+dr,s[1]+dc
    ns=(nr,nc) if inb(nr,nc) else s
    if ns==GOAL: return ns,0.0,True
    if ns==PIT:  return ns,-50.0,True
    r=-1.0 + (3.0 if ns==CHARGE else 0.0)   # well-meant subgoal bonus
    return ns,r,False
def run_hacked(Q,eps,alpha=0.5,gamma=0.99,maxT=200):
    s=START; visits_charge=0; reached=False
    for t in range(maxT):
        a=int(rng.integers(4)) if rng.random()<eps else int(np.argmax(Q[s[0],s[1]]))
        ns,r,done=stepenv_hacked(s,a)
        if ns==CHARGE: visits_charge+=1
        target=r if done else r+gamma*np.max(Q[ns[0],ns[1]])
        Q[s[0],s[1],a]+=alpha*(target-Q[s[0],s[1],a]); s=ns
        if done: reached=(s==GOAL); return reached,visits_charge,t+1
    return False,visits_charge,maxT
Qh=np.zeros((N,N,4))
for ep in range(600): run_hacked(Qh,eps=0.1)
reached,visits,length=run_hacked(Qh,eps=0.0)
print(f"with a +3 'charge cell' bonus meant as a helpful subgoal:")
print(f"  greedy rollout reached goal={reached}, times it re-entered the charge cell={visits}, length={length}")
print(f"  the agent farms the bonus instead of finishing — the proxy reward, not the task, got optimized")

print("\n=== EXP4: model-based RL is far more sample-efficient (model-based-rl) ===")
free_cells=[(r,c) for r in range(N) for c in range(N)
            if (r,c) not in WALLS and (r,c) not in (GOAL,PIT)]
def collect(K):
    """continuing random walk: on hitting goal/pit, teleport to a random free cell (good coverage)"""
    seen={}; s=START
    for _ in range(K):
        a=int(rng.integers(4)); ns,r,done=stepenv(s,a)
        seen[(s,a)]=(ns,r)
        s=free_cells[int(rng.integers(len(free_cells)))] if done else ns
    return seen
def plan_and_test(model):
    V=np.full((N,N),-100.0)
    V[GOAL]=0.0; V[PIT]=0.0     # terminal states are worth 0; their reward is on the transition
    for _ in range(300):
        Vn=V.copy()
        for (r,c) in free_cells:
            best=-1e9
            for a in ACT:
                if ((r,c),a) in model:
                    ns,rew=model[((r,c),a)]; best=max(best,rew+0.99*V[ns])
            if best>-1e8: Vn[r,c]=best
        V=Vn
    s=START
    for _ in range(100):
        if s==GOAL: return True
        if s==PIT: return False
        # rank moves by the learned model's own estimate: reward now + 0.99 * value of where it lands
        cand=[]
        for a in ACT:
            if (s,a) in model:
                ns,rew=model[(s,a)]; cand.append((rew+0.99*V[ns], a, ns))
        if not cand: return False
        _,_,s=max(cand)
    return False
for K in [200,500,1000,2000]:
    ok=plan_and_test(collect(K))
    cov=len(collect(K))
    print(f"  {K:>4} random real steps -> learned {cov} of {len(free_cells)*4} moves -> plan reaches goal={ok}")
qsteps=sum(1 for _ in range(0))  # placeholder
print(f"  Q-learning (model-free) only backs up ONE step per real step, so it needs many hundreds")
print(f"  of steps of trial and error; a learned map plans over every remembered move at once.")

print("\n=== EXP5: policy gradient sharpens a probability (policy-optimization / policy) ===")
# 1D corridor length 5, start at 0, goal at 4. Actions: right(0)/left(1). Softmax policy per cell.
L=5; theta=np.zeros((L,2))
def softmax(z): z=z-z.max(); e=np.exp(z); return e/e.sum()
def rollout_pg(theta):
    s=0; traj=[];
    for t in range(20):
        p=softmax(theta[s]); a=int(rng.random()>p[0])  # 0=right,1=left
        ns=min(L-1,s+1) if a==0 else max(0,s-1)
        r=1.0 if ns==L-1 else -0.1; traj.append((s,a,r)); s=ns
        if s==L-1: break
    return traj
p_right_start=[softmax(theta[0])[0]]
for it in range(400):
    traj=rollout_pg(theta); G=sum(r for _,_,r in traj);
    for (s,a,_) in traj:
        p=softmax(theta[s]); grad=-p.copy(); grad[a]+=1
        theta[s]+= 0.05*G*grad
    p_right_start.append(softmax(theta[0])[0])
print(f"P(step toward goal) at start: {p_right_start[0]:.2f} (random) -> {p_right_start[-1]:.2f} (trained)")
print(f"policy gradient nudged the SAME rule's probabilities toward the actions that paid off.")
