"""Real LQR run on a double integrator (a cart you push).
x=[position, velocity], u=force.  x_{k+1}=A x_k + B u_k.
We iterate the discrete Riccati recursion by hand (no scipy) so convergence is visible."""
import numpy as np
np.set_printoptions(precision=4, suppress=True)

dt = 0.1
A = np.array([[1, dt],[0, 1]])
B = np.array([[0],[dt]])
Q = np.array([[1.0, 0],[0, 0.0]])   # penalize position error

def riccati_backward(R, N=200):
    """Return list of gains K_k from k=N-1 back to 0, plus final steady gain."""
    P = Q.copy()                      # terminal cost = Q
    gains = []
    for _ in range(N):
        # K = (R + B'PB)^-1 B'PA ; P = Q + A'PA - A'PB K
        S = R + (B.T @ P @ B)
        K = np.linalg.solve(S, B.T @ P @ A)     # 1x2
        P = Q + A.T @ P @ A - A.T @ P @ B @ K
        gains.append(K.flatten())
    return np.array(gains)             # row 0 = one step from terminal, last row = deep interior

# ---------- EXPERIMENT 1: the gain forgets the horizon ----------
R = np.array([[0.1]])
g = riccati_backward(R, N=200)
Kfar = g[-1]
# how many backward steps until K is within 1% of the steady value?
err = np.linalg.norm(g - Kfar, axis=1) / np.linalg.norm(Kfar)
settle = int(np.argmax(err < 0.01))
print("=== EXP1: Riccati gain convergence (R=0.1) ===")
print("gain 1 step from end :", g[0])
print("gain 3 steps from end:", g[2])
print("gain 10 steps from end:", g[9])
print("steady interior gain :", Kfar)
print(f"steps to reach within 1% of steady: {settle}")
print(f"=> {settle} steps = {settle*dt:.1f} s of horizon; beyond that LQR uses ONE fixed rule")

# ---------- EXPERIMENT 2: ablation over control price R ----------
print("\n=== EXP2: sweep control price R -> gain, settling, effort ===")
def simulate(K, x0, steps=200, umax=None):
    x = np.array(x0, float); xs=[x.copy()]; us=[]; cost=0.0
    for _ in range(steps):
        u = float(-K @ x)
        if umax is not None: u = max(-umax, min(umax, u))
        cost += float(x @ Q @ x) + 0.1*u*u
        x = A @ x + B.flatten()*u
        xs.append(x.copy()); us.append(u)
    return np.array(xs), np.array(us), cost
print(f"{'R':>7} {'K_pos':>8} {'K_vel':>8} {'settle_s':>9} {'peak_|u|':>9}")
for Rv in [0.01, 0.1, 1.0, 10.0, 100.0]:
    g = riccati_backward(np.array([[Rv]]))
    K = g[-1]
    xs, us, _ = simulate(K, [1.0, 0.0])
    # settling time: first time |pos|<0.05 and stays
    below = np.abs(xs[:,0]) < 0.05
    st = next((i for i in range(len(below)) if below[i:].all()), len(below))
    print(f"{Rv:>7} {K[0]:>8.3f} {K[1]:>8.3f} {st*dt:>9.1f} {np.max(np.abs(us)):>9.2f}")

# ---------- EXPERIMENT 3: the real weakness — saturation ----------
print("\n=== EXP3: linear gain vs a real actuator limit |u|<=1.0 ===")
K = riccati_backward(np.array([[0.1]]))[-1]
for x0 in [0.5, 1.0, 3.0, 8.0]:
    u_demand = float(-K @ np.array([x0, 0.0]))
    _, us_c, cost_c = simulate(K, [x0,0.0], umax=1.0)
    _, _,   cost_u = simulate(K, [x0,0.0], umax=None)
    print(f"x0={x0:>4}m  first u demanded={u_demand:>8.2f}  (limit 1.00)  "
          f"cost_ideal={cost_u:>8.1f}  cost_clipped={cost_c:>9.1f}  "
          f"blowup x{cost_c/cost_u:>5.1f}")
