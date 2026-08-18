#!/usr/bin/env python3
"""Build the cross-course bridge page: 'Data -> Model -> Control, one machine'.

Connects Steve Brunton's data-driven dynamical-systems course (the FRONT half:
get a model and a state from data) to Stanford AA203 optimal control (the BACK
half: given a model and state, compute the optimal control). Brunton produces
exactly what AA203 assumes; the two compose into one closed loop.

Hosted in the AA203 site. AA203 concept links are relative (concepts/<id>-deep.html);
Brunton links use BRUNTON_BASE (swap the localhost value for the public Pages URL
at deploy time).
"""
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "bridge-data-to-control.html"

# Swap this for the public Brunton Pages URL when deploying.
BRUNTON_BASE = "http://localhost:8012/"

def e(s): return html.escape(str(s), quote=True)
def aa(cid, label): return f'<a href="concepts/{cid}-deep.html">{e(label)}</a>'
def eig(cid, label): return f'<a href="{BRUNTON_BASE}{cid}-deep.html">{e(label)}</a>'

# The connections. Each: Brunton side (from data) -> shared hidden object -> AA203 side (to control) + handoff.
BRIDGE = [
    {
        "brunton": [("sindy", "SINDy"), ("dynamic-mode-decomposition", "DMD"), ("koopman-operator", "Koopman")],
        "object": "the evolution rule — how the state moves, x → f(x, u)",
        "aa203": [("dynamics", "dynamics"), ("lqr", "LQR"), ("trajectory-optimization", "trajectory optimization"), ("model-based-rl", "model-based RL")],
        "how": "Brunton's methods recover the equations of motion from measured trajectories — no hand-derived model. AA203 then takes that very rule as the model it plans and optimizes control over. One side discovers f; the other side optimizes through it.",
    },
    {
        "brunton": [("kalman-filter", "the Kalman filter")],
        "object": "the true state you cannot directly measure",
        "aa203": [("state", "state"), ("value-function", "value / feedback")],
        "how": "The Kalman filter reconstructs the hidden state from noisy, partial sensors. Every AA203 controller quietly assumes it can read a clean state — the filter is what actually supplies it.",
    },
    {
        "brunton": [("proper-orthogonal-decomposition", "POD")],
        "object": "a low-dimensional set of coordinates",
        "aa203": [("state", "reduced state"), ("dynamic-programming", "dynamic programming")],
        "how": "POD compresses a high-dimensional system to the few coordinates that carry the behavior. AA203's value iteration and LQR, which choke on large state spaces, become tractable in that reduced state.",
    },
    {
        "brunton": [("koopman-operator", "the Koopman operator")],
        "object": "linear coordinates for a nonlinear system",
        "aa203": [("lqr", "LQR"), ("local-quadratic-approximation", "local quadratic approximation")],
        "how": "Koopman lifts nonlinear dynamics into coordinates where they act linearly. AA203's most powerful tools are linear-quadratic — so once Koopman does the lifting, LQR applies directly instead of only in a small neighborhood.",
    },
    {
        "brunton": [("sensitivity-and-robustness", "the waterbed law")],
        "object": "the robustness ↔ performance tradeoff",
        "aa203": [("stability-under-replanning", "stability under replanning"), ("model-predictive-control", "MPC")],
        "how": "The waterbed law proves no feedback loop can be robust everywhere — push down error rejection at one frequency and it pops up at another. AA203's replanning controllers live inside that hard bound; it tells them what they cannot buy.",
    },
    {
        "brunton": [("compressed-sensing", "compressed sensing")],
        "object": "sparsity — few measurements suffice",
        "aa203": [("state", "state from few sensors"), ("feasibility", "sensing budget")],
        "how": "Compressed sensing rebuilds a full signal from far fewer samples than seem necessary, when the signal is sparse. When AA203's state must be inferred under a tight sensor budget, this is what makes a full state estimate possible at all.",
    },
]

CSS = """
.bridge-hero .kick{color:var(--accent-2)}
.loop{max-width:760px;margin:22px auto 6px;display:block}
.loop text{font-family:Inter,system-ui,sans-serif}
.legend2{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:10px 0 26px}
.legend2 .side{border:1px solid var(--line);border-radius:10px;background:var(--paper);padding:14px 16px}
.legend2 .side h3{margin:0 0 4px;font-size:16px}
.legend2 .side.data h3{color:var(--accent-2)}.legend2 .side.control h3{color:var(--accent)}
.legend2 .side p{margin:0;font-size:14px;color:var(--muted)}
.conn{border:1px solid var(--line);border-radius:12px;background:var(--paper);padding:0;margin:14px 0;overflow:hidden}
.conn .top{display:grid;grid-template-columns:1fr auto 1fr;gap:0;align-items:stretch}
.conn .cell{padding:14px 16px}
.conn .from{background:#fbf3ee;border-right:1px solid var(--line)}
.conn .to{background:var(--soft);border-left:1px solid var(--line)}
.conn .mid{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:12px 14px;min-width:150px;text-align:center;background:var(--paper)}
.conn .mid .obj{font-size:13px;color:var(--ink);font-weight:600;line-height:1.35}
.conn .mid .arrow{font-family:ui-monospace,Menlo,monospace;color:var(--accent);font-size:18px;margin:2px 0}
.conn .lab{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);display:block;margin-bottom:6px}
.conn .from .lab{color:var(--accent-2)}.conn .to .lab{color:var(--accent)}
.conn .chips a{display:inline-block;margin:0 5px 5px 0;padding:3px 9px;border-radius:999px;border:1px solid var(--line);background:#fff;font-size:13px;text-decoration:none}
.conn .from .chips a:hover{border-color:var(--accent-2)}.conn .to .chips a:hover{border-color:var(--accent)}
.conn .how{padding:12px 16px;border-top:1px solid var(--line);font-size:14.5px;color:#24323a;background:#fff}
.conn .how b{color:var(--accent-2)}
@media(max-width:760px){.conn .top{grid-template-columns:1fr}.conn .from,.conn .to{border:0;border-bottom:1px solid var(--line)}.legend2{grid-template-columns:1fr}}
"""

def ring_svg():
    # simple closed-loop ring: DATA -> MODEL+STATE -> ACTIONS -> back to DATA
    return """
<svg class="loop" viewBox="0 0 760 260" role="img" aria-label="Closed loop: data to model to control back to data">
  <defs><marker id="ah" markerWidth="10" markerHeight="10" refX="7" refY="3" orient="auto">
    <path d="M0,0 L7,3 L0,6 Z" fill="#0b6b64"/></marker></defs>
  <rect x="30" y="100" width="150" height="60" rx="10" fill="#fff" stroke="#d7e0e6"/>
  <text x="105" y="126" text-anchor="middle" font-size="14" font-weight="700" fill="#17202a">measured data</text>
  <text x="105" y="145" text-anchor="middle" font-size="11" fill="#5d6875">sensors, trajectories</text>
  <rect x="300" y="20" width="160" height="66" rx="10" fill="#fbf3ee" stroke="#e6cdbc"/>
  <text x="380" y="46" text-anchor="middle" font-size="13" font-weight="700" fill="#8b3f18">Brunton</text>
  <text x="380" y="64" text-anchor="middle" font-size="11" fill="#5d6875">discover model + state</text>
  <rect x="580" y="100" width="150" height="60" rx="10" fill="#e8f2f0" stroke="#bcd">
  </rect>
  <text x="655" y="126" text-anchor="middle" font-size="13" font-weight="700" fill="#0b6b64">AA203</text>
  <text x="655" y="145" text-anchor="middle" font-size="11" fill="#5d6875">optimal control</text>
  <rect x="300" y="176" width="160" height="60" rx="10" fill="#fff" stroke="#d7e0e6"/>
  <text x="380" y="202" text-anchor="middle" font-size="14" font-weight="700" fill="#17202a">actions</text>
  <text x="380" y="220" text-anchor="middle" font-size="11" fill="#5d6875">commands to the world</text>
  <path d="M180,120 C240,60 260,50 300,52" fill="none" stroke="#8b3f18" stroke-width="2" marker-end="url(#ah)"/>
  <path d="M460,53 C520,55 540,70 590,110" fill="none" stroke="#0b6b64" stroke-width="2" marker-end="url(#ah)"/>
  <path d="M655,160 C655,210 520,206 462,206" fill="none" stroke="#0b6b64" stroke-width="2" marker-end="url(#ah)"/>
  <path d="M300,206 C200,206 120,190 105,162" fill="none" stroke="#5d6875" stroke-width="2" stroke-dasharray="4 3" marker-end="url(#ah)"/>
  <text x="240" y="150" font-size="11" fill="#8b3f18">model+state</text>
  <text x="470" y="150" font-size="11" fill="#0b6b64">given model</text>
  <text x="150" y="212" font-size="11" fill="#5d6875">new data</text>
</svg>"""

def conn_html(c):
    frm = "".join(eig(cid, l) for cid, l in c["brunton"])
    to = "".join(aa(cid, l) for cid, l in c["aa203"])
    return f"""<div class="conn"><div class="top">
<div class="cell from"><span class="lab">Brunton · from data</span><div class="chips">{frm}</div></div>
<div class="cell mid"><div class="arrow">&darr;</div><div class="obj">{e(c["object"])}</div><div class="arrow">&darr;</div></div>
<div class="cell to"><span class="lab">AA203 · to control</span><div class="chips">{to}</div></div>
</div><div class="how"><b>How it hands off.</b> {e(c["how"])}</div></div>"""

def page():
    conns = "\n".join(conn_html(c) for c in BRIDGE)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Data → Model → Control: One Machine</title>
<link rel="stylesheet" href="assets/styles.css">
<style>{CSS}</style></head><body>
<header class="topbar"><a class="brand" href="index.html">Stanford AA203 Control Lab</a>
<nav><a href="index.html">Overview</a><a href="concepts.html">Concepts</a><a href="deep-track.html">Deep track</a><a href="concept-explainers.html">Mechanism map</a><a class="active" href="bridge-data-to-control.html">Data → Control bridge</a></nav></header>
<main>
<div class="hero bridge-hero"><div class="kick">connecting the dots · two courses, one pipeline</div>
<h1>Data → Model → Control: One Machine</h1>
<p class="lede">Steve Brunton's data-driven course and Stanford AA203 optimal control look like separate subjects. They are two halves of the same machine. Brunton's half turns <b>measured data into a model and a state</b>; AA203's half turns <b>that model and state into the best control</b>. Brunton produces exactly what AA203 assumes — and the actions AA203 commands generate the next round of data, closing the loop.</p>
</div>
{ring_svg()}
<div class="legend2">
<div class="side data"><h3>Brunton — the front half</h3><p>Get a model and a state <i>from data</i>: discover the governing equations (SINDy, DMD, Koopman), reconstruct the hidden state (Kalman filter), compress it (POD), and bound its robustness (the waterbed law).</p></div>
<div class="side control"><h3>AA203 — the back half</h3><p><i>Given</i> a model and a state, compute the best action: value and cost-to-go (dynamic programming), fixed-gain regulation (LQR), whole-path planning (trajectory optimization), and re-solving online (MPC).</p></div>
</div>
<div class="eyebrow" style="font-family:ui-monospace,Menlo,monospace;font-size:11px;text-transform:uppercase;letter-spacing:.16em;color:var(--accent);margin:30px 0 6px">The connections</div>
<h2 style="margin:0 0 4px">Where the dots actually connect</h2>
<p class="muted" style="max-width:80ch">Each row is one wire between the courses: a Brunton concept produces the hidden object in the middle, and an AA203 concept consumes it. Click any concept to open its deep dive.</p>
{conns}
<div class="conn" style="border-color:var(--accent-2)"><div class="how" style="border-top:0;background:#fbf3ee"><b>And the loop closes.</b> AA203's controller acts, the world responds, and those responses are new measured data — which Brunton's methods use to refine the model and state. Run that cycle continuously and you have adaptive, data-driven control: exactly the meeting point that <a href="concepts/model-based-rl-deep.html">model-based RL</a> formalizes. The two courses are not neighbors; they are one loop.</div></div>
<p class="muted" style="font-size:12px;margin-top:34px;border-top:1px solid var(--line);padding-top:18px">Cross-course bridge · generated by scripts/build_bridge.py · AA203 links are local; Brunton links use BRUNTON_BASE (set to the public Pages URL at deploy).</p>
</main></body></html>"""

def main():
    OUT.write_text(page(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} | {len(BRIDGE)} connections")

if __name__ == "__main__":
    main()
