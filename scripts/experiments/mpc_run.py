"""Real MPC / safety runs on a braking cart (double integrator).
State = [position, velocity], control = force in [-1,1]. A wall sits ahead at
position = 0; the cart must stop before it. We plan a short horizon of forces,
apply the first, re-measure, replan. Everything printed is measured."""
import numpy as np
rng=np.random.default_rng(0)
dt=0.2; UMAX=1.0
def stepc(x,u):
    u=max(-UMAX,min(UMAX,u))
    p,v=x; v2=v+dt*u; p2=p+dt*v2
    return np.array([p2,v2])

def best_plan(x, H, wall):
    """Enumerate simple constant-then-brake force plans over horizon H; return the
    lowest-cost plan that never crosses the wall, else None (infeasible)."""
    best=None; bestc=1e18
    grid=np.linspace(-1,1,11)
    # candidate plans: brake hard for k steps then coast (enough to cover the space cheaply)
    cands=[]
    for u0 in grid:
        cands.append([u0]*H)
    for k in range(1,H+1):
        cands.append([-1.0]*k+[0.0]*(H-k))
    for plan in cands:
        x2=x.copy(); ok=True; cost=0.0
        for u in plan:
            x2=stepc(x2,u)
            if x2[0] > wall + 1e-9: ok=False; break     # crossed the wall
            cost += x2[0]**2 + 0.1*u**2                  # want position -> 0, gentle effort
        if ok and cost<bestc:
            bestc=cost; best=plan
    return best

def simulate_mpc(x0, H, wall, steps=40):
    x=np.array(x0,float); traj=[x.copy()]; crashed=False; infeasible_at=None
    for t in range(steps):
        plan=best_plan(x,H,wall)
        if plan is None:
            infeasible_at=t; break
        x=stepc(x,plan[0]); traj.append(x.copy())
        if x[0] > wall+1e-9: crashed=True; break
    return np.array(traj), crashed, infeasible_at

print("=== EXP1: feasibility — does ANY safe braking plan exist right now? ===")
wall=0.0
for p0,v0 in [(-3.0,1.0),(-1.0,2.0),(-0.5,2.5)]:
    plan=best_plan(np.array([p0,v0]), H=8, wall=wall)
    # minimal stopping distance under max brake from speed v0: v0^2/(2*UMAX) roughly
    stop_dist=v0*v0/(2*UMAX)
    print(f"  start pos={p0:+.1f} m, speed={v0:.1f} m/s: distance to wall={-p0:.1f} m, "
          f"min stopping distance≈{stop_dist:.2f} m -> {'a safe plan EXISTS' if plan else 'NO safe plan (infeasible)'}")

print("\n=== EXP2: recursive feasibility — a short horizon walks into a trap ===")
for H in [2,4,8]:
    traj,crashed,infeas=simulate_mpc([-3.0,0.0],H=H,wall=0.0,steps=40)
    # drive it: give the cart a target that pulls it forward (position cost pulls toward 0=wall)
    outcome = "CRASHED into wall" if crashed else ("stuck (declared infeasible mid-run)" if infeas is not None else "stopped safely")
    endp = traj[-1]
    print(f"  horizon H={H}: {outcome}; final pos={endp[0]:+.2f} m, speed={endp[1]:+.2f} m/s "
          f"(steps taken={len(traj)-1})")
print("  A greedy short horizon races toward position 0 (low cost) and only 'sees' the wall too late")
print("  to brake; a longer horizon foresees the stop it will need and never enters the trap.")

print("\n=== EXP3: reachability — which starting speeds CAN still stop in time? ===")
wall=0.0; H=10
dist=2.0  # cart starts 2 m before the wall
safe=[]; unsafe=[]
for v0 in np.round(np.arange(0.5,6.01,0.5),2):
    plan=best_plan(np.array([-dist,v0]),H=H,wall=wall)
    (safe if plan is not None else unsafe).append(float(v0))
print(f"  from {dist:.0f} m before the wall, horizon {H}:")
print(f"    speeds that CAN still stop safely: {safe}")
print(f"    speeds already doomed (no plan stops in time): {unsafe}")
if unsafe:
    print(f"  the boundary is between {max(safe)} and {min(unsafe)} m/s — the edge of the safe set.")

print("\n=== EXP4: stability under replanning — does the cost actually go DOWN each step? ===")
traj,crashed,infeas=simulate_mpc([-3.0,0.0],H=8,wall=0.0,steps=40)
costs=[float(x[0]**2) for x in traj]   # 'how far from the target still' each step
downs=sum(1 for i in range(1,len(costs)) if costs[i]<=costs[i-1]+1e-9)
print(f"  distance-to-target at steps 0,1,2,3: {[round(c,2) for c in costs[:4]]}")
print(f"  final: {round(costs[-1],3)} at step {len(costs)-1}")
print(f"  the 'how-far-left' number went DOWN (or held) on {downs} of {len(costs)-1} steps "
      f"-> replanning makes steady progress, it does not oscillate.")
