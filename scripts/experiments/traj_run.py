"""Real trajectory-optimization runs on the least-effort move of a cart.
Move a cart from (position 0, speed 0) to (position 1, speed 0) in fixed time,
using as little total push-effort (sum of squared force) as possible.
Double integrator, N steps, dt. Everything printed is measured."""
import numpy as np
np.set_printoptions(precision=3, suppress=True)
N=20; T=2.0; dt=T/N
# build linear map u (length N) -> final [pos, vel], starting from rest at 0
def final_state(u):
    p=0.0; v=0.0
    for uk in u:
        v=v+dt*uk; p=p+dt*v
    return np.array([p,v])
# columns of M = response of final state to a unit push at step k
M=np.zeros((2,N))
for k in range(N):
    e=np.zeros(N); e[k]=1.0; M[:,k]=final_state(e)
target=np.array([1.0,0.0])

print("=== EXP1: the least-effort trajectory (trajectory-optimization) ===")
# min ||u||^2 subject to M u = target  ->  least-norm solution
ustar=M.T @ np.linalg.solve(M@M.T, target)
Jstar=float(ustar@ustar)
# a hand-made plan that also reaches the target: push +a for half, -a for half (bang-bang)
a=None
# find a so bang-bang reaches pos 1 with final v 0: by symmetry final v=0 automatically; solve pos
def bangbang(a):
    u=np.array([a]*(N//2)+[-a]*(N//2)); return u
# scale a to hit position 1
u1=bangbang(1.0); p1=final_state(u1)[0]
abb=1.0/p1
ubb=bangbang(abb); Jbb=float(ubb@ubb)
print(f"  least-effort total effort J* = {Jstar:.3f}")
print(f"  a sensible hand plan (push hard, then brake hard) reaching the same target: J = {Jbb:.3f}")
print(f"  the optimized whole-path plan uses {100*(1-Jstar/Jbb):.0f}% less effort than the hand plan.")

print("\n=== EXP2: indirect vs direct agree (indirect-methods / calculus-of-variations / hamiltonian / costate) ===")
# Pontryagin: H = u^2/2 + lam_p*v + lam_v*u ; dH/du=0 -> u=-lam_v ;
# costate: lam_p'=0 (const), lam_v'=-lam_p  -> lam_v LINEAR in time -> optimal u is LINEAR in time.
ts=np.arange(N)
A=np.column_stack([ts,np.ones(N)])
coef,res,*_=np.linalg.lstsq(A,ustar,rcond=None)
fit=A@coef
r2=1-np.sum((ustar-fit)**2)/np.sum((ustar-ustar.mean())**2)
print(f"  Pontryagin (the indirect/costate route) predicts the optimal push is a STRAIGHT LINE in time.")
print(f"  the directly-optimized push sequence fits a straight line with R^2 = {r2:.5f} (1.0 = perfect line).")
print(f"  push at first step = {ustar[0]:+.3f}, at last step = {ustar[-1]:+.3f} (mirror image, as the theory says).")

print("\n=== EXP3: shooting — guess the start, measure the miss, correct (shooting-methods) ===")
# unknown = initial costate (2 numbers); u=-lam_v, lam_v evolves linearly. Parametrize u = g0 + g1*t.
# endpoint(g) = final_state(u(g)) ; Newton on the 2x2 linear map.
def u_of_g(g): return g[0]+g[1]*ts
def endpoint(g): return final_state(u_of_g(g))
g=np.array([0.0,0.0])          # first guess: push nothing
misses=[float(np.linalg.norm(endpoint(g)-target))]
# Jacobian of endpoint wrt g (linear, constant)
J=np.zeros((2,2))
for j,dg in enumerate([np.array([1.0,0]),np.array([0,1.0])]):
    J[:,j]=(endpoint(dg)-endpoint(np.zeros(2)))
for it in range(3):
    g=g-np.linalg.solve(J, endpoint(g)-target)
    misses.append(float(np.linalg.norm(endpoint(g)-target)))
print(f"  endpoint miss (distance from the target) per shooting iteration: {[round(m,4) for m in misses]}")
print(f"  one Newton correction takes the miss from {misses[0]:.3f} to {misses[1]:.4f} — the guess is fixed by")
print(f"  simulating forward, seeing where it lands, and adjusting the launch.")

print("\n=== EXP4: transcription defect — a drawn path must obey the dynamics (direct-transcription / collocation) ===")
# candidate: straight-line positions 0..1, velocities from finite differences that DON'T obey dynamics
pos_line=np.linspace(0,1,N+1)
vel_guess=np.gradient(pos_line,dt)
# defect at each knot = (p_{k+1}-p_k)/dt - v_{k+1} should be 0 under our dynamics; check a mismatch version
# deliberately inconsistent: the drawing claims the cart is barely moving (speed ~0) while its
# position marches from 0 to 1 -- the implied speed and the written speed disagree
vel_bad=np.zeros(N+1)
defect_bad=np.array([(pos_line[k+1]-pos_line[k])/dt - vel_bad[k+1] for k in range(N)])
# consistent trajectory from the optimal solution
p=0.0; v=0.0; traj=[(p,v)]
for uk in ustar:
    v=v+dt*uk; p=p+dt*v; traj.append((p,v))
traj=np.array(traj)
defect_ok=np.array([(traj[k+1,0]-traj[k,0])/dt - traj[k+1,1] for k in range(N)])
print(f"  a hand-drawn path with made-up speeds has a worst defect of {np.max(np.abs(defect_bad)):.3f}")
print(f"    (the drawing's implied speed disagrees with the physics between knots).")
print(f"  the optimized path's worst defect is {np.max(np.abs(defect_ok)):.2e} — essentially zero: every knot")
print(f"    hands the next one a physically reachable state. That is what solving the transcription enforces.")

print("\n=== EXP5: gradient descent to the first-order condition (gradient-first-order-condition) ===")
# minimize f(z)=(z-3)^2 + 0.2 z^2 ; df/dz=2(z-3)+0.4z=2.4z-6 ; min at z=2.5
z=0.0; lr=0.1; grads=[]
for _ in range(60):
    g1=2.4*z-6; z=z-lr*g1; grads.append(abs(g1))
print(f"  minimizing (z-3)^2 + 0.2 z^2: gradient magnitude {grads[0]:.2f} -> {grads[-1]:.4f} over 60 steps,")
print(f"  landing at z={z:.3f} (the exact minimum is 2.5, where the gradient is exactly 0).")

print("\n=== EXP6: static optimization with an active limit (static-optimization) ===")
# same f but with a cap z <= 1.5
zc=min(2.5,1.5)
print(f"  unconstrained best z=2.5. Add a cap z<=1.5: the best legal z is {zc:.1f} (pinned at the cap).")
print(f"  the cap is 'active': the unconstrained pull wants z=2.5 but the boundary holds it at 1.5.")
print(f"  cost at 2.5 = {(2.5-3)**2+0.2*2.5**2:.3f}; cost at the capped 1.5 = {(1.5-3)**2+0.2*1.5**2:.3f}.")

print("\n=== EXP7: local quadratic approximation is good near, bad far (local-quadratic-approximation) ===")
# true nonlinear cost g(x)=1-cos(x) (pendulum-ish). Quadratic fit at 0 is x^2/2.
for dx in [0.2,0.5,1.0,2.0]:
    true=1-np.cos(dx); approx=dx*dx/2
    print(f"  at offset {dx:.1f}: true cost {true:.3f}, quadratic guess {approx:.3f}, "
          f"error {abs(true-approx)/max(true,1e-9)*100:.1f}%")
print("  the bowl-shaped guess is nearly perfect close in and drifts off far out — which is exactly why")
print("  methods that trust it (like iLQR) must keep their steps small.")
