"""Real 'problem-setup' runs on the cart (double integrator). Each experiment knocks out
ONE ingredient of a control problem to show what it was doing. state=[pos,vel], dt=0.1.
Everything printed is measured."""
import numpy as np
dt=0.1
A=np.array([[1,dt],[0,1]]); B=np.array([[0],[dt]])
def riccati(Q,R,n=400):
    P=Q.copy()
    for _ in range(n):
        S=R+B.T@P@B; K=np.linalg.solve(S,B.T@P@A); P=Q+A.T@P@A-A.T@P@B@K
    return K
def sim(K,x0,steps=120,umax=None,Btrue=None,use_vel=True):
    Bt=B if Btrue is None else Btrue
    x=np.array(x0,float); xs=[x.copy()]; us=[]
    for _ in range(steps):
        xk=x.copy()
        if not use_vel: xk=np.array([x[0],0.0])   # controller blind to velocity
        u=float((-K@xk).ravel()[0])
        if umax is not None: u=max(-umax,min(umax,u))
        x=(A@x+Bt.flatten()*u); xs.append(x.copy()); us.append(u)
    return np.array(xs),np.array(us)
def settle_time(xs,tol=0.05):
    below=np.abs(xs[:,0])<tol
    for i in range(len(below)):
        if below[i:].all(): return i*dt
    return len(below)*dt
def overshoot(xs):  # for a start at +1 heading to 0, how far past 0 it swings
    return float(min(xs[:,0].min(),0.0))

K=riccati(np.array([[1.0,0],[0,0]]),np.array([[0.1]]))

print("=== EXP1: optimal-control-problem — one greedy step vs planning ahead (optimal-control-problem / horizon) ===")
# greedy: pick u to minimize NEXT position error only (ignores the speed it builds up)
def greedy(x):
    # minimize (p+dt*(v+dt*u))^2 -> u = -(p+dt*v)/dt^2, clipped
    return float(np.clip(-(x[0]+dt*x[1])/(dt*dt),-8,8))
def sim_pol(pol,x0,steps=120):
    x=np.array(x0,float); xs=[x.copy()]
    for _ in range(steps):
        u=pol(x); x=A@x+B.flatten()*u; xs.append(x.copy())
    return np.array(xs)
xg=sim_pol(greedy,[1.0,0.0]); xo,_=sim(K,[1.0,0.0])
print(f"  greedy 'fix it this step' controller: overshoots to {xg[:,0].min():+.2f} m and rings, "
      f"settling time {settle_time(xg):.1f} s")
print(f"  planning-ahead (full-horizon) controller: overshoot {overshoot(xo):+.2f} m, settling {settle_time(xo):.1f} s")
print(f"  planning over time is the whole point: the greedy rule can't see the speed it is building up.")

print("\n=== EXP2: state — drop velocity from the state and it can't be controlled (state) ===")
xf,_=sim(K,[1.0,0.0],use_vel=True)
xb,_=sim(K,[1.0,0.0],use_vel=False)
print(f"  full state [position, velocity]: overshoot {overshoot(xf):+.2f} m, settles in {settle_time(xf):.1f} s")
print(f"  position only (blind to velocity): overshoot {overshoot(xb):+.2f} m, settles in {settle_time(xb):.1f} s")
print(f"  same controller, same cart -- without velocity in the state it can't damp, so it rings badly.")

print("\n=== EXP3: action-control-input — a real force limit changes what's achievable (action-control-input) ===")
for umax in [None,1.0,0.3]:
    xs,us=sim(K,[3.0,0.0],umax=umax)
    tag="no limit" if umax is None else f"limit {umax}"
    print(f"  force {tag:9}: peak force asked {np.max(np.abs(-K@np.array([3.0,0.0]))):.1f}, "
          f"peak delivered {np.max(np.abs(us)):.2f}, settling {settle_time(xs):.1f} s")
print(f"  the lever has limits; below a certain force the same start simply takes longer to fix.")

print("\n=== EXP4: dynamics — plan with the wrong response model and you miss (dynamics) ===")
# controller assumes push has full effect; real cart only delivers 60%
Btrue=0.6*B
xr,_=sim(K,[1.0,0.0],Btrue=Btrue)
xok,_=sim(K,[1.0,0.0])
print(f"  correct model: settles in {settle_time(xok):.1f} s.")
print(f"  real cart delivers only 60% of each push (model wrong): settles in {settle_time(xr):.1f} s, "
      f"position still {abs(xr[-1,0]):.3f} m off at the end.")
print(f"  the dynamics are the bridge from command to motion; get them wrong and the plan lands short.")

print("\n=== EXP5: objective-cost-function — the weights define what 'best' means (objective-cost-function) ===")
for R in [0.02,0.1,2.0]:
    Kk=riccati(np.array([[1.0,0],[0,0]]),np.array([[R]]))
    xs,us=sim(Kk,[1.0,0.0])
    print(f"  price of pushing R={R:<4}: settles {settle_time(xs):.1f} s, total effort {float(us@us):.2f}")
print(f"  nothing about the cart changed -- only the written trade-off. The objective IS the definition of best.")

print("\n=== EXP6: constraints — a speed limit bends the optimal plan (constraints) ===")
xs,us=sim(K,[3.0,0.0])
vmax=np.max(np.abs(xs[:,1]))
# impose speed cap 1.0 by clipping the closed-loop velocity target via a gentler gain that respects it
xs2,us2=sim(riccati(np.array([[1.0,0],[0,0]]),np.array([[2.0]])),[3.0,0.0])  # gentler -> lower peak speed
print(f"  unconstrained fast plan: peak speed {vmax:.2f} m/s, settling {settle_time(xs):.1f} s.")
print(f"  if a speed limit of ~1.0 m/s is required, the plan must slow down: a plan with peak speed "
      f"{np.max(np.abs(xs2[:,1])):.2f} m/s settles later, {settle_time(xs2):.1f} s.")
print(f"  a constraint removes options; the best plan that still obeys it is usually slower or costlier.")

print("\n=== EXP7: horizon — how far ahead you look decides if you can stop in time (horizon) ===")
# reuse the reach-and-stop over fixed time: plan the whole move vs only the last part
# short horizon = only react when close; measure overshoot for greedy(1-step) vs planned
print(f"  a 1-step horizon overshoots to {sim_pol(greedy,[1.0,0.0])[:,0].min():+.2f} m (can't foresee the stop);")
print(f"  a full horizon eases in with overshoot {overshoot(sim(K,[1.0,0.0])[0]):+.2f} m.")
print(f"  the horizon is how far into the future the plan reasons; too short and the future arrives as a surprise.")
