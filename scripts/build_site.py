#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
RAW = ROOT / "raw-material/youtube"
ANALYSIS = ROOT / "analysis"


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(line.rstrip() for line in content.splitlines()) + "\n", encoding="utf-8")


def load_json(path: Path, fallback: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback


def page(title: str, body: str, active: str = "", depth: int = 0) -> str:
    prefix = "../" * depth
    nav = [
        ("index.html", "Overview", "overview"),
        ("lectures.html", "Lectures", "lectures"),
        ("transcripts.html", "Transcripts", "transcripts"),
        ("concepts.html", "Concepts", "concepts"),
        ("course-spine.html", "Spine", "spine"),
        ("families.html", "Families", "families"),
        ("primitives.html", "Primitives", "primitives"),
        ("formula-reader.html", "Formulas", "formulas"),
        ("derivations.html", "Derivations", "derivations"),
        ("drills.html", "Drills", "drills"),
        ("evidence.html", "Evidence", "evidence"),
        ("review-guide.html", "Review", "review"),
    ]
    links = "\n".join(
        f'<a class="{"active" if key == active else ""}" href="{prefix}{href}">{label}</a>' for href, label, key in nav
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} · Stanford AA203 Control Lab</title>
  <link rel="stylesheet" href="{prefix}assets/styles.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="{prefix}index.html">Stanford AA203 Control Lab</a>
    <nav>{links}</nav>
  </header>
  <main>{body}</main>
</body>
</html>
"""


def card(title: str, body: str, extra_class: str = "") -> str:
    return f'<article class="card {extra_class}"><h3>{esc(title)}</h3>{body}</article>'


def section_list(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


def sentence_body(value: str) -> str:
    return value.strip().rstrip(".")


def recognition_sentence(value: str) -> str:
    text = sentence_body(value)
    lowered = text[:1].lower() + text[1:]
    for prefix in ["Use it when ", "Use this when ", "Use this term when "]:
        if text.lower().startswith(prefix.lower()):
            return "Use it when " + text[len(prefix):]
    if text.lower().startswith("choose this lens when "):
        return "Use this lens when " + text[len("choose this lens when "):]
    if text.lower().startswith("before asking "):
        body = text[len("before asking "):]
        body = re.sub(r", ask\s+", "; first ask ", body, flags=re.I)
        return "Use it before asking " + body
    if text.lower().startswith("ask "):
        return "Use it when you need to " + lowered
    if text.lower().startswith("look for "):
        return "Use it when you need to " + lowered
    return "Use it when you need to " + lowered


def concept_link(concept: dict[str, Any], depth: int = 0) -> str:
    prefix = "../" * depth
    return f'<a href="{prefix}concepts/{esc(concept["id"])}.html">{esc(concept["name"])}</a>'


def evidence_by_id(evidence: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in evidence}


def evidence_card(row: dict[str, Any], depth: int = 0) -> str:
    prefix = "../" * depth
    timestamp = ""
    if row.get("timestamp_start"):
        timestamp = f' · <a href="{esc(row.get("timestamp_url", row["url"]))}">{esc(row["timestamp_start"])}-{esc(row.get("timestamp_end", ""))}</a>'
    return f"""<article class="evidence-card" id="{esc(row['id'])}">
  <h3>{esc(row['id'])}: Lecture {esc(row['lecture'])} · {esc(row['lecture_title'])}</h3>
  <p class="muted"><a href="{esc(row['url'])}">{esc(row['video_id'])}</a>{timestamp} · <code>{esc(row['local_transcript'])}</code> · {esc(row['confidence_status'])}</p>
  <blockquote>{esc(row['local_transcript_window'])}</blockquote>
  <p><strong>Transcript supports:</strong> {esc(row['what_transcript_supports'])}</p>
  <p><strong>Synthesis boundary:</strong> {esc(row['synthesis_beyond_transcript'])}</p>
  <p><a href="{prefix}evidence.html#{esc(row['id'])}">Open evidence record</a></p>
</article>"""


CONCEPT_RUNS: dict[str, dict[str, str]] = {
    "optimal-control-problem": {
        "run": "Suppose a landing rocket is 80 meters above the pad, falling at 18 m/s, with 12 seconds of fuel left. Use a rough two-step horizon with dt = 1 second, state x = (height, velocity, fuel), and control u = upward acceleration from thrust. Gravity adds -10 m/s^2, and fuel drops by 2 units for each 1 m/s^2 of thrust. Candidate A burns hard now: u_0 = 18, then u_1 = 8. After the first second, velocity changes from -18 to -10 m/s and height falls to 70 meters; fuel drops from 12 to -24, so the path is illegal before it can be attractive. Candidate B burns less: u_0 = 4, then u_1 = 2. After two seconds, velocity is -32 m/s, height is 24 meters, and fuel is 0; it is legal on fuel but headed for a hard crash. Candidate C uses u_0 = 3 and u_1 = 3. It also keeps fuel nonnegative, ending with fuel 0, but it reaches only h_2 = 23 meters with v_2 = -32 m/s. The score may rank B and C, but A is rejected before scoring. The setup can say something stronger than which bad plan is less bad. Since fuel cannot go below zero, the two commands must satisfy 2*u_0 + 2*u_1 <= 12, so u_0 + u_1 <= 6. But over two seconds gravity subtracts 20 m/s from velocity. Even spending all legal fuel gives v_2 = -18 + 6 - 20 = -32 m/s. A soft touchdown with v_2 near 0 is not inside this written problem. These ugly numbers are the point: an optimal-control problem is not a wish to land softly. It is the named chain of states, controls, dynamics, cost, horizon, and constraints that lets the controller discover whether a soft landing is even available.",
        "math": "One finite-horizon form is: choose u_0...u_{N-1} to minimize J = sum_k fuel_cost(u_k) + 100*landing_error^2 + 20*touchdown_speed^2, subject to x_{k+1}=f(x_k,u_k), fuel_k >= 0, 0 <= u_k <= u_max, and safe touchdown speed. The rocket state update might be v_{k+1}=v_k + dt*(u_k - 10), h_{k+1}=h_k + dt*v_{k+1}, and fuel_{k+1}=fuel_k - 2*u_k. For Candidate B, the fuel constraint passes because 12 - 2*4 - 2*2 = 0, but a two-step terminal score with h_target = 0 and v_target = 0 gives 100*(24 - 0)^2 + 20*(-32)^2 = 78,080 before adding fuel cost. Candidate C has 12 - 2*3 - 2*3 = 0 and terminal score 100*(23 - 0)^2 + 20*(-32)^2 = 73,380. The feasibility check is separate from the ranking check. Fuel nonnegativity implies sum_u = u_0 + u_1 <= 6. The velocity formula over two one-second steps is v_2 = -18 + sum_u - 20, so every legal sequence has v_2 <= -32. If the mission constraint says |v_2| <= 2 for touchdown, the feasible set is empty for this horizon and fuel amount. The right repair is not to tune weights harder; it is to change a real setup piece, such as add fuel, lengthen the horizon, change the initial state, or admit that landing is impossible. This one line ties the pieces together: the action changes acceleration, acceleration changes velocity, velocity changes height, fuel limits future actions, and the objective scores the whole resulting trajectory. If the fuel model is wrong or the constraint is omitted, the optimizer can produce a mathematically neat answer to the wrong landing problem.",
    },
    "state": {
        "run": "A car is at lane position y = 0.20 meters left of center. If that number is the whole state, two physically different cars look identical. Car A has sideways velocity v_y = 0.00 m/s and heading error psi = 0 degrees. Car B has v_y = -1.50 m/s and psi = -8 degrees because it is sliding back toward the lane center. Give both cars the same steering command, u = +5 degrees, for dt = 0.2 seconds. A simple lateral update might say y_next = y + dt*v_y. Car A predicts y_next = 0.20 + 0.2*0.00 = 0.20 meters. Car B predicts y_next = 0.20 + 0.2*(-1.50) = -0.10 meters, crossing the center line in the other direction before steering has even done much. Position alone did not contain enough memory. A single camera frame might show only y = 0.20. Two recent frames can reveal more: if y was 0.50 meters left 0.2 seconds ago and is 0.20 now, then v_y_est = (0.20 - 0.50)/0.2 = -1.50 m/s. Now use a delivery drone with the same position and velocity but two battery temperatures. Drone C has battery_temp = 32 C; Drone D has battery_temp = 46 C. The same climb command may be legal for C, but for D it can push the pack over a 48 C heat limit. If temperature is omitted, both drones receive the same action even though one has a future constraint almost active. The missing state variable turns a safe climb into a hidden thermal violation. The state needs the present facts that make the next step predictable: position, velocity, heading, tire slip, battery heat, and any nearby obstacle that changes what a legal action can do.",
        "math": "A state is the record x_t that makes the next-step model meaningful: x_{t+1}=f(x_t,u_t). If two histories give the same x_t, the model is asserting that the same action distribution over next states applies to both histories. The Markov test is practical, not mystical: ask whether adding a missing variable changes the predicted next state, cost, or constraint. In the car example, using x=[y] fails because the same y and u produce different y_next once v_y is revealed. Using x=[y,v_y,psi] is closer because it carries the motion needed for the next update. An observation o_t can be only what the sensor sees now, while the state used by the controller may include an estimate built from history. With o_t = camera_frame_t, the car may need x_t = [y_t, (y_t-y_{t-1})/dt, psi_t] to recover lateral velocity. In the numbers above, (0.20 - 0.50)/0.2 = -1.50, which separates sliding Car B from steady Car A. For the drone, x=[position,velocity] is not enough if heat constrains future thrust. A better state includes battery_temp, so the heat update can check battery_temp_next = battery_temp + heat_gain(u). If heat_gain(climb)=3 C, Drone C moves from 32 C to 35 C and stays below 48 C, while Drone D moves from 46 C to 49 C and violates the heat constraint. Same command, different true state. The boundary is omitted memory: hidden battery temperature, tire grip, load mass, or another car's velocity can make a controller repeat the same action in situations whose futures are not the same.",
    },
    "action-control-input": {
        "run": "A drone pilot may want the drone to be two meters higher, but height is not the command. Suppose the drone is at h = 10 meters, moving upward at v = 0.2 m/s, and the controller raises average rotor thrust from hover thrust to 48 percent above hover for the next dt = 0.1 seconds. In this simple model, that command gives upward acceleration a(u)=4.8 m/s^2. Acceleration changes velocity first: v_next = 0.2 + 0.1*4.8 = 0.68 m/s. Then velocity changes height: h_next = 10 + 0.1*0.68 = 10.068 meters. The drone did not jump to 12 meters. It moved 6.8 centimeters because the action was a motor command applied for one tenth of a second. Now try a more desperate request: u = 0.9, meaning 90 percent above hover. If the motor limit is u <= 0.5, the command actually sent is u_sent = 0.5. The next velocity is 0.2 + 0.1*5.0 = 0.70 m/s and the next height is 10.070 meters, not 12 meters. If the plan writes 'go to 12 meters' as the action, it has skipped the actuator and asked the optimizer for an outcome the drone cannot directly issue. Add one more piece of actuator truth. Suppose the previous command was u_prev = 0.10 and the motor controller can change thrust by only 0.20 per tick. Even though u = 0.50 is within the absolute limit, the command that reaches the motor this tick is u_rate = 0.30. Then a(u_rate)=3.0 m/s^2, v_next = 0.2 + 0.1*3.0 = 0.50 m/s, and h_next = 10 + 0.1*0.50 = 10.050 meters. The action set can also change with state. If battery_temp = 46 C, the safe set may shrink to u <= 0.25 until the pack cools; the same requested u = 0.48 must then be sent as u_hot = 0.25. With a(u_hot)=2.5 m/s^2, the next height is only 10.045 meters. A grid-world action such as north, south, east, west is discrete; a thrust command like u = 0.37 is continuous. Both are actions because both are choices passed into the next-step rule. The next action may again increase thrust, but each command still passes through limits, rate changes, motors, acceleration, velocity, and only then position.",
        "math": "The action u is the command passed into the dynamics. A simple vertical model might use a(u)=10*u, where u is thrust above hover written as a fraction, capped by -0.3 <= u <= 0.5. For u = 0.48, a(u)=4.8 m/s^2 and the updates are v_next = v + dt * a(u) and h_next = h + dt * v_next. With dt = 0.1, v=0.2, and h=10, the result is v_next=0.68 and h_next=10.068. If the optimizer asks for u = 0.9, the actuator limit clips it to u_clipped = min(0.9,0.5) = 0.5, so the model should compute with a=5.0 m/s^2. That gives v_next = 0.2 + 0.1*5.0 = 0.70 and h_next = 10 + 0.1*0.70 = 10.070. A rate limit is different from an absolute limit. If u_prev = 0.10 and |u - u_prev| <= 0.20, then the requested u_clipped = 0.5 must be sent as u_rate = 0.30 for this tick. The update becomes a(u_rate)=3.0, v_next = 0.2 + 0.1*3.0 = 0.50, and h_next = 10 + 0.1*0.50 = 10.050. The admissible action set can depend on the state, written U(x). In the hot-battery state, U(x_hot) = [-0.3, 0.25], so u_safe = min(0.48,0.25) = 0.25 and h_next = 10 + 0.1*(0.2 + 0.1*2.5) = 10.045. Some actuators also have a dead zone: if |u| < 0.05, then a(u)=0 because the command is too small to overcome motor friction. A requested u = 0.03 is a real command, but it produces v_next = 0.2 and h_next = 10.020 in this toy model. The next state is produced by x_next = f(x, u_rate), so action limits are limits on the command that actually reaches the plant, not on wishes about x_next. A desired height can appear in the cost, for example (h_next - 12)^2, but it is not the control input. The boundary is actuator truth: delay, saturation, dead zones, state-dependent safe sets, and rate limits belong in the action model because they decide what command the system can actually obey.",
    },
    "dynamics": {
        "run": "A car is moving at speed 20 m/s with heading theta = 0 degrees. The controller sends the same steering command in two worlds: u = 5 degrees for dt = 0.2 seconds. On dry asphalt, suppose the tire model gives yaw_rate = 0.30 rad/s. The next heading is theta_next = 0 + 0.2*0.30 = 0.06 rad. On ice, the same state and same steering command may give yaw_rate = 0.05 rad/s and sideways slip v_y = -1.0 m/s. The next heading is only theta_next = 0 + 0.2*0.05 = 0.01 rad, while lateral position changes by y_next = y + 0.2*(-1.0). Keep applying the same command for three ticks. The dry model predicts theta = 0.18 rad after 0.6 seconds. The icy car reaches only theta = 0.03 rad and has drifted y = -0.6 meters sideways. Now add steering delay. If the command at this tick is u_now = 5 degrees but the rack still applies the previous command u_prev = 0 degrees, the first yaw rate is 0.00 rad/s and theta_next stays 0.00 rad. The 5 degree command affects the following tick, not this one. A model with delay must remember the pending command; otherwise two cars with the same pose but different pending steering are falsely treated as identical. The action did not change. The wish did not change. The rule that converts state and action into the next state changed. Dynamics are that rule. They are where mass, friction, delay, contact, gravity, and actuator response enter the problem. Without dynamics, a planner can draw a lane change but cannot say whether the car can physically start it in the next fifth of a second.",
        "math": "Dynamics can be written as x_next = f(x,u) in discrete time or dx/dt = f(x,u) in continuous time. A simple car state might be x=[y,theta,v_y,speed]. One update could be theta_next = theta + dt*yaw_rate(x,u,grip) and y_next = y + dt*v_y_next. The word model matters: dry asphalt and ice are different functions f_dry and f_ice, even when x and u have the same numbers. Under f_dry, three repeated steps give theta_3 = 3*0.2*0.30 = 0.18 rad and almost no sideways slip in this toy model. Under f_ice, the same commands give theta_3 = 3*0.2*0.05 = 0.03 rad and y_3 = 3*0.2*(-1.0) = -0.6 meters. A delayed actuator needs a different state or update. If the applied steering is u_applied = u_prev, then theta_next = theta + dt*yaw_rate(x,u_prev,grip). With u_prev = 0 degrees, yaw_rate = 0.00 rad/s, so theta_next = 0 + 0.2*0.00 = 0.00 rad even though u_now = 5 degrees has just been requested. The next state must carry u_now forward as the future u_prev. That means x must include pending steering when delay matters. If a controller plans with f_dry but the road follows f_ice, or plans with instant steering while the hardware has one-tick delay, the predicted next state is wrong before optimization, learning, or feedback has a chance to help. The boundary is model fidelity. Dynamics do not say what outcome is desirable; they say what outcome follows from a command. A cost can prefer the lane center and a constraint can forbid collision, but the dynamics decide what motion is physically produced. Bad dynamics make good optimization confidently wrong. That separation keeps wishes, rules, and scores from being confused.",
    },
    "objective-cost-function": {
        "run": "A parking controller compares two futures. Path A reaches the spot in 8 seconds but passes 6 centimeters from the wall and uses hard steering. Path B takes 12 seconds, stays 35 centimeters from the wall, and turns gently. If the cost counts only time, Path A wins because 8 is smaller than 12. Now write a fuller score: time in seconds plus 0.5 times steering effort plus a wall penalty. Give Path A steering effort 10 and wall risk 30 because 6 centimeters is close enough to scrape if the pose estimate is off. Give Path B steering effort 3 and wall risk 0. With wall weight 1.0, the totals become Path A: 8 + 0.5*10 + 1.0*30 = 43. Path B: 12 + 0.5*3 + 1.0*0 = 13.5. With wall weight 0, Path A scores 13 and beats 13.5. The chosen path changed because the scoreboard changed. But a wall clearance rule is not always a price. If the parking garage says clearance must be at least 10 centimeters, then Path A is illegal because 6 < 10, no matter how low its time cost is. A soft wall penalty trades wall risk against time; a hard wall constraint refuses the trade. Now use the thermostat from the course overview. The room target is 70 F. Plan A keeps temperatures 69, 70, 71 over three minutes and uses 3 heater units. Plan B keeps 67, 68, 70 and uses 1 heater unit. If the stage cost is temperature_error^2 + 0.2*heat, Plan A has tracking cost 1 + 0 + 1 plus heat 0.6, total 2.6. Plan B has tracking cost 9 + 4 + 0 plus heat 0.2, total 13.2. If energy weight rises to 5.0, Plan A adds 15 and scores 17, while Plan B adds 5 and scores 18; A still barely wins. If the terminal cost pays 20*(final_error)^2, both final errors are 1 and 0 respectively, so B wins despite worse early tracking. If comfort has a hard rule 68 <= temp <= 72, Plan B starts at 67 F and is rejected before scoring. The objective is not the human wish to park or heat well; it is the written measurement of what counts as better, plus any written lines that cannot be crossed.",
        "math": "A typical objective adds stage costs along the path and a terminal cost at the end: J = sum_k stage_cost(x_k,u_k) + terminal_cost(x_N). A parking stage cost might include 1.0*time_step + 0.5*steering_effort + w_wall*wall_risk. In a three-step path, that could mean stage_0 + stage_1 + stage_2 plus terminal alignment error. The weights are exchange rates: 0.5*steering_effort says one unit of steering effort is worth half a second of time in the written score. For the two parking paths, A has base score 8 + 0.5*10 = 13 before wall risk, and B has 12 + 0.5*3 = 13.5. The wall term adds 30*w_wall to A and 0 to B. Path A is chosen when 13 + 30*w_wall < 13.5, so w_wall < 0.5/30 = 0.0167. Any wall weight above 0.0167 flips the written choice to B. A hard clearance constraint is different: clearance_A = 0.06 meters, clearance_min = 0.10 meters, so clearance_A - clearance_min = -0.04 meters and A is infeasible before J is compared. In the thermostat run, stage_cost_k=(temp_k - 70)^2 + alpha*heat_k and terminal_cost=beta*(temp_3 - 70)^2. With alpha=0.2 and beta=0, J_A=(1+0+1)+0.2*3=2.6 and J_B=(9+4+0)+0.2*1=13.2. With alpha=5 and beta=0, J_A=2+15=17 and J_B=13+5=18. With alpha=5 and beta=20, if A ends at 71 and B ends at 70, then J_A=17+20*(1^2)=37 and J_B=18+20*(0^2)=18. If the hard comfort constraint is 68 <= temp_k <= 72, then Plan B's first temperature has residual 67 - 68 = -1 and B is infeasible even though its terminal value is good. The same measured temperatures support different choices because the written exchange rates and written constraints changed. The optimizer has not become careless; it follows the score and the feasibility rules. If damage, comfort, energy, or final error is absent from J and not forbidden by a constraint, the controller is free to ignore it. The boundary is proxy honesty: a cost cannot punish a mistake that never appears as a term or hard constraint.",
    },
    "horizon": {
        "run": "A delivery drone is 60 meters from the pad, flying 8 m/s, with 18 percent battery left. Each second of full-speed flight uses 2 percent battery and moves 8 meters. Each second of slow flight uses 1 percent battery and moves 4 meters. A three-second horizon sees only the next 24 meters. If the cost inside those 3 seconds is arrival progress plus battery use, full speed looks attractive: it moves 24 meters and spends 6 percent battery, leaving 12 percent. Slow flight moves only 12 meters and spends 3 percent, leaving 15 percent. But the landing zone has a crosswind band from 25 meters to 40 meters from the start, and crossing that band safely requires at least 14 percent battery so the drone can reject the gust while slowing. The short horizon ends just before the band, so it chooses the fast first command and enters the next plan with too little reserve. A five-second horizon reaches the end of the wind band under full speed: distance_5 = 5*8 = 40 meters and battery_5 = 18 - 5*2 = 8 percent. That is not merely expensive; it violates the 14 percent reserve rule. A ten-second horizon reaches the pad test too. Full speed would travel 80 meters, overshooting the 60 meter pad by 20 meters, while slow speed would be only 40 meters along and still in the wind band with 8 percent battery. Among those two crude modes, the longer horizon says neither simple plan is acceptable; the controller needs a shaped speed plan, a charging stop, or a different route. A thirty-second horizon sees the descent, the wind band, the battery reserve, and the need to slow before touchdown. It can choose slow flight first, not because slow is always better, but because the delayed wind cost is now visible before the first command is issued. The horizon is the length of future the controller is willing to put on the table; if the real danger appears after the table ends, the optimizer cannot price it.",
        "math": "A finite-horizon problem chooses actions for k = 0...N. With dt = 0.5 seconds and N = 6, the controller sees only 3 seconds. With N = 60, it sees 30 seconds. The short-horizon comparison is local: full speed gives distance_3 = 3*8 = 24 meters and battery_3 = 18 - 3*2 = 12 percent; slow speed gives distance_3 = 3*4 = 12 meters and battery_3 = 18 - 3*1 = 15 percent. If the model scores only the first 3 seconds, it may prefer 24 meters of progress. A medium horizon can change the status from attractive to illegal. At 5 seconds, full speed gives distance_5 = 40 meters and battery_5 = 8 percent, so battery_at_wind = 8 < 14 fails the reserve constraint. At 10 seconds, full speed gives distance_10 = 10*8 = 80 meters and overshoot_10 = 80 - 60 = 20 meters. Slow speed gives distance_10 = 10*4 = 40 meters and battery_10 = 18 - 10*1 = 8 percent, still below the wind reserve. The longer horizon adds the later constraint battery_at_wind >= 14 percent and the later terminal facts: touchdown speed, remaining battery, and final position. N is not just a number of samples; it decides whether delayed costs such as low battery, touchdown speed, or wind near the landing zone can enter the optimization before the first action is chosen. Too short is blind; too long can be expensive or misleading if the far future model is guessed. The practical test is the first consequence time: choose a horizon that reaches the first event that can change today's best action, and then ask whether the first action still leaves a legal future.",
    },
    "constraints": {
        "run": "A robot arm moving a camera around a shelf can save energy by cutting through the shelf corner. Suppose the gripper must stay at least 4 centimeters from the shelf and each joint motor is limited to 12 newton-meters of torque. Candidate A has low energy cost, but at t = 0.4 seconds its gripper is only 3 centimeters from the shelf, and at t = 0.6 seconds joint 2 asks for 15 newton-meters. Candidate B uses more energy, but its closest clearance is 5 centimeters and its largest torque is 11 newton-meters. If the objective only counts energy, Candidate A may look better. The constraint check rejects it before cost comparison because 3 < 4 and 15 > 12. Candidate B is not chosen because it is prettier; it is the first one still standing after the legal tests. Now suppose someone softens clearance into a small penalty of 2 points per missing centimeter. Candidate C uses only 4 energy points but passes 2 centimeters from the shelf, so its written score is 4 + 2*(4 - 2) = 8. Candidate B might cost 11 energy points. If clearance was meant to be hard, Candidate C must still be rejected, even though 8 < 11. There is also a smaller boundary story inside the same idea. If the wrist would like torque 14 because that minimizes (tau - 14)^2, the 12 newton-meter limit makes tau = 14 illegal. The best legal torque is tau = 12, where the upper torque constraint is active. At tau = 10, the same constraint is inactive because there is still 2 newton-meters of slack. From tau = 12, the optimizer may want to move upward, but that direction leaves the feasible interval; from tau = 10, both small upward and downward changes are still legal. Constraints are the lines a path must not cross, even when crossing them would lower the written score.",
        "math": "A constraint is an equation or inequality such as g(x,u) <= 0. Write clearance as g_clear,k = 0.04 - distance_to_shelf(x_k) <= 0. At Candidate A's closest point, distance_to_shelf = 0.03, so g_clear = 0.04 - 0.03 = 0.01 > 0; violation. Write torque as g_tau,k = abs(tau_k) - 12 <= 0. At 15 newton-meters, g_tau = 15 - 12 = 3 > 0; violation. Candidate B has distance 0.05, so g_clear = -0.01, and torque 11, so g_tau = -1; both pass. Candidate C has distance 0.02, so g_clear = 0.04 - 0.02 = 0.02 > 0. A soft penalty might add rho*max(0,g_clear), for example 100*0.02 = 2, but that is a design choice, not the same statement as g_clear <= 0. For the wrist example, minimize J(tau)=(tau - 14)^2 subject to -12 <= tau <= 12. The unconstrained minimizer is tau = 14, but it violates tau <= 12. At tau = 12, g_upper(tau)=tau - 12 = 0, so the upper bound is active. At tau = 10, g_upper(tau)=10 - 12 = -2, so that bound is inactive. Equality constraints work the same way but require exact matching, such as defect_k = x_{k+1} - f(x_k,u_k) = 0. These legal tests are not optional penalties unless the problem designer deliberately makes them soft. A hard constraint says the candidate is outside the feasible set, not merely expensive. This is why feasibility is checked before ranking any path. The boundary is honesty: if shelf flex, cable snag, heat, or human clearance is absent from the constraint set, the optimizer is allowed to ignore it.",
    },
    "feasibility": {
        "run": "A car is 18 meters behind a stopped truck, moving 22 m/s, with a wet-road braking limit of 6 m/s^2. Full braking needs roughly v^2/(2a) = 22^2/(2*6) = 40.3 meters before the car stops, so braking straight ahead still reaches the truck. Try the other obvious family of actions: steer left. The next lane has a box truck beside the car with only 0.5 meters of side clearance, while the safety rule requires 1.5 meters. Try steering right: a concrete barrier is 0.8 meters away and the rule again requires 1.5 meters. Try accelerating: the closing speed only increases. In that state, the question is not which plan is best. The feasible set may already be empty because no allowed braking, steering, or acceleration sequence avoids the blocked space. Move the same car back to 45 meters behind the truck and the straight-brake family changes status: 40.3 <= 45 is true, leaving 4.7 meters of stopping margin. Now the feasible set is not empty, even if braking is uncomfortable and expensive. A cheap collision path is not a plan with a high cost; it is outside the legal set. Now expose a modeling mistake. Suppose the road also has a legal shoulder opening 12 meters ahead, but the first model did not include the shoulder lane as an action family. A two-step escape can brake hard for 0.5 seconds, dropping speed from 22 to 19 m/s and using about 10 meters, then steer into the shoulder opening with 2.0 meters of side clearance. That plan is still scary, but it satisfies the written clearance rule and avoids the truck. The old empty set was true for the old model, not for the richer action set. The controller should report the emergency boundary when the set is empty, not pretend optimization found a winner.",
        "math": "The feasible set contains states and actions satisfying dynamics, bounds, and path constraints. In symbols, a horizon plan is feasible only if each x_{k+1}=f(x_k,u_k), each u_k stays within actuator limits, and every clearance and speed constraint is satisfied. For this state x_0, the straight-brake candidate violates stop_distance <= 18 because 40.3 <= 18 is false. The left-lane candidate violates clearance_left >= 1.5 because 0.5 >= 1.5 is false. The right-lane candidate violates clearance_right >= 1.5 because 0.8 >= 1.5 is false. If those are the only action families available over the short horizon, F_old(x_0) = empty set. For a different state x_safe with truck_distance = 45 meters, the same braking candidate satisfies stop_distance <= 45 because 40.3 <= 45 is true, so F(x_safe) contains at least the full-brake plan. With the shoulder action added, define u_shoulder as brake for 0.5 seconds then steer right into the opening. The first half-second speed check is v_1 = 22 - 6*0.5 = 19 m/s. A rough distance update gives d_used = 0.5*(22 + 19)*0.5 = 10.25 meters, leaving 18 - 10.25 = 7.75 meters before the truck while the car reaches the shoulder opening. The shoulder clearance is 2.0 >= 1.5, so u_shoulder belongs to F_new(x_0). Optimization then has a legal candidate to compare. This is different from a merely expensive plan: a plan with J = 10,000 can still be feasible if it obeys the constraints, while an illegal plan with J = 1 cannot be chosen. The boundary is model honesty and horizon length. If the state forgot a shoulder lane, or the horizon is too short to see a later escape gap, the computed empty set may describe the model rather than the road.",
    },
    "static-optimization": {
        "run": "A delivery robot is plugged in for one hour before its next route. The engineer must choose one charging power z for that hour, not a changing sequence. Low power leaves the battery short; high power heats the pack. Suppose the desired power is 6 kilowatts, but the wall outlet allows at most 4 kilowatts and the battery maker says heat rises sharply above 5 kilowatts. A simple snapshot objective is J(z) = (z - 6)^2, with the legal set 0 <= z <= 4. Without the outlet constraint, the best snapshot answer is z = 6 because the error is zero. But z = 6 is not legal. Inside the legal interval, J(4) = (4 - 6)^2 = 4, J(3) = 9, and J(0) = 36, so z = 4 is the best legal static decision. The answer is not a story about motors, road grade, or future traffic. It is just one number chosen from a legal interval. But now add temperature: after 20 minutes at z = 4, suppose battery temperature rises from 30 C to 46 C, above a 45 C limit, while z = 3 keeps it at 42 C. That is no longer the same static problem unless the heat constraint was already folded into the legal set. If a fixed cooling fan is always on, the engineer can precompute temperature_after_20_min(z) for each constant z and keep a static constraint. For example the fan may make z = 3.5 end at 44 C and score J(3.5)=6.25, while z = 4 still fails heat. Compare the surviving candidates: z = 3 has score 9 and z = 3.5 has score 6.25, so the best legal static choice becomes 3.5 kilowatts. But if the controller can change power after 10 minutes because the pack cooled faster than expected, the next temperature becomes a state for the next decision. Then the one-shot calculation becomes one piece inside a sequence. Static optimization is the one-shot grammar: name the decision, score each legal candidate, reject illegal candidates, and choose the best legal candidate.",
        "math": "A finite-dimensional static problem has the form minimize_z J(z) subject to g_i(z) <= 0 and h_j(z) = 0. In the charging example, g_1(z)=z-4 <= 0 and g_2(z)=-z <= 0 describe the interval 0 <= z <= 4. The unconstrained stationary point solves dJ/dz = 2*(z - 6) = 0, giving z = 6, but feasibility rejects it. The constrained optimum sits on the active outlet boundary z = 4. If temperature must be handled in the same snapshot, add a static inequality such as g_heat(z)=temperature_after_20_min(z)-45 <= 0; then z = 4 is rejected if g_heat(4)=46-45=1 > 0, and z = 3 can become the best legal point. With a fixed cooling fan, the map might say g_heat(3.5)=44-45=-1 <= 0 and g_heat(4)=46-45=1 > 0, so z = 3.5 is legal and closer to the desired 6 kilowatts than z = 3. The fan is not a second decision; it is baked into the fixed map being checked. This is still static only if temperature_after_20_min(z) is a fixed map from this one decision to a checked outcome. If the controller can change power after each 10 minute interval, the state update has the form temperature_next = f(temperature,z), and the problem has become control. The boundary is exactly there: if the consequence of z changes the next condition that future decisions see, a static problem is only a subproblem inside control.",
    },
    "gradient-first-order-condition": {
        "run": "A rover is choosing one steering correction z in degrees for the next planning snapshot. The written cost is J(z) = (z - 3)^2 + 0.2*z^2: miss the desired 3 degree turn, but also avoid using too much steering. At z = 0, the slope is dJ/dz = 2*(0 - 3) + 0.4*0 = -6. A tiny positive move, delta z = +0.1, is predicted to change cost by about -6*0.1 = -0.6, so the rover should move right. At z = 2.5, the slope is dJ/dz = 2*(2.5 - 3) + 0.4*2.5 = 0. The first-order test says that, to first order, a tiny move left or right does not lower the cost. Check the numbers: J(2.4) = (2.4 - 3)^2 + 0.2*2.4^2 = 1.512, J(2.5) = 1.5, and J(2.6) = 1.512. The point is locally best for this smooth one-variable score. Now add a steering stop z <= 2.0. At z = 2.0, the slope is dJ/dz = 2*(2 - 3) + 0.4*2 = -1.2, so the written cost would like a positive move. But delta z = +0.1 is illegal because it crosses the stop. The best legal answer can sit at the boundary with nonzero slope. The opposite warning is a flat point that is not good. For K(z)=-(z - 2)^2 + 5, the slope at z = 2 is zero, but K(1.9)=4.99 and K(2)=5.0, so z=2 is a local maximum for a cost-minimization problem. A zero first derivative found a candidate, not the answer. In two knobs, the same idea is not 'make every number bigger.' Suppose the rover also chooses a speed trim s and the local gradient at (z,s)=(1,0) is grad J = [-2, 4]. A small change delta = [0.1, -0.1] has dot product -2*0.1 + 4*(-0.1) = -0.6, so it is predicted downhill. A different change delta = [0.1, 0.1] gives -2*0.1 + 4*0.1 = +0.2, so it is predicted uphill even though steering moved the helpful way. At a saddle, the gradient can vanish too. For S(z,s)=z^2 - s^2, grad S(0,0)=[0,0], but moving in the s direction by delta=[0,0.1] changes cost by about -0.01, while moving in the z direction by delta=[0.1,0] changes it by about +0.01. First order is silent there; the second-order shape decides. But if a rock begins at steering above 2.3 degrees and the cost forgot collision, even the unconstrained stationary point z = 2.5 can satisfy the gradient condition while the rover still hits the rock.",
        "math": "First-order reasoning starts with the small-displacement formula from the transcript: J(z + delta z) is approximately J(z) + grad J(z)^T delta z. If some legal delta z makes grad J(z)^T delta z < 0, then that move lowers cost to first order, so z is not a local minimum. For an unconstrained smooth local minimum, every tiny direction is legal; the only way to avoid a downhill direction is grad J(z) = 0. With constraints, the condition changes: downhill directions that leave the legal set do not count. At the steering stop z <= 2.0, a feasible tiny move must satisfy delta z <= 0. Since grad J(2.0) = -1.2, the first-order change for delta z = -0.1 is (-1.2)*(-0.1)=+0.12, an increase. The downhill move delta z = +0.1 would give -0.12, but it is illegal. That is why a constrained local minimum can have a nonzero gradient. For the smooth steering cost, the second derivative is d^2J/dz^2 = 2 + 0.4 = 2.4, so the stationary point is a local bowl. For K(z)=-(z - 2)^2 + 5, the second derivative is d^2K/dz^2 = -2, so the stationary point is a hilltop for minimization. For several decision variables, the gradient is a price list for tiny changes. With grad J = [-2, 4], the direction delta = [0.1, -0.1] has grad J^T delta = -0.6, while delta = [0.1, 0.1] has grad J^T delta = +0.2. The sign of the dot product, not the sign of one coordinate, says whether that whole small move helps. At S(z,s)=z^2 - s^2, grad S(0,0)=[0,0], but the Hessian has one positive and one negative direction. In numbers, S(0,0.1)=-0.01 and S(0.1,0)=+0.01. The test tells you where to look next, not where to stop thinking. The boundary of the idea is localness and model honesty: grad J = 0 is a filter for candidates, not proof of global optimality, safety, or mission success.",
    },
    "calculus-of-variations": {
        "run": "A small inspection robot must move along a 1 meter rail in 2 seconds. The decision is not one number. It is the whole velocity curve u(t) from t = 0 to t = 2. One candidate drives at 0.5 m/s for the whole trip, so x(2) = 1 meter. Another candidate surges to 0.8 m/s during the first second and slows to 0.2 m/s during the second; it also reaches 1 meter, but it spends more effort. If the path cost is J[u] = integral_0^2 u(t)^2 dt, the constant-speed curve costs 2*(0.5^2) = 0.5. The surge-then-slow curve costs 1*(0.8^2) + 1*(0.2^2) = 0.68. Now test the surge curve by a tiny legal reshaping: reduce the first-second speed by 0.1 m/s and add the same 0.1 m/s to the second second. The distance is unchanged because -0.1*1 + 0.1*1 = 0. But the cost becomes 1*(0.7^2) + 1*(0.3^2) = 0.58, so the old curve was not even locally settled. Now add a speed limit u(t) <= 0.75 m/s. The original surge at 0.8 m/s was never admissible, no matter how nice the variation argument looks. A legal two-block curve might use 0.75 m/s for the first second and 0.25 m/s for the second; it still travels 1 meter and costs 1*(0.75^2) + 1*(0.25^2) = 0.625. The same smoothing nudge by 0.1 gives 0.65 and 0.35, still legal, with cost 1*(0.65^2) + 1*(0.35^2) = 0.545. Calculus of variations asks that question for every small shape eta(t), not only for this two-block nudge. If every admissible bump makes the first-order change zero or positive, the curve is a stationary candidate. The object being tested is the full signal, not one steering angle or one power setting.",
        "math": "A functional maps a function to a number, for example J[u] = integral_0^2 u(t)^2 dt. A variation replaces u(t) by u(t) + epsilon*eta(t), where eta(t) is a small shape change and epsilon is the size of the nudge. The first variation is d/depsilon J[u + epsilon*eta] evaluated at epsilon = 0. For J[u], this derivative is integral_0^2 2*u(t)*eta(t) dt. For the rail example without dynamics beyond x_dot = u and fixed endpoint x(2)=1, admissible eta must satisfy integral_0^2 eta(t) dt = 0 so the final position does not move. The constant curve u(t)=0.5 has first variation integral_0^2 2*0.5*eta(t) dt = integral_0^2 eta(t) dt = 0 for every endpoint-preserving eta. The surge curve does not. Choose eta(t)=-1 on the first second and eta(t)=+1 on the second. Then integral eta dt = 0, but the first variation is 2*0.8*(-1)*1 + 2*0.2*(+1)*1 = -1.2. A small positive epsilon lowers cost, which matches the concrete move from 0.68 down to 0.58. With the speed bound u(t) <= 0.75, the 0.8/0.2 curve is outside the legal set. The 0.75/0.25 curve has cost 0.625, and the same eta with epsilon = 0.1 gives 0.65/0.35, endpoint change (-0.1)*1 + (+0.1)*1 = 0, and cost 0.545. The word admissible carries all of that: the perturbation must preserve the endpoint and stay inside path limits. The boundary is smooth admissible perturbations: jumps, impacts, hard switching limits, and hidden state constraints can break the clean variation argument.",
    },
    "costate-adjoint-variable": {
        "run": "A small elevator cart must reach height 10 meters after two seconds. Its simplified motion is x_next = x + u, where u is the upward move chosen for one second. The final penalty is 100*(x_2 - 10)^2, so being 0.1 meters low at the end costs 100*(0.1^2) = 1. At the last second, if the cart is at x_1 = 9.4 meters and can choose u_1, the terminal error after the move is x_1 + u_1 - 10. The derivative of final penalty with respect to x_1 is 200*(x_1 + u_1 - 10). If the planned u_1 is 0.5, the final height is 9.9 and the derivative is -20. That number is the backward price of height at time 1: one extra meter of height at x_1 would lower final penalty by about 20. Now add a running penalty 5*(x_1 - 9.5)^2 for being away from the hallway-safe height at time 1. At x_1 = 9.4, its derivative is 10*(9.4 - 9.5) = -1, so the total price at time 1 becomes -21. Now give the cart two state coordinates: height h and velocity v. From h_1=9.4, v_1=0.2, and acceleration a_1=0.3, use h_2=h_1+v_1+0.5*a_1=9.75 and v_2=v_1+a_1=0.5. If the terminal cost is 50*(h_2-10)^2 + 5*v_2^2, the terminal price is not one number. The height price is -25 and the velocity price is 5. Pulled back to time 1, lambda_h1=-25 and lambda_v1=-20 because velocity affects both next height and next velocity. If the cart is low or fast earlier, that early error matters because dynamics carry it into both the time-1 running cost and the final cost, and in the two-state version into later height and later velocity. The costate is this future price carried backward through the dynamics, so a present control can be judged by what it does to tomorrow's expensive state.",
        "math": "In continuous time, the lecture introduces p(t) as the time-varying analog of Lagrange multipliers for the dynamics constraint. Finite-dimensional multipliers price violations of algebraic constraints; the costate prices violations of x_dot = f(x,u) all along the trajectory. In a simple discrete picture, lambda_2 = d terminal_cost/dx_2 = 200*(x_2 - 10). If x_2 = 9.9, then lambda_2 = -20. Because x_2 = x_1 + u_1 has derivative dx_2/dx_1 = 1, the previous future price is lambda_2*1 = -20. If there is no extra running state cost, lambda_1 = -20. With running cost l_1(x_1)=5*(x_1 - 9.5)^2, add dl_1/dx_1 = 10*(9.4 - 9.5) = -1, so lambda_1 = -20 + (-1) = -21. If the dynamics had x_2 = 0.5*x_1 + u_1, the same terminal price would come back as lambda_2*0.5 = -10 before adding any running-cost derivative. For the two-coordinate check, x=[h,v] and terminal_cost=50*(h_2-10)^2 + 5*v_2^2. At h_2=9.75 and v_2=0.5, the terminal gradient is lambda_2=[100*(9.75-10), 10*0.5]=[-25, 5]. The Jacobian of the step h_2=h_1+v_1+0.5*a_1, v_2=v_1+a_1 with respect to [h_1,v_1] is [[1,1],[0,1]]. Pulling back gives lambda_1 = [[1,0],[1,1]]*[-25,5] = [-25,-20]. The velocity price is different from the height price because one meter per second of extra velocity changes both final height and final velocity. The boundary is model trust: a costate is only the price inside the written dynamics and written cost, not a moral price for omitted heat, collision, or actuator wear.",
    },
    "hamiltonian-optimal-control": {
        "run": "A vertical cart is at height x and chooses upward thrust u for the next instant. Using thrust is costly now: the running cost is 0.5*u^2. But thrust also changes the next height through x_dot = u, and the costate says how valuable height is for the future. Suppose the backward price is p = -20, meaning one extra meter of height would reduce future penalty by about 20. The Hamiltonian puts the two local effects in one expression: H = 0.5*u^2 + p*u. Try u = 0: H = 0. Try u = 10: H = 50 - 200 = -150. Try u = 20: H = 200 - 400 = -200. Try u = 30: H = 450 - 600 = -150. The best local balance in this smooth unconstrained example is u = 20. Now add a motor cap u <= 12. The old answer is not available. At the cap, H(12)=0.5*12^2 - 20*12 = 72 - 240 = -168. That is worse than the illegal H(20)=-200 but better than the legal H(10)=-150, so the constrained local choice sits at u = 12. Now change only the future price. If the cart is almost on target, let p = -4. Then H(u)=0.5*u^2 - 4*u, and the unconstrained balance is u = 4, not 20. Check the numbers: H(0)=0, H(4)=8-16=-8, and H(12)=72-48=24, so the cap is legal but no longer attractive. If the cart is already too high and extra height is bad, use p = +6. Then H(u)=0.5*u^2 + 6*u, so every positive thrust raises the local account; with u >= 0, the best local choice is u = 0. These three cases use the same motor and the same running cost. Only the backward price changed. That is the point: the Hamiltonian is not a new physical energy here. It is the local accounting sheet that prices one control by immediate cost plus the future value of the state motion it creates.",
        "math": "For dynamics x_dot = f(x,u) and running cost L(x,u), the Hamiltonian is H(x,u,p)=L(x,u)+p*f(x,u). In the cart example, L = 0.5*u^2 and f = u, so H(u)=0.5*u^2 - 20*u when p=-20. The stationarity condition is dH/du = u - 20 = 0, giving u = 20. This is the same balance seen by checking H(10), H(20), and H(30). With the constraint u <= 12, stationarity at u = 20 is not a legal candidate. The derivative at the cap is dH/du at u=12 = 12 - 20 = -8, which means the Hamiltonian would still go down if u could increase, but increasing u is forbidden. Over the legal interval, the best point is therefore the active boundary u^* = 12. With p=-4, the derivative is dH/du = u - 4, so stationarity gives u=4. Since 0 <= 4 <= 12, the cap is inactive and the local choice is the interior point. With p=+6, the derivative is dH/du = u + 6. It is positive for every legal u >= 0, so the minimum over 0 <= u <= 12 is the lower boundary u=0. The lecture's phrase 'augment the cost with the constraint' is doing exactly this: the dynamics constraint is multiplied by the costate p(t), then added to the local cost so the control choice sees both fuel and future state price. The Hamiltonian condition is local in time, while the costate came from the rest of the trajectory. If the next part of the path changes because a target, obstacle, or terminal penalty changes, p(t) changes and the local thrust can change even with the same engine. The boundary is necessary-condition thinking. If the model omits motor heat, the Hamiltonian can balance the wrong local accounting sheet; if the active-control rule is forgotten, a clean derivative-zero answer can be illegal; if someone checks only one time instant, they have not proved the whole path is best.",
    },
    "indirect-methods": {
        "run": "A rail cart must move from x(0)=0 meters to x(2)=1 meter while using little effort. The dynamics are x_dot = u, and the running cost is 0.5*u^2. A direct method would choose many grid values for x and u and enforce the dynamics between grid points. An indirect method first asks what any smooth optimum must obey. It introduces a costate p(t), builds the Hamiltonian H = 0.5*u^2 + p*u, and sets the local stationarity condition dH/du = u + p = 0. That gives u = -p. The costate equation gives p_dot = 0, so p is constant. Now the whole family of candidate paths is controlled by one missing number: the initial costate. If p(0) = -0.3, then u = 0.3 for the whole run and x(2)=0.6, so the cart is 0.4 meters short. If p(0) = -0.7, then u = 0.7 and x(2)=1.4, so it overshoots by 0.4 meters. Those two misses are useful because they put the correct shot between -0.3 and -0.7. Trying the midpoint p(0) = -0.5 gives u = 0.5, reaches x(2)=1.0 exactly, and produces x(t)=0.5*t. Now change the problem: the final position is free, but missing the mark is penalized by phi(x(2))=10*(x(2)-1)^2. The endpoint is no longer forced to equal 1. Instead the final costate must match the terminal price, p(2)=dphi/dx=20*(x(2)-1). If p is constant and u=-p, then p(2)=p0 and x(2)=-2*p0. The boundary condition becomes p0 = 20*(-2*p0 - 1), so 41*p0 = -20 and p0=-20/41=-0.488. The cart reaches x(2)=40/41=0.976, slightly short, because the method trades effort against final error instead of treating the target as a hard wall. The indirect method did not search over every grid point. It derived the equations of a candidate optimum, guessed or solved the missing boundary value, simulated the resulting path, measured the terminal miss, and adjusted the guess until the boundary rule was met.",
        "math": "The standard indirect pattern is derive first, solve second. From a continuous optimal-control problem, form H(x,u,p)=L(x,u)+p*f(x,u). Then write the necessary conditions: x_dot = partial H/partial p, p_dot = -partial H/partial x, partial H/partial u = 0, plus boundary conditions such as x(0)=0 and x(2)=1. In the rail-cart example, partial H/partial u = u+p=0 expresses control as u=-p, and p_dot=0 makes p constant. The boundary residual is r(p0)=x(2;p0)-1. Trying p0=-0.3 gives r=-0.4; trying p0=-0.7 gives r=+0.4; the sign change says a zero residual lies between them. Because x(2;p0)=-2*p0 in this example, r(p0)=-2*p0-1, so the root is p0=-0.5. That is a shooting method: choose the unknown initial costate, integrate x_dot and p_dot forward, then compare the terminal state with the required endpoint. For the free-endpoint variant, the residual is different. The final position residual is not x(2)-1; the boundary residual is b(p0)=p(2)-20*(x(2)-1). Since p(2)=p0 and x(2)=-2*p0, b(p0)=p0-20*(-2*p0-1)=41*p0+20, whose zero is p0=-20/41. The two problems use the same dynamics and Hamiltonian, but different boundary conditions produce different controls. A fixed endpoint says hit x(2)=1 exactly; a terminal penalty says stop when the marginal effort price and marginal miss price balance. The strength is a small structured boundary-value problem. The boundary is fragility. If a path limit such as x(t) <= 0.8 becomes active before t=2, the smooth unconstrained equations above no longer describe the whole answer. If the Hamiltonian was derived with the wrong sign, or the first costate guess lands far from the root, the method can miss the solution even though the original control problem still has one.",
    },
    "value-function": {
        "run": "A rover starts at state S beside a rocky shortcut and a smooth detour. The rocky shortcut costs 1 minute now and moves the rover to state R, where the wheels are damaged. From R, the remaining best trip to the charger has already been computed as V(R)=18 minutes. The smooth detour costs 4 minutes now and moves the rover to state H, where the wheels are healthy and the remaining best trip is V(H)=7 minutes. If the rover looks only at the next move, it chooses the shortcut because 1 is smaller than 4. If it reads the value of the next state, it compares 1 + 18 = 19 against 4 + 7 = 11 and chooses the smooth route. The value of a state is that stored future burden. It lets the present decision inherit work that was solved downstream. The number is attached to the state, not to the path label: if another road also leads to damaged state R, that road inherits the same V(R)=18 because the future from R is the same once the rover is there. Now change one real fact. Suppose a field mechanic opens near R, and the best remaining trip from the damaged-wheel state drops to V_repaired(R)=9 because the rover can spend a short stop getting safe wheels before the hard climb. The same rocky first move now scores 1 + 9 = 10, which beats smooth 11. The shortcut was not permanently good or bad. Its first cost stayed at 1; the stored future price changed because the downstream world changed. If a different road also reaches R, that road also reuses V_repaired(R)=9. That reuse is the whole point: solve the future once for a state, then let every earlier choice that lands there borrow the answer.",
        "math": "V(x) stores the best future cost from state x under the written dynamics, cost, constraints, and policy class. Once V is known, a current action can be judged by immediate cost plus the value of the next state it creates: choose u by comparing cost(x,u) + V(f(x,u)). In the rover run, f(S,rocky)=R and f(S,smooth)=H. The action scores are Q(S,rocky)=1+V(R)=1+18=19 and Q(S,smooth)=4+V(H)=4+7=11, so V(S)=11 and the first action is smooth. If the repair option is part of the problem, the stored value at the same damaged-wheel state is V_repaired(R)=9. Then Q(S,rocky)=1+9=10 and the minimum becomes V(S)=10 with rocky first, because 10 is smaller than the smooth score 11. If someone stores V(R)=6 because the wheel damage was ignored, the same calculation becomes 1 + 6 = 7 against 11 and the rover chooses the damaging shortcut for the wrong reason. The formula did not fail; the stored future price described the wrong state or the wrong world. In a deterministic cost-minimizing problem, the full value relation is V(x)=min_u [cost(x,u) + V(f(x,u))]. In a reward version, the sign changes but the idea is the same: a number attached to a state summarizes the best future consequence from that state. The boundary is representation. If battery heat, wheel damage, traffic, or a locked gate changes the future but is not in x, then one stored V(x) is being asked to price several different futures. If the map, repair station, cost, or allowed policy changes, the value table must be recomputed or clearly labeled as belonging to the old problem.",
    },
    "bellman-recursion": {
        "run": "A warehouse robot stands at a junction state x = J and can enter aisle A or aisle B. Aisle A costs 2 seconds now and leaves the robot in state C, a crowded aisle whose stored future value is V(C)=9. Aisle B costs 5 seconds now and leaves the robot in state L, a clear lane whose stored future value is V(L)=3. The Bellman step is one local backup. It does not list every route to the loading dock. It asks: if I take one legal action, what immediate cost do I pay, and what future value is already stored at the state I create? For A, the backup is 2 + V(C) = 2 + 9 = 11. For B, it is 5 + V(L) = 5 + 3 = 8. The recursion stores V(J)=8 and pi(J)=B. If later another state points into J, that earlier state can reuse V(J) without reopening both aisles. If a later pass discovers that the clear lane L is blocked and its value should be V(L)=14, the same backup changes B to 5 + 14 = 19 and the junction switches to A. Now add a deadline so the word future has teeth. At time t=1, a scanner robot at shelf state S has one step left. slow_scan costs 4 and reaches goal, whose terminal value is V_2(goal)=0. rush costs 1 but often drops the item into wrong_shelf, whose terminal value is V_2(wrong_shelf)=40. The one-step backup at S compares 4 + 0 = 4 with 1 + 40 = 41, so V_1(S)=4 and pi_1(S)=slow_scan. Bellman recursion is the one-step accounting identity that makes dynamic programming reusable, but reuse only helps when the stored numbers are consistent with the current problem.",
        "math": "In deterministic form, the backup is V(x) = min_u [c(x,u) + V(f(x,u))]. The action that attains the minimum becomes the policy at that state: pi(x) = argmin_u [c(x,u) + V(f(x,u))]. In the junction example, Q(J,A)=2+V(C)=11 and Q(J,B)=5+V(L)=8, so V(J)=min(11,8)=8 and pi(J)=B. After the blocked-lane correction, Q(J,B)=5+14=19, so V(J)=min(11,19)=11 and pi(J)=A. That is why the Bellman equation is a consistency equation, not just a calculator button. In a finite backward pass, terminal values are fixed first, such as V(goal)=0, then earlier states are backed up from those fixed values. With time indexed, the deterministic equation is V_k(x)=min_u [c_k(x,u)+V_{k+1}(f_k(x,u))]. The scanner example uses V_2(goal)=0 and V_2(wrong_shelf)=40 before computing V_1(S). The backup is Q_1(S,slow_scan)=4+V_2(goal)=4 and Q_1(S,rush)=1+V_2(wrong_shelf)=41, so V_1(S)=min(4,41)=4. This is why time may need to be part of the state: shelf S with one step left is not the same situation as shelf S with ten steps left. If the page collapses both into the same stored value, it can recommend rush because it forgot the deadline. In an infinite-horizon or cyclic problem, repeated backups keep changing values until the left side V(x) and the right side min expression agree. The stored value is allowed to hide the rest of the route only because state C, state L, or the time-indexed shelf state contains everything that matters next. It is not allowed to hide a battery warning, locked door, loaded pallet, or deadline that changes the future but was left out of the state. With uncertainty, the single next value becomes an expectation: V(x)=min_u [c(x,u)+sum_{x_next} P(x_next|x,u)V(x_next)]. The boundary is state truth and value consistency. If V(C)=9 was computed with a different cost, missing obstacle, or stale map, the Bellman step will faithfully reuse a wrong future price.",
    },
    "direct-transcription": {
        "run": "A robot arm must move from joint angle 0.0 rad to 1.2 rad in 0.6 seconds while staying under a 5 newton-meter torque limit. Direct transcription does not ask for a smooth curve in one piece. It creates grid variables at t = 0.0, 0.2, 0.4, and 0.6 seconds: joint angle q, joint velocity v, and torque tau at each point. A first optimizer guess might write q_0=0.0, q_1=0.4, q_2=0.9, q_3=1.2. That looks like progress, but the grid is not trusted just because the numbers rise. At t = 0.2, suppose q_1=0.4 rad, v_1=1.0 rad/s, tau_1=2 newton-meters, and the simple step model predicts q_2_pred = 0.6 rad at t = 0.4. If the next grid variable says q_2=0.9 rad, the defect is q_2 - q_2_pred = 0.9 - 0.6 = 0.3 rad. That defect must be driven to zero or the path is a drawing, not a real arm motion. If the optimizer tries to fix the defect by setting tau_1=8, the torque bound rejects that repair because 8 > 5. A legal repair can instead move the exposed grid state to q_2=0.6 while keeping tau_1=2, making q_2 - q_2_pred = 0.6 - 0.6 = 0. Now make the repair less fake. Suppose tau_1=5 predicts q_2_pred = 0.75. Moving q_2 from 0.9 to 0.75 gives zero defect and still obeys the torque bound. Keeping q_2=0.9 would need tau_1=8, which fixes dynamics on paper but breaks the actuator limit. The same grid also carries path constraints. If a fixture requires q <= 0.80 at t = 0.4, then the false q_2=0.9 violates the path bound before the endpoint is even considered. If the repair sets q_2=0.75, both the defect and the path bound pass. Notice what did not happen: the endpoint q_3=1.2 did not excuse a false middle point. Direct transcription checks the route, not only the finish. Direct transcription is powerful because the optimizer can move middle states and controls together; it is disciplined because every move must pass the defect and bound checks. It turns a continuous-time story into a finite list of numbers, but the list must still prove that each neighboring pair could really follow from the model.",
        "math": "The continuous path becomes decision variables x_0...x_N and u_0...u_N. For the arm, x_k=[q_k,v_k] and u_k=tau_k. A common transcription first picks a mesh spacing h = 0.2 seconds and assumes zero-order hold: tau(t)=tau_k for t_k <= t < t_{k+1}. With Euler integration, x_{k+1} = x_k + h*f(x_k,u_k). A defect constraint has the form defect_k = x_{k+1} - step(x_k,u_k), where step(x_k,u_k)=x_k + h*f(x_k,u_k). In the scalar angle check, defect_1 = q_2 - q_2_pred = 0.3 rad, so the candidate violates defect_1 = 0. The illegal torque repair has tau_1=8, which violates -5 <= tau_k <= 5. The state repair has q_2=0.6, so defect_1 = 0.6 - 0.6 = 0 while tau_1 remains inside the torque bound. A mixed repair can change both variables: tau_1=5 gives q_2_pred=0.75, and choosing q_2=0.75 gives defect_1 = 0.75 - 0.75 = 0 with tau_1 at the active torque boundary. Choosing q_2=0.9 with the same legal tau_1=5 leaves defect_1 = 0.9 - 0.75 = 0.15, so the grid state still lies. If only q_0=0 and q_3=1.2 were checked, the false middle value q_2=0.9 could survive. Add the path inequality q_2 <= 0.80 and the false middle point fails twice: defect_1 = 0.15 and path_residual = q_2 - 0.80 = 0.10. The repaired q_2=0.75 has path_residual = -0.05, so the path bound is satisfied with 0.05 rad of margin. The defect check is the written proof that the middle step came from the model. Direct transcription asks the optimizer to choose all grid states and controls while also enforcing defect_k = 0, torque bounds, endpoint constraints q_0=0 and q_3=1.2, and collision constraints. The grid points are therefore not independent dots; they are tied by equations that make neighboring states obey real dynamics. The difference from shooting is where the handles are. Shooting chooses controls and simulates states from them. Direct transcription also exposes states as variables, then uses defects to stop those exposed states from lying. The boundary is grid honesty. If a collision happens between t = 0.2 and t = 0.4 but no constraint samples it, the transcription can satisfy every written defect and still miss the physical problem.",
    },
    "shooting-methods": {
        "run": "A small test cart starts at x = 0 meters with v = 0 m/s and must stop at x = 10 meters after 2 seconds. Use dt = 1 second and let the optimizer choose only two acceleration commands, u_0 and u_1. Try u_0 = 4 m/s^2 and u_1 = -1 m/s^2. With a simple update that changes velocity first and then moves the cart, the first command gives v_1 = 4 m/s and x_1 = 4 meters. The second command gives v_2 = 3 m/s and x_2 = 7 meters, so the cart is still 3 meters short and still moving. Change the shot to u_0 = 6 m/s^2 and u_1 = -2 m/s^2. Now v_1 = 6, x_1 = 6, v_2 = 4, and x_2 = 10. The cart reaches the mark but fails the stop condition because v_2 is still 4 m/s. A corrected shot is u_0 = 10 m/s^2 and u_1 = -10 m/s^2. It gives v_1 = 10, x_1 = 10, v_2 = 0, and x_2 = 10, so both endpoint errors are zero. The optimizer cannot move x_1 or x_2 by hand. It changes the guessed controls, simulates again, and reads the endpoint miss in both position and speed. The corrected shot is not automatically best; it may use too much effort or violate an acceleration bound such as |u_k| <= 8. If the cart must avoid a camera cable between x = 5.0 and x = 5.5 meters, shooting can only check that cable after the simulated states appear. That is why shooting is small and natural when controls are the main unknown, but awkward when many state limits must be enforced along the way.",
        "math": "In shooting, only u_0 and u_1 are decision variables in this two-step example. The states are produced by repeated dynamics such as v_{k+1}=v_k + dt*u_k and x_{k+1}=x_k + dt*v_{k+1}. The endpoint residual can be written as residual r = [x_2 - 10, v_2 - 0]. For the first shot, r = [7 - 10, 3 - 0] = [-3, 3]. For the second shot, r = [10 - 10, 4 - 0] = [0, 4]. For the corrected shot, u=[10,-10], v_1=10, x_1=10, v_2=0, x_2=10, and r=[10 - 10, 0 - 0]=[0,0]. If the effort cost is J_u = u_0^2 + u_1^2, this successful shot costs 10^2 + (-10)^2 = 200, while the second shot costs 6^2 + (-2)^2 = 40 but misses the stop condition. If the actuator bound is |u_k| <= 8, the successful endpoint shot is illegal even though r is zero. The optimizer changes u, integrates forward again, and tries to drive r toward zero while reducing cost and respecting bounds. Single shooting makes one long chain from the initial state to the end, so a small early control change can move every later state. Multiple shooting shortens that chain: introduce a join state x_join at t = 1 second, simulate each shorter piece, and add a matching condition such as gap_1 = x_join - step(x_0,u_0). For example, if u_0=4 then step(x_0,u_0) gives x_1=4 and v_1=4. If the optimizer proposes x_join=(5,4), the join gap is [5 - 4, 4 - 4] = [1,0], so the two pieces do not connect. If it proposes x_join=(4,4), the join gap is [0,0] and the second piece can start from a state the first piece actually reaches. The join state is not free to lie; the gap must go to zero. The benefit is that the optimizer gets handles in the middle while dynamics still decide whether the pieces connect.",
    },
    "collocation": {
        "run": "A robot arm must swing around a fixture between t = 0.0 and t = 0.4 seconds. The endpoints can look legal: the gripper is left of the fixture at x = 0.02 meters at the start and right of it at x = 0.18 meters at the end. Endpoint-only checking says the move clears the fixture. Collocation adds a midpoint at t = 0.2 seconds. If the polynomial path puts the gripper at x = 0.10 meters while the fixture occupies x = 0.08 to 0.12 meters, the midpoint exposes the collision that endpoint checking hid. It also checks motion, not only location. Suppose the path slope at the midpoint is path_derivative_mid = 0.9 m/s, but the arm dynamics with the chosen torque predict f(x_mid,u_mid)=0.4 m/s. The curve is trying to pass through the checked point faster than the motors can produce there. A repaired candidate bends wider: x_mid = 0.14 meters, outside the fixture, and uses torque whose predicted speed is f(x_mid,u_mid)=0.6 m/s while the curve slope is 0.6 m/s. Now the midpoint passes both checks. But one honest midpoint is not a free pass for the whole curve. Add a second checked point at t = 0.3 seconds. If the path there has x_3 = 0.16 meters, clearance_3 = 0.16 - 0.12 = 0.04 meters, and defect_3 = 0.5 - 0.5 = 0, the later part is also believable. If instead x_3 = 0.11 meters, the fixture collision has merely moved later in the interval. Now check a whole interval, not just one point. Between t = 0.2 and t = 0.4, dt = 0.2 seconds. If the grid says x_2 = 0.14 and x_4 = 0.18, the drawn jump is x_4 - x_2 = 0.04 meters. If the dynamics at the two ends predict speeds 0.6 m/s and 0.2 m/s, a trapezoid estimate of motion is 0.2*(0.6 + 0.2)/2 = 0.08 meters. The interval defect is 0.04 - 0.08 = -0.04 meters, so the curve has not moved as far as its own endpoint dynamics say it should. Changing x_4 to 0.22 would fix that defect, but it may violate a wall limit x <= 0.20. Collocation makes these tensions visible at the same time: clearance, dynamics, actuator bounds, and endpoint goals all have to agree. That is the heart of collocation: choose a curve or grid, then force selected interior points and intervals to be physically honest.",
        "math": "Collocation uses polynomial or grid approximations and enforces defect equations at selected points. A midpoint defect can be written as defect_mid = path_derivative_mid - f(x_mid,u_mid). In the failing arm example, defect_mid = 0.9 - 0.4 = 0.5 m/s, so driving defect_mid to 0 says the curve's slope at the checked point must agree with the dynamics. A collision constraint at the same point can be written clearance_mid >= 0. If the fixture spans x = 0.08 to 0.12 meters and x_mid = 0.10 meters, then clearance_mid is negative and the candidate fails even before scoring effort. For the repaired midpoint, x_mid = 0.14 meters gives clearance_mid = 0.14 - 0.12 = 0.02 meters on the right side of the fixture, and defect_mid = 0.6 - 0.6 = 0. A second point can carry the same tests: clearance_3 = x_3 - 0.12 and defect_3 = path_derivative_3 - f(x_3,u_3). With x_3 = 0.16, clearance_3 = 0.04 and defect_3 = 0.5 - 0.5 = 0. With x_3 = 0.11, clearance_3 = -0.01 and the candidate fails even if the midpoint looked repaired. An interval defect can be written as defect_interval = (x_{k+1} - x_k) - dt*(f_k + f_{k+1})/2. For the interval from x_2=0.14 to x_4=0.18 with dt=0.2, f_2=0.6, and f_4=0.2, defect_interval = (0.18 - 0.14) - 0.2*(0.6 + 0.2)/2 = -0.04 meters. Setting x_4=0.22 would make (0.22 - 0.14) - 0.08 = 0, but the wall constraint x_4 <= 0.20 rejects it. A zero start error and a zero finish error are not enough; the curve must also point in a physically possible direction where it is sampled and move the right amount over each checked interval. Each added sample is another question the drawn curve must answer. Using points at t = 0.1, 0.2, and 0.3 seconds makes it harder for the optimizer to hide a collision, torque spike, or impossible acceleration between endpoints. The boundary is sampling and representation: collocation checks the points and polynomial pieces the designer wrote down, not every unmodeled flex, backlash, or contact event in the real arm.",
    },
    "trajectory-optimization": {
        "run": "A walking robot needs to move its foot from behind a box to the floor in front of it over 1.2 seconds. The answer is not one footstep point. At t = 0.0, 0.3, 0.6, 0.9, and 1.2 seconds, the plan must name body angle, foot position, joint velocity, and motor torque. Suppose the foot height samples are 0.04, 0.18, 0.22, 0.12, and 0.00 meters while the box top is 0.16 meters. That looks safe at the foot. Now check the body and actuator: at t = 0.6 the torso lean is 17 degrees even though the support limit is 12 degrees, and at t = 0.9 the knee torque is 46 newton-meters even though the motor limit is 40 newton-meters. A repaired plan lifts the foot a little higher, with samples 0.04, 0.20, 0.26, 0.16, 0.00, and slows the body so torso lean peaks at 11 degrees and knee torque peaks at 38 newton-meters. The foot path may look less direct, but the whole motion is legal. Now imagine a local optimizer proposes Candidate B to save effort: lower the middle foot sample from 0.26 to 0.21 meters and reduce peak torque from 38 to 34 newton-meters. The effort score improves by 38^2 - 34^2 = 288 torque-squared units, but a midpoint check at t = 0.45 seconds predicts foot height 0.155 meters. Clearance is 0.155 - 0.16 = -0.005 meters, so the cheaper candidate clips the box and must be rejected or repaired. A start-and-finish plan would hide both failures. A picture of the foot path would hide the torso fall. Trajectory optimization treats the whole state-action history as the decision: not only where the foot goes, but what every relevant part of the robot is doing while it gets there. The output is a planned motion that a feedback tracker may later follow; the trajectory itself is still a model-based promise, not proof that the real robot will stay on it after a shove.",
        "math": "The decision is a sequence or curve of states and controls, such as x_0...x_N and u_0...u_{N-1}. For the five-sample walking plan, x_k might contain torso angle, foot height, joint velocity, and contact state, while u_k contains hip and knee torques. The solver minimizes a path cost such as J = sum_k [10*foot_error_k^2 + 0.01*torque_k^2] while satisfying dynamics x_{k+1}=f(x_k,u_k), boundary conditions, and constraints along the trajectory. A dynamics defect at one interval can be written defect_k = x_{k+1} - f(x_k,u_k); a physically connected plan needs defect_k = 0, not merely nice-looking samples. The legal checks are local in time: torso_lean_2 = 17 degrees violates torso_lean <= 12 degrees, and torque_3 = 46 violates torque <= 40. The repaired plan has torso_lean_2 = 11 degrees and torque_3 = 38, so those two inequalities pass; it may pay extra foot cost because 0.26 meters is higher than needed. A local surrogate step may say Delta J_effort = 0.01*(34^2 - 38^2) = -2.88, which is good for the written effort term. But constraints are not suggestions inside the score. The midpoint clearance constraint is clearance_mid = foot_height_mid - box_height >= 0. Candidate B has clearance_mid = 0.155 - 0.16 = -0.005, so its constraint residual is negative even though effort improved. A safer candidate can use foot_height_mid = 0.175, giving clearance_mid = 0.015 while still reducing torque to 36 newton-meters. Then Delta J_effort = 0.01*(36^2 - 38^2) = -1.48: less savings, but legal. The solver may trade a slightly higher foot path for lower torque or better balance because the score and constraints apply to the whole history. The boundary is model and resolution. If the grid skips the instant when the knee clips the box, or if the contact model lies about foot slip, the optimized trajectory can be neat in the file and bad on the floor.",
    },
    "dynamic-programming": {
        "run": "A grid rover is two cells from the charging pad. The goal cell G has value V(G)=0. The cell A just before the goal has value V(A)=1 because one legal move reaches the pad. A rough cell R has value V(R)=6 because the remaining route is slow. Now update a muddy cell M. Moving right costs 1 and reaches A, so that branch costs 1 + V(A) = 2. Moving down costs 3 and reaches R, so that branch costs 3 + V(R) = 9. Dynamic programming writes V(M)=2 and stores the right move. Now update an earlier cell S. From S, moving east costs 2 and reaches M, so that branch costs 2 + V(M) = 4. Moving south costs 1 and reaches R, so that branch costs 1 + V(R) = 7. The stored value becomes V(S)=4. A path-enumeration mindset would compare full strings such as S-east-M-right-A-goal and S-south-R-slow-goal. Dynamic programming does not reopen M every time some earlier state reaches it. It solved future cells once, reused their values, and turned a long path comparison into repeated one-step comparisons. Add another earlier cell T that can move north to M for cost 4 or west to R for cost 2. With the old rough route, north costs 4 + V(M) = 6 and west costs 2 + V(R) = 8, so T stores north. The important part is not the direction name. It is that S and T both borrow the same V(M)=2 instead of each re-solving the little story M-right-A-goal. That reuse is what makes the answer a feedback table: if the rover later lands in M from any route, the stored move is still right. Now change the map: workers lay boards across the rough cell, so the best remaining route from R drops from V(R)=6 to V_new(R)=2. The update at M changes because down now costs 3 + V_new(R) = 5 while right is still 2, so M keeps the right move. The update at S changes more: south now costs 1 + V_new(R) = 3, which beats east at 4. Dynamic programming rewrites V_new(S)=3 and pi_new(S)=south without listing every complete path again. T changes too: west now costs 2 + V_new(R) = 4 while north through M still costs 6, so pi_new(T)=west. The changed future price travels backward only through states that depend on it, and it can flip one earlier decision while leaving another alone.",
        "math": "Dynamic programming solves coupled subproblems indexed by state. A deterministic update has the shape V(s) = min_a [c(s,a) + V(next(s,a))]. The backward pass starts from terminal values such as V(G)=0, writes neighboring state values such as V(A)=1, then uses those values to write earlier states such as V(M)=2 and V(S)=4. The policy is stored at the same time: pi(M)=right and pi(S)=east. This is why the transcript calls it a procedural way to solve for closed-loop policies. The added state T is another backup using the same stored future: V(T)=min(4+V(M), 2+V(R)) = min(6,8) = 6, so pi(T)=north. After the rough-cell repair, the same equations are reused with V_new(R)=2. At M, min(1+V(A), 3+V_new(R)) = min(2,5) = 2, so V_new(M)=2 and pi_new(M)=right. At S, min(2+V_new(M), 1+V_new(R)) = min(4,3) = 3, so V_new(S)=3 and pi_new(S)=south. At T, min(4+V_new(M), 2+V_new(R)) = min(6,4) = 4, so V_new(T)=4 and pi_new(T)=west. The method is not magic search; it is bookkeeping that lets a local value change be propagated through earlier state backups. The price is state coverage. If the rover grid has 100 positions, 5 battery levels, and 4 load states, the table already has 100*5*4 = 2,000 state entries before actions are compared. Add 20 heading values and 10 mud-depth levels, and the table grows to 100*5*4*20*10 = 400,000 entries. With 3 legal actions per state, one full sweep checks about 400,000*3 = 1,200,000 action branches. If value iteration needs 50 sweeps, the simple table has about 60,000,000 branch checks before the values settle. That count is why the lecture warns that dynamic programming is computationally intensive. If the state omits mud depth or battery health, the reused subproblem value is reused for states whose futures are not actually the same. If two cells share the label R but one is wet mud and the other is dry boards, one number V(R) falsely prices two different futures. Reuse is powerful only when the state is honest and small enough to cover.",
    },
    "lqr": {
        "run": "A small delivery cart is 20 centimeters left of the center line, so write the lateral error as e = 0.20 meters. Near the center line, one steering correction can be approximated as e_next = e + u, where u is the sideways change produced over the next short step. The cart dislikes being off-center, but it also dislikes hard steering. A simple local score is 5*e^2 + u^2 now, plus a future penalty 20*e_next^2. If u = 0, the cart stays 20 centimeters off and pays the future penalty. If u = -0.20, the next error is zero but the steering effort is larger. The best local compromise is concrete: minimizing u^2 + 20*(0.20 + u)^2 gives u = -0.190 meters. The feedback rule is therefore push back almost the full measured error, but not quite, because steering itself has a price. If the cart is 5 centimeters left instead, e = 0.05 and the same gain gives u = -(20/21)*0.05 = -0.0476 meters. If it is 20 centimeters right, e = -0.20 and the sign flips to u = +0.190 meters. That proportional correction is what LQR turns into a gain: measure the deviation, multiply by a gain, and push back toward the nominal path. Now make steering four times more expensive by scoring 4*u^2 instead of u^2. The same 20 centimeter error gives u = -0.1667 meters and leaves e_next = 0.0333 meters. Make steering cheap with 0.25*u^2, and the same error gives u = -0.1975 meters and leaves only e_next = 0.0025 meters. Now add heading. Suppose the state is x = [lane_error, heading_error] = [0.20, 0.10], where heading_error is in radians. A sample local gain might be u = -0.8*lane_error - 0.4*heading_error. The command is u = -0.8*0.20 - 0.4*0.10 = -0.20 meters. If the cart is centered but pointing right, x = [0.00, 0.10], the same rule gives u = -0.04 meters before lane error appears. LQR is not only a spring pulling position to zero; with a richer state it can push against the motion that will create future error. The weights are not decoration. They decide whether the controller spends actuator effort now or tolerates more remaining error. Same car, different written prices, different feedback gain.",
        "math": "LQR assumes linear dynamics such as x_{k+1}=A_k x_k + B_k u_k and a quadratic cost such as x_k^T Q_k x_k + u_k^T R_k u_k plus a terminal quadratic. The important closure is that a quadratic future value stays quadratic when carried one step backward through linear dynamics. In the scalar cart example, minimize J(u)=u^2 + 20*(0.20 + u)^2. The derivative is 2u + 40*(0.20 + u), so 42u + 8 = 0 and u = -8/42 = -0.190. For a general scalar error e, the same derivative gives 2u + 40*(e + u)=0, so u = -(20/21)*e. Written as feedback, u = -K e with K = 20/21. Larger R makes K smaller because control effort is expensive. With R = 4, the one-step score is 4u^2 + 20*(e+u)^2. The derivative 8u + 40*(e+u)=0 gives u = -(5/6)*e, so K = 5/6 and e = 0.20 gives u = -0.1667. With R = 0.25, the derivative 0.5u + 40*(e+u)=0 gives u = -(40/40.5)*e, so e = 0.20 gives u = -0.1975. Larger future state penalty would push K closer to 1. In vector form the feedback is u_k = -K_k x_k. For the two-state example, K = [0.8, 0.4], so u = -[0.8,0.4]*[0.20,0.10] = -0.20. The same gain on x = [0.00,0.10] gives u = -0.04, showing that heading error can matter before position error is visible. Now add an actuator bound |u| <= 0.10 meters. For e = 0.20, plain LQR asks for u = -0.190, but the actuator can only deliver u = -0.10. The clipped action leaves e_next = 0.10, not the predicted 0.010. If a wall constraint says |e_next| <= 0.05, the clipped action is not merely less elegant; it violates the written safety bound because 0.10 > 0.05. LQR stops being the right full explanation when the local model is false, the actuator saturates, or a hard state constraint matters, because those features are not inside the plain linear-quadratic problem.",
    },
    "stochastic-dynamic-programming": {
        "run": "A delivery rover can cross gravel or detour around it. Crossing gravel costs 1 minute now. Nature then draws a disturbance W. With probability 0.6, W = straight and the rover reaches a state with future value 5. With probability 0.3, W = slip-left and the future value is 12. With probability 0.1, W = slip-right and the future value is 20. These probabilities must add to 1.0 because they describe the full set of next outcomes for this action. The next state is not one promise. The expected future value is 0.6*5 + 0.3*12 + 0.1*20 = 8.6, so the gravel action costs 1 + 8.6 = 9.6. The detour costs 4 minutes now. It has probability 0.9 of reaching a state with value 4 and probability 0.1 of meeting a slow gate with value 9, so its total is 4 + 0.9*4 + 0.1*9 = 8.5. The detour wins even though its immediate cost is larger. If slip-right is serious but not enormous, say value 60, gravel costs 1 + 0.6*5 + 0.3*12 + 0.1*60 = 13.6. If slip-right means a broken axle with repair cost 200, the gravel expected total becomes 1 + 0.6*5 + 0.3*12 + 0.1*200 = 27.6. Now suppose an old dry-floor table claimed P(straight)=0.68, P(slip-left)=0.30, and P(slip-right)=0.02. That would score gravel as 1 + 0.68*5 + 0.30*12 + 0.02*20 = 8.4, just beating the 8.5 detour. After rain, the rover records 50 gravel crossings: 24 straight, 18 slip-left, and 8 slip-right. The measured probabilities are 24/50 = 0.48, 18/50 = 0.36, and 8/50 = 0.16. The same Bellman backup now gives 1 + 0.48*5 + 0.36*12 + 0.16*20 = 10.92, so the detour wins again. The choice changed because rain changed the probabilities, not because detour became cheaper. Stochastic dynamic programming is the same backward reasoning as ordinary dynamic programming, except each possible next state carries probability weight before the action is compared.",
        "math": "The stochastic Bellman update uses an expectation over the disturbance or next state: V(x) = min_u [cost(x,u) + E_W V(f(x,u,W))]. For a discrete next-state model, that expectation becomes cost(x,u) + sum over x_next of P(x_next|x,u) V(x_next). The probabilities are part of the dynamics model, not decoration after the fact. In the gravel example, P(straight|x,gravel)=0.6, P(slip-left|x,gravel)=0.3, and P(slip-right|x,gravel)=0.1, so P(straight|x,gravel)+P(slip-left|x,gravel)+P(slip-right|x,gravel)=1.0. The rare slip-right branch still adds 0.1*20 = 2 to the expected future value; with value 60 it adds 0.1*60 = 6; and in the broken-axle version it adds 0.1*200 = 20. The dry-floor model shows how fragile the action choice can be: Q_dry(x,gravel)=1+0.68*5+0.30*12+0.02*20=8.4, while Q(x,detour)=8.5. The measured wet-floor model gives P_hat(straight)=24/50=0.48, P_hat(slip-left)=18/50=0.36, and P_hat(slip-right)=8/50=0.16, so Q_wet(x,gravel)=1+0.48*5+0.36*12+0.16*20=10.92. The Bellman equation did not change; the transition model changed. If wet gravel and dry gravel share one state label, the stored probability is averaging two different worlds and the controller will be wrong on at least one of them. The state must carry the past effects of earlier disturbances; the update should not need the whole old history again. A policy that ignores that branch is not optimistic in a harmless way; it has priced a different world than the rover will face. The boundary is risk preference and model truth: expectation is the average cost criterion, so it may still accept rare catastrophic outcomes unless the cost, constraint, or risk measure makes them large enough, and it can only average the probabilities it was given. With slip-right value 60, expectation ranks gravel at 13.6 minutes; a safety rule such as P(broken_axle) <= 0 would reject gravel regardless of its average. If one slip destroys the rover, average minutes may be the wrong measuring stick; the model needs a hard safety constraint or a risk measure, not only a mean.",
    },
    "local-quadratic-approximation": {
        "run": "A robot gripper is following a planned motion, but at one instant it is 6 centimeters too far left. The full contact model is messy: if the gripper moves a little right, the error improves; if it moves too far, it hits the rim of the bin and the real cost jumps. Around the current command, test three nearby nudges. At delta u = -0.02 meters the measured local score is 5.8. At delta u = 0 meters the score is 4.0. At delta u = 0.02 meters the score is 3.0. Those three readings say the local slope is negative: moving right helps. They also show the curve is bending upward, so the next improvement should get smaller. A local quadratic model is the small bowl fitted to that neighborhood, not a promise about the whole bin. It lets the solver compute a correction before trying the real motion again. If the fitted bowl says jump 12 centimeters right, the controller should distrust that step because the data came from nudges of only 2 centimeters. Even a 2.8 centimeter suggested step is slightly outside the tested band, so a guarded controller may clip the first move to delta u = 0.02 meters. After taking that clipped step, the real score is measured as 3.15, close to the predicted 3.1. Now refit around the new command. Nearby scores at extra nudges -0.01, 0, and +0.01 meters are 3.40, 3.15, and 3.05. The gripper is now closer to the rim, so the same extra centimeter is more dangerous than before. The new fitted bowl is flatter and suggests only another 1.2 centimeter move, not a big jump. In a control rollout, the same idea uses deviations from a nominal plan. Suppose the nominal state is x_bar = 0.06 meters left of the desired grasp and the nominal command is u_bar = 0.00. A local dynamics fit says delta x_next = 0.7*delta x + 1.5*delta u. If the current deviation is delta x = -0.02 and we apply the clipped delta u = 0.02, the local model predicts delta x_next = 0.7*(-0.02) + 1.5*0.02 = 0.016 meters. If the real rollout measures 0.024 meters instead, the model was useful but not exact, so the next quadratic should be centered at the measured point. This is the repeated rhythm: fit nearby, step guardedly, measure again, and only then trust the next bowl.",
        "math": "Around a nominal state and action, write the change as delta x and delta u, where delta x = x - x_bar and delta u = u - u_bar. A second-order local model has the shape q(delta u) = c + g*delta u + 0.5*H*delta u^2 when delta x is fixed for this one small calculation. Suppose the fitted numbers are c = 4.0, g = -70, and H = 2500. Setting the derivative to zero gives g + H*delta u = 0, so delta u* = -g/H = 0.028 meters. The predicted score there is q(0.028)=4.0 - 70*0.028 + 0.5*2500*0.028^2 = 3.02. That looks better than q(0)=4.0, but the samples only covered -0.02 <= delta u <= 0.02. A trust region with radius 0.02 would choose delta u_clipped = 0.02 first, where q(0.02)=4.0 - 1.4 + 0.5 = 3.1, then remeasure and refit around the new point. The second fit has c2 = 3.15, g2 = -10, and H2 = 833. Setting g2 + H2*delta u = 0 gives delta u2* = 10/833 = 0.012 meters, which matches the small second step suggested by the new samples. The old 0.028 meter step is no longer the answer because the center of the approximation moved after real contact changed. In control, the same idea is applied to dynamics and value: linearize the dynamics, quadratize the cost or Q function, solve the easier local problem, and take a guarded step. A scalar local dynamics model might be delta x_next = A*delta x + B*delta u with A = 0.7 and B = 1.5. For delta x = -0.02 and delta u = 0.02, the predicted next deviation is 0.7*(-0.02) + 1.5*0.02 = 0.016. If the measured next deviation is 0.024, the prediction error is 0.024 - 0.016 = 0.008 meters. That error is a warning to relinearize around the new measured trajectory, not a reason to keep pushing from the stale quadratic. In iLQR language, use x_bar,u_bar to linearize dynamics and quadratize cost, solve for delta u, roll out u_bar + delta u, then set the next x_bar,u_bar from the new rollout. The boundary is the trust region. If the proposed delta u is much larger than the neighborhood used to fit g and H, or if the measured prediction error keeps growing, the quadratic may be explaining empty space rather than the real system.",
    },
    "reachability": {
        "run": "Two cars are 5 meters apart along the road. The rear car is drifting toward the front car's lane at 0.6 meters per second, and the front car can move sideways at at most 0.4 meters per second. A one-second plan that only checks the current gap may say the front car is safe because there is still 1.2 meters of lateral space. Reachability asks a different question: if the rear car gets one bad push from wind or a steering error, is there still any legal evasive command that keeps the cars out of the collision target set? Suppose the bad target is lateral distance below 0.3 meters. If the current lateral gap is 0.5 meters, even the strongest front-car move gives 0.5 + 0.4 - 0.6 = 0.3 after one second. That state is already on the unsafe boundary. If the current gap is 0.4 meters, the same best escape leaves 0.2 meters, which is inside the target set. A state with 1.2 meters of lateral gap is outside that one-step danger set because the front car still has enough room to grow the gap to 1.0 meters under the same worst case. Now step backward one more second. From a 0.7 meter gap, the best first escape under the same bad push leaves 0.7 + 0.4 - 0.6 = 0.5. But 0.5 is already in the one-step danger set, so 0.7 is unsafe over a two-second horizon. From a 0.8 meter gap, the same first step leaves 0.6, which is outside the one-step danger set, so the car still has a safety move in this tiny model. The output is not a single heroic swerve. It is a map of starting states for a chosen horizon: below 0.5 is already bad in one step, 0.7 becomes bad over two steps, and 0.8 remains outside this two-step danger map.",
        "math": "For an avoidance question, define the target set as collision states, for example T_bad = {gap <= 0.3 meters}. A simple one-step predecessor calculation marks a state unsafe if there exists a disturbance w such that for every legal control u, next_gap(gap,u,w) is in T_bad. The order matters: the disturbance is allowed to be bad, and the controller must fail for every legal response. With gap = 0.5, front control u can add at most 0.4 meters of lateral separation and disturbance w can remove 0.6 meters, so next_gap <= 0.5 + 0.4 - 0.6 = 0.3. That starting state belongs to the backward avoidance set A_1. With gap = 0.4, even the best control gives next_gap <= 0.4 + 0.4 - 0.6 = 0.2, which is strictly inside T_bad. With gap = 1.2, the same worst case gives next_gap <= 1.0, so it is not in this one-step bad set. The next set is built from the previous set: A_2 contains states whose worst-case next state lands in A_1. Since A_1 begins at gap <= 0.5 in this example, gap = 0.7 enters A_2 because 0.7 + 0.4 - 0.6 = 0.5. gap = 0.8 does not enter A_2 because 0.8 + 0.4 - 0.6 = 0.6, which is outside A_1. This is the backward part of backward reachability: start from the target, then repeatedly ask which earlier states can be forced into the set already known to be bad. For a goal-reaching question, the quantifiers flip: for all disturbances, there must exist a control that reaches the good target. Reachability is hard because it prices the fight between control and disturbance over sets of states, not only one predicted path.",
    },
    "model-predictive-control": {
        "run": "A warehouse cart is 3.0 meters from a loading mark and is moving at 1.0 m/s. Every 0.5 seconds it solves a small plan with three future acceleration commands. At 10:00:00 the optimizer predicts this sequence: brake at -0.8 m/s^2, then -0.6, then -0.2. Using v_next = v + dt*u and p_next = p + dt*v_next, the first predicted half-second gives velocity 0.60 m/s and position 3.30 meters. The next two predicted positions are 3.53 meters and 3.70 meters, staying below the 4.0 meter stop line. MPC applies only the first command, -0.8 m/s^2, for the next 0.5 seconds. It does not apply the old -0.6 and -0.2 yet. A floor bump slows the cart more than expected, so the measured state at 10:00:00.5 is position 3.40 meters and velocity 0.50 m/s, not the predicted 3.30 meters and 0.60 m/s. The controller now discards the old second and third commands as promises made from the wrong state. If it blindly applied the old next brake -0.6 from the measured state, it would get v_next = 0.50 + 0.5*(-0.6) = 0.20 m/s and p_next = 3.40 + 0.5*0.20 = 3.50 meters, leaving the cart too far short of the mark. Solving again from the measured state, it may choose [-0.4, -0.3, -0.1] because the cart is already slower. The new first command gives v_next = 0.50 + 0.5*(-0.4) = 0.30 m/s and p_next = 3.40 + 0.5*0.30 = 3.55 meters. The next new predictions are 3.625 meters and 3.675 meters, closer to the mark while still below the stop line. Now test a tempting lazy plan from the same measured state: [-0.1, -0.1, -0.1]. It feels gentle, and no single command breaks the acceleration bound. But its three predicted steps are p_1 = 3.625 with v_1 = 0.45, p_2 = 3.825 with v_2 = 0.40, and p_3 = 4.000 with v_3 = 0.35. The cart reaches the stop line still moving at 0.35 m/s. If the terminal rule says final speed must be at most 0.10 m/s and the cart must keep positive room before the hard line, this lazy plan is rejected before its first command can be used. Timing creates another plain failure. If a solve started at 10:00:00.5 takes 0.8 seconds while the controller period is 0.5 seconds, the answer arrives at 10:00:01.3. A cart coasting from position 3.40 meters at 0.50 m/s during those 0.8 seconds reaches p_late = 3.40 + 0.8*0.50 = 3.80 meters. The command was chosen for state (3.40, 0.50), but it arrives when the cart is near (3.80, 0.50). The method is not 'plan once carefully.' It is 'plan, use the first piece, measure, and make a new plan from reality,' and it only works when the first piece is computed in time and leaves another legal plan.",
        "math": "At time k, MPC solves a finite-horizon problem for variables u_0...u_{N-1} and predicted states x_0...x_N with x_0 = x_measured(k). The optimization minimizes predicted cost while enforcing dynamics, input bounds, state bounds, and any terminal rule. The implemented policy is pi_MPC(x_measured(k)) = u_0^*, the first control from that solve. After applying u_0^*, the real system produces x_measured(k+1). The next problem is not anchored at the old prediction x_1^pred if the sensor says otherwise; it uses x_0 = x_measured(k+1). In the cart run, the old tail [-0.6, -0.2] was computed for predicted state (3.30, 0.60), but the next solve starts from measured state (3.40, 0.50) and chooses new tail [-0.4, -0.3, -0.1]. The applied control is therefore -0.4, not the old -0.6. From measured state (3.40, 0.50), using old -0.6 gives predicted state (3.50, 0.20). Using new -0.4 gives predicted state (3.55, 0.30), and the new three-step rollout ends at (3.675, 0.10). If a simple terminal error is distance to the loading mark at 4.0 meters, the old one-step position error is 4.0 - 3.50 = 0.50 meters while the new one-step position error is 4.0 - 3.55 = 0.45 meters. That small comparison shows why the old tail is not sacred: it was good for a state the cart did not actually reach. The terminal check is a second filter, not decoration. The candidate tail [-0.1, -0.1, -0.1] gives v_1=0.45, p_1=3.625; v_2=0.40, p_2=3.825; and v_3=0.35, p_3=4.000. A weak horizon check might only notice p_3 <= 4.0 and call the path legal. A useful MPC problem asks for the state it hands to the next solve. With terminal speed 0.35 > 0.10 and terminal margin 4.0 - 4.000 = 0.000, the terminal rule rejects it before the first command. The timing check is just as mechanical: t_solve = 0.8 seconds and dt_control = 0.5 seconds gives t_solve > dt_control, so the command is stale on arrival. If the cart coasts while waiting, p_late = 3.40 + 0.8*0.50 = 3.80, which is 0.40 meters away from the state used in the solve. That measurement reset is why MPC is closed loop even though each solve is an open-loop optimization. The boundary is speed and future protection: if the solve takes 0.8 seconds while the control period is 0.5 seconds, the chosen command is already late; if the horizon and terminal structure allow a first move that leaves no feasible continuation, the loop can make a legal-looking move now and fail one step later. Recursive feasibility and stability are extra promises on top of basic MPC, not automatic consequences of replanning.",
    },
    "recursive-feasibility": {
        "run": "A delivery cart is rolling toward a narrow doorway with 2.0 meters left before the stop line. The MPC horizon has three half-second moves. At 10:00 it finds a feasible plan: brake gently, brake harder, then enter a terminal slow zone where speed is below 0.2 m/s and at least 0.4 meters of stopping distance remains. The first command is legal by itself. But recursive feasibility asks a stricter question: after that first command is applied, can the next MPC solve still find a legal three-move plan? If the first command keeps speed at 1.4 m/s with only 1.1 meters left, tomorrow's optimizer may have no braking sequence that respects the doorway speed limit and stop line. With maximum braking 0.8 m/s^2, stopping from 1.4 m/s needs v^2/(2a)=1.4^2/(2*0.8)=1.225 meters, which is already more than the 1.1 meters left. That first command was not illegal at 10:00, but it handed 10:00.5 an impossible problem. A safer first command might leave speed 1.0 m/s with 1.2 meters left. Then stopping needs 1.0^2/(2*0.8)=0.625 meters, leaving 0.575 meters of margin for the next solve. This margin is the handoff certificate: if the next solve gets stuck, the cart still has enough room to use maximum braking and enter the slow zone. Now suppose the measured successor is worse than planned: speed 1.1 m/s with 1.15 meters left. Stopping needs 1.1^2/(2*0.8)=0.756 meters, leaving 0.394 meters, just below the required 0.4 meter terminal margin. The planned handoff looked safe, but the measured handoff failed by 0.006 meters. A recursively feasible design chooses the first command whose successor state still belongs to the set of states with a feasible continuation, and then checks that claim against the real measured successor. The phrase is easy to misread. It does not mean the optimizer found a plan once. It means every applied move preserves at least one future plan, like walking across a bridge only by stepping on boards that leave another board reachable.",
        "math": "The standard handoff proof uses the tail of the previous feasible plan. Suppose at time k the feasible sequence is [u_0^*, u_1^*, u_2^*] with predicted states [x_0, x_1, x_2, x_3], and x_3 lies in a terminal set X_F. MPC applies u_0^* and the model gives x_{k+1}=f(x_k,u_0^*) = x_1. At the next solve, a candidate plan is [u_1^*, u_2^*, v_backup]: shift the old tail forward and append one backup control. If X_F is controlled invariant, then there exists v_backup that keeps f(x_3,v_backup) in X_F while obeying bounds. That shifted-tail candidate proves the next optimization is feasible before asking whether it is optimal. The doorway version of X_F is ordinary: speed <= 0.2 m/s and stopping_distance_remaining >= 0.4 meters. In set language, X_0 is the set of states from which the horizon problem has at least one feasible solution, and recursive feasibility asks the closed-loop move to keep x_{k+1} in X_0 whenever x_k started in X_0. For the safe successor, the backup certificate is concrete: x_1 = (1.2 meters left, 1.0 m/s), v_backup = maximum brake, stopping_distance = 0.625 meters, and reserve = 1.2 - 0.625 = 0.575 meters. Written in the terminal-margin form, stopping_distance_remaining - stopping_distance = 1.2 - 0.625 = 0.575 meters, so it still has a continuation. Since 0.575 >= 0.4, the next optimizer has at least one fallback even before it searches for a better one. A state with speed 1.4 m/s and 1.1 meters left is outside the safe handoff set because even maximum braking needs 1.225 meters. The measured successor with speed 1.1 m/s and 1.15 meters left has stopping_distance = 1.1^2/(2*0.8)=0.756 meters, so stopping_distance_remaining - stopping_distance = 1.15 - 0.756 = 0.394 meters. Since 0.394 < 0.4, that measured state is outside X_F even though the planned x_1 was inside. The proof also depends on applying the old tail from the state the model predicted. If the real cart lands at x_measured = (1.15 meters left, 1.1 m/s) instead of x_1 = (1.2 meters left, 1.0 m/s), the shifted sequence [u_1^*, u_2^*, v_backup] is no longer certified. The boundary is model truth and terminal-set design: if the real state misses x_1, or X_F is chosen too small, too large, or not invariant, the handoff proof no longer protects the loop. Feasibility is a promise about the next optimization problem having an answer; it is not yet a promise that the cart reaches the doorway smoothly or quickly.",
    },
    "stability-under-replanning": {
        "run": "A warehouse robot is 1.5 meters left of its charging lane and moving right at 0.8 m/s. A short MPC solve can be feasible at every second and still behave badly: at 10:00 it steers right, at 10:01 it overcorrects left, at 10:02 it steers right again, and the robot keeps crossing the lane. Every individual solve found legal commands, but the repeated loop did not settle. Stability under replanning asks for a number that should go down after each real move, not just a fresh feasible plan. Use a simple stored burden E = distance_error^2 + 0.5*sideways_speed^2. At 10:00, E = 1.5^2 + 0.5*0.8^2 = 2.57. After the first command, suppose the measured state is 0.9 meters left and 0.5 m/s right, so E = 0.9^2 + 0.5*0.5^2 = 0.935. That is progress. A good next replan might leave the robot 0.5 meters left with sideways speed 0.3 m/s right, giving E = 0.5^2 + 0.5*0.3^2 = 0.295. The burden keeps falling. A bad feasible replan overcorrects instead: the measured state becomes 1.0 meters right with sideways speed 0.6 m/s left, so E = 1.0^2 + 0.5*0.6^2 = 1.18. The robot is still inside the corridor and every input is legal, but the trusted burden rose from 0.935 to 1.18. Another failure is delay. A one-step horizon may choose a tiny brake that lowers effort now and leaves E = 0.90, then choose another tiny brake and leave E = 0.88, while the loading dock requires E <= 0.20 within three seconds. Each replan is feasible and each tiny drop is real, but the loop is not spending error fast enough. Adding a terminal condition E_terminal <= 0.20 or a terminal cost 6*E_terminal makes the delayed bill visible. Stability under replanning rejects loops that merely stay legal or make microscopic progress while missing the long-run target. A stable MPC design uses terminal cost, terminal set, or a decrease condition so the receding-horizon loop spends stored error instead of moving it around.",
        "math": "Once MPC applies its first control as feedback, the closed-loop update can be written x_{k+1}=f_closed(x_k). A Lyapunov-style check chooses a nonnegative function V(x), often the optimal MPC cost J_MPC^*(x), and asks whether V(f_closed(x)) - V(x) <= -stage_cost(x,pi_MPC(x)) or at least <= 0 near the equilibrium. In the robot run, V acts like stored energy: 2.57 drops to 0.935 after the real first move, so delta V = 0.935 - 2.57 = -1.635. The good second move gives delta V = 0.295 - 0.935 = -0.640, another decrease. The bad second move gives delta V = 1.18 - 0.935 = +0.245, which violates a nonincrease test even though feasibility still holds. If the stage cost for the second state were 0.10, the stronger test delta V <= -0.10 would accept -0.640 and reject +0.245. The delayed-braking case shows why nonincrease alone may be too weak for a task deadline. From E_0=0.935, two tiny decreases to E_1=0.90 and E_2=0.88 satisfy E_{k+1} <= E_k, but miss the required E_3 <= 0.20 target. A terminal constraint writes E_N <= 0.20. A terminal cost changes the score from sum stage_cost to sum stage_cost + 6*E_N, so ending a horizon at E_N=0.88 adds 5.28 points while ending at E_N=0.18 adds 1.08 points. Feasibility alone would only say the next optimization exists; stability asks whether the closed-loop sequence drains that stored cost toward the lower bound at the goal. The terminal ingredients matter because a short horizon can hide delayed error. A terminal cost prices what remains after the visible horizon, and a terminal set gives the final predicted state a place where a known local controller can keep reducing V. If those pieces are weak, repeated replanning can remain feasible while cycling, drifting, delaying, or amplifying velocity.",
    },
    "imitation-learning": {
        "run": "A human teleoperates a robot through 200 drawer pulls. Each saved row says what the robot saw and what the human commanded: handle center x = 0.00 meters, gripper angle 0 degrees, pull speed 0.04 m/s; then handle center x = 0.01 meters, gripper angle 2 degrees, pull speed 0.05 m/s; and so on. Imitation learning uses those rows to build a policy, a rule that looks at the current observation and chooses a robot command. The reason this is useful is ordinary: nobody wants to write a full reward for latch friction, wrist angle, wood flex, and gentle contact. The human demonstration carries that know-how. But the rows are not magic. They only show what the expert did in the states the expert visited. In the 200 pulls, suppose 160 rows are centered pulls with handle angle between -2 and +2 degrees. Another 30 rows show a careful left-hook style: gripper angle -14 degrees and pull speed 0.03 m/s. Another 10 rows show a right-hook style: gripper angle +16 degrees and pull speed 0.02 m/s. Both hook styles open a sticky drawer, but averaging them gives about -4 degrees, a command that catches neither side of the handle. That is one imitation problem: if several good human choices exist, a simple squared-error learner can invent a middle action no human meant. The second problem appears when the learned policy is put in charge. If it misses the handle by 3 centimeters on the first pull, the handle may rotate 12 degrees. The training set may contain only 2 rows with handle angle 12 degrees because the human did not make that mistake. The learner is now asking its copied policy to control a state outside the examples. On rollout, the copied policy might command gripper angle 1 degree and pull speed 0.05 m/s, scraping the handle for 0.4 seconds. The expert correction in that same state is gripper angle -18 degrees, slow down to 0.02 m/s, and re-center before pulling. A DAgger-style repair is to roll out the learner for 50 drawer attempts, collect 17 off-center states it creates, ask the expert what action should be taken there, and add those 17 labeled states back into the dataset. Imitation learning is therefore not just 'watch and copy.' It is a choice about which expert behavior to copy, how to represent several valid choices, and how to get labels for states the learner creates after its own small mistakes.",
        "math": "The dataset has pairs (x_i, u_i^expert). Behavioral cloning fits policy parameters theta so pi_theta(x_i) predicts the expert action on demonstrated states. A simple loss is L(theta)=sum_i ||pi_theta(x_i) - u_i^expert||^2. If a drawer state has 30 left-hook labels at -14 degrees and 10 right-hook labels at +16 degrees, a scalar squared-error model that predicts one angle a solves 30*(a - (-14))^2 + 10*(a - 16)^2. The derivative is 60*(a+14) + 20*(a-16) = 80a + 520, so the optimum is a = -6.5 degrees. That number is between the two styles, but it is not necessarily a working hook. A better representation may predict a distribution pi_theta(u|x) with two modes, or it may first choose a mode such as left_hook or right_hook and then output the matching continuous command. The next boundary is state distribution. The supervised loss is measured under the expert state distribution, the states produced when the human or expert policy acts. Deployment is different: x_{t+1}=f(x_t, pi_theta(x_t)), so the learned policy creates the next states it must handle. In the drawer example, the expert dataset has 2/200 = 0.01 of its rows at handle angle 12 degrees, but the learner rollout has 17/50 = 0.34 attempts that pass through off-center recovery states. If pi_theta makes a small early error, the learner state distribution can drift away from the expert distribution and the same supervised loss no longer tells whether recovery actions are known. Dataset aggregation changes the training distribution by collecting states x_j^learner visited by pi_theta, querying u_j^expert for those states, and retraining on both old demonstrations and learner-created states. Written as sets, D_0 is the original 200 expert rows, and D_1 = D_0 union {(x_j^learner,u_j^expert)} for the 17 recovery labels. The method still depends on the expert: if the expert labels are inconsistent, unsafe, or too expensive to query, imitation cannot quietly repair that missing knowledge.",
    },
    "behavioral-cloning": {
        "run": "A small driving policy is trained from expert camera frames. In 1,000 centered-lane frames the expert action is nearly straight: steering angle 0 degrees. Near a parked van, the demonstrations split into two good styles. Some experts steer left around the van with steering angle -12 degrees; others slow down and steer right into a wider gap with steering angle +12 degrees. Behavioral cloning turns each frame into a supervised label problem: given this image and speed, predict the expert steering and throttle. If the model uses squared error and sees the same-looking van frame labeled -12 degrees in 50 examples and +12 degrees in 50 examples, the average label is 0 degrees. That middle command is not cautious wisdom. It drives straight at the van, which no expert intended. Now look at a quieter failure. On held-out expert frames, the model is off by only 1 degree on average. But when deployed, a 1 degree right bias over 20 frames moves the car 0.25 meters toward the lane edge. The next image is not in the 1,000 centered-lane frames; it is a recovery state. The expert would steer -8 degrees left there, but the cloned policy has no label for that state and still predicts 0 degrees. A DAgger-style repair would roll out the learner for 200 such frames, ask the expert for labels on the 37 off-center frames it creates, add those 37 pairs to the dataset, and retrain. This is why behavioral cloning is easy to implement but not automatically safe: the loss can reward a compromise action that is bad in the world, and good test error on expert states can hide bad closed-loop recovery.",
        "math": "The dataset is D = {(x_i,u_i^expert)}. Behavioral cloning fits theta by minimizing a supervised loss such as L(theta)=sum_i ||pi_theta(x_i)-u_i^expert||^2. For the two-mode van frame, if pi_theta(x)=a is a scalar steering angle, the local loss is 50*(a - (-12))^2 + 50*(a - 12)^2. Its derivative is 100*(a+12) + 100*(a-12) = 200a, so the squared-error optimum is a = 0 degrees. The algebra is doing exactly what it was asked to do: predict the conditional mean action. The control problem may need a mode choice instead, such as left path or right path, followed by the matching steering command. The other boundary is closed-loop. The supervised loss is measured on states drawn from the expert distribution d_expert(x), but deployment creates states from d_pi_theta(x) through x_{t+1}=f(x_t,pi_theta(x_t)). In the lane example, d_expert has many centered images and almost no 0.25 meter right-edge images. After rollout, d_pi_theta contains 37 off-center frames out of 200. Dataset aggregation changes the training set from D_0 to D_1 = D_0 union {(x_j^learner,u_j^expert)} for those 37 recovery states. Behavioral cloning itself has no built-in exploration or reward signal to discover that repair; someone must collect or query the missing states.",
    },
    "distribution-shift-imitation": {
        "run": "A cloned lane policy is trained mostly on expert states within 10 centimeters of lane center. On a test set of expert frames it looks good: when the car is 4 centimeters right, it predicts a small left correction; when it is 6 centimeters left, it predicts a small right correction. Now put the policy in the car. At second 0 the car is centered, but the policy understeers by only 2 centimeters. At second 1 the camera view is now 2 centimeters right of the expert path. The policy understeers again, and the car becomes 5 centimeters right. By second 2 it is 9 centimeters right; by second 3 it is 13 centimeters right; by second 4 the car is 18 centimeters right, a state that appeared in only 3 of the 10,000 expert frames because the expert almost always corrected earlier. The policy is not failing on the data it was graded on; it is failing on the state stream created by its own actions. That is why the failure can look unfair at first. The training report says 98 percent of expert frames had steering error below 1 degree, but the road test asks for recovery from a camera view the expert almost never produced. In that 18 centimeter right state, the expert would steer -14 degrees left and slow to 0.5 m/s. The cloned policy has mostly seen mild corrections, so it steers -3 degrees left and keeps 0.9 m/s. One second later the car is 24 centimeters right and the right tire touches the lane marker. Distribution shift in imitation is that split between states produced by the expert and states produced by the learner. A DAgger-style repair would run this learner for 300 seconds, record 42 frames where the car is more than 15 centimeters off center, ask the expert for the correct steering there, and train again on those newly labeled states. The repair is not more abstract cleverness. It puts recovery examples exactly where the copied policy has shown it will go.",
        "math": "Let d_expert(x) be the state distribution generated by the expert policy and d_pi(x) be the state distribution generated by the learned policy pi_theta. Behavioral cloning minimizes prediction loss on samples from d_expert, but deployment performance depends on d_pi because x_{t+1}=f(x_t,pi_theta(x_t)). In the lane run, a 2 centimeter first error changes the next input; the next input makes the following error more likely, so the gap compounds over time. A simple count makes the mismatch visible: d_expert(|offset| > 15 cm) = 3/10000 = 0.0003, while one learner rollout gives d_pi(|offset| > 15 cm) = 42/300 = 0.14. The warning sign is d_pi(18 cm right) much larger than d_expert(18 cm right), even if held-out expert accuracy is high. If the per-step chance of a small mistake on expert-like frames is epsilon = 0.02, then a 50-step drive does not behave like one independent label test. A rough compounding bound can scale like T^2*epsilon = 50^2*0.02 = 50 expected mistake-pressure units, because each wrong action can move the car into states where later actions are less trained. Dataset aggregation changes the sampling rule: collect rollout states from d_pi, query the expert action u^expert(x) on those states, append them to the dataset, and retrain so the learner has recovery labels where its own policy actually goes. In symbols, start with D_0 from expert demonstrations, train pi_1, roll out pi_1 to get learner states x_j^pi_1, query labels u_j^expert, then form D_1 = D_0 union {(x_j^pi_1,u_j^expert)}. If the 42 off-center frames are added, the loss now directly sees pairs like x = 18 cm right maps to u^expert = -14 degrees and 0.5 m/s. The boundary is access and coverage: DAgger helps only if an expert can label the learner's states, and it should keep the states that matter instead of flooding the dataset with thousands of already-centered frames.",
    },
    "reinforcement-learning": {
        "run": "A robot has no expert labels for how to pick up a soft pouch. It can try a grip, watch what happens, and receive reward. In one rollout, the first action closes the fingers lightly with 12 newtons and gets reward 0 because nothing has lifted yet. The second action tilts the wrist by 15 degrees and gets reward -1 because the pouch slips. The third action squeezes a little more with 18 newtons, lifts the pouch 6 centimeters, and gets reward +10. A supervised learner would ask what the right action label was at the first image. RL asks a different question: did the whole sequence of actions lead to good return, and how should that later +10 change the earlier action choices? With discount gamma = 0.9, the return from the first step is G_0 = 0 + 0.9*(-1) + 0.9^2*10 = 7.2. That number says the first light grip was not useless just because its immediate reward was zero. Now compare a second rollout from almost the same camera view. The robot closes with 30 newtons, lifts 2 centimeters, tears the pouch, and gets rewards +2, -12. With the same gamma, G_0(tear) = 2 + 0.9*(-12) = -8.8. The learner should not copy the first visible motion from the successful rollout or avoid every squeeze from the failed rollout. It has to learn which state-action choices made later reward more likely. That is credit assignment: the third action got the visible success, but the first light grip may have set up the pouch so the later squeeze worked. If a random trial squeezes with 40 newtons and tears the pouch, the reward may teach something only after damaging hardware or the object. A practical learner therefore treats force > 25 newtons as outside the safe action set, not as useful curiosity. Reinforcement learning is powerful because the data come from interaction, but that same fact makes bad interaction costly.",
        "math": "A reinforcement-learning sample is a transition or rollout generated by interaction: (x_t,u_t,r_t,x_{t+1}). A three-step pouch rollout is tau = [(x_0,light_grip,0,x_1),(x_1,tilt,-1,x_2),(x_2,lift,+10,x_3)]. The return from time t is G_t = r_t + gamma*r_{t+1} + gamma^2*r_{t+2} + ... , so G_0 = 7.2 for the successful pouch rollout and G_1 = -1 + 0.9*10 = 8 for the state after the light grip. The objective is expected return, for example E[sum_t gamma^t r_t] under the trajectory distribution induced by the policy and environment. The word expected matters because one rollout is only one sample. Suppose the robot visits the same state x = 'pouch centered, fingers open, force limit 25 newtons' in five rollouts and observes returns 7.2, 6.1, 8.0, -8.8, and 7.5 after choosing light_grip. A Monte Carlo estimate would average them: (7.2 + 6.1 + 8.0 - 8.8 + 7.5)/5 = 4.0. More samples can move that number because the estimate is an empirical mean, not a label handed down by an expert. A value-based update might turn one observed transition into a target y = r_t + gamma max_{u'} Q(x_{t+1},u') and move Q(x_t,u_t) toward y. If Q(x,light_grip)=3.0, r_t=0, gamma=0.9, and max_{u'} Q(x_next,u')=8, then y = 0 + 0.9*8 = 7.2. With alpha = 0.5, the update is Q_new = 3.0 + 0.5*(7.2 - 3.0) = 5.1. A policy-gradient method instead changes policy parameters so actions from high-return rollouts become more likely. Either way, the data are consequences of the learner's own actions, not labels supplied ahead of time. The boundary is credit, exploration, and reward honesty: the learner may credit the wrong early action, avoid trying a necessary risky action, or exploit a reward that pays for lifting speed while omitting tearing force.",
    },
    "reward": {
        "run": "A table robot must move a glass cup to a marked square. The first reward a designer writes is simple: +10 if the cup reaches the square, -1 for each second used. Trial A is careful. The robot moves slowly, takes 6 seconds, keeps contact force below 8 newtons, and the cup arrives intact. Its written return is 10 - 6 = 4. Trial B is ugly. The robot slaps the cup across the table in 1 second, uses 35 newtons of contact force, chips the rim, and the cup still lands on the square. Its written return is 10 - 1 = 9. If the learner only sees that reward, Trial B is better. The problem is not that reward is useless. The problem is that the scalar signal was asked to stand for the whole task but forgot force, damage, and controlled motion. A better reward might be +10 for arrival, -1 per second, -0.5 per newton above 8, and -20 if the cup is damaged. Now add delayed reward. A drawer robot can tug gently for two seconds and then open the drawer on the third second, receiving rewards 0, 0, +10. Or it can yank hard, get +4 now for moving the handle, then jam the drawer and receive -6 next. With no discount, gentle return is 10 and yank return is -2. With gamma = 0.5, gentle return is 0 + 0.5*0 + 0.5^2*10 = 2.5, while yank return is 4 + 0.5*(-6) = 1. The delayed success still wins, but by less. The reward numbers decide how much patience the learner can afford.",
        "math": "A reward function maps state and action, or a transition, to a scalar such as r(x,u,x_next). Return accumulates those scalars over time, for example G_0 = sum_t gamma^t r_t. In the cup example, the first reward is r = 10*arrived - elapsed_seconds. It ranks Trial B above Trial A because 9 > 4. Add the missing damage terms and the score changes: Trial A remains 4 because it has no force excess or damage, while Trial B becomes 10 - 1 - 0.5*(35 - 8) - 20 = -24.5. For the drawer example, the gentle trajectory has rewards [0,0,10], so G_0(gentle; gamma=1)=10 and G_0(gentle; gamma=0.5)=0+0.5*0+0.25*10=2.5. The yank trajectory has rewards [4,-6], so G_0(yank; gamma=1)=-2 and G_0(yank; gamma=0.5)=4+0.5*(-6)=1. A smaller gamma makes later rewards count less; it does not change what the real drawer needs. The math did not discover the real task; it optimized the written measuring stick. The boundary is literalness: if safety, smoothness, impact, energy, patience, or task quality is absent from reward or constraints, the learner can improve return by violating the designer's unstated intent.",
    },
    "policy": {
        "run": "A hallway robot sees distance_to_wall = 0.45 meters, forward_speed = 0.8 m/s, and battery = 38 percent. A policy is the rule that turns that present information into the next command. One policy says: if distance_to_wall < 0.50 meters, set steering = -18 degrees and speed_command = 0.4 m/s. Another policy is stochastic: in the same state, choose slow-left with probability 0.8 and hard-left with probability 0.2. The policy is not the whole route to the charger. It is the closed-loop answer to 'what do I do now from this state?' After it commands slow-left, the robot may measure distance_to_wall = 0.62 meters and forward_speed = 0.35 m/s, so the next action is chosen from the new state, not from yesterday's written path. Now compare that with a fixed two-command script: first slow-left, then slow-left again. If the first turn already moves the robot to 0.62 meters from the wall, the script still turns left again and may drift to 0.90 meters, away from the hallway center. A feedback policy can instead say: if distance_to_wall > 0.60 meters, steer = +10 degrees and speed_command = 0.5 m/s. In the same second step, it corrects back toward center. The first command can match the script, but the second command is different because the measured state is different. If the policy ignores battery, it may steer safely around the wall while stranding the robot before it reaches the charger.",
        "math": "A deterministic policy has the form u = pi(x). A stochastic policy has the form pi(u|x), a distribution over actions conditioned on the current state or observation. In the hallway example, pi(slow-left|x) = 0.8 and pi(hard-left|x) = 0.2. Closed-loop rollout means x_{t+1}=f(x_t,u_t) with u_t drawn from pi(.|x_t) or set to pi(x_t). For a deterministic check, write x_0=(0.45, 0.8, 38). The policy gives u_0=(-18 degrees, 0.4 m/s), and the next measured state is x_1=(0.62, 0.35, 37). The open-loop script uses the stored command u_1=(-18 degrees, 0.4 m/s) again. The policy recomputes u_1=pi(x_1)=(+10 degrees, 0.5 m/s) because x_1 says the robot has moved past the safe middle. That is the difference between a list of actions and a rule. The policy's quality is judged through the state stream it creates: reward, cost, constraints, and future value are all consequences of repeatedly applying the rule. A policy that omits a needed state variable is a different controller, even if its action looks reasonable in one frame.",
    },
    "value-based-rl": {
        "run": "A warehouse robot reaches a fork while carrying a box. Its state is x = 'two meters from shelf 12, box loaded, battery 22 percent, aisle B blocked.' The two legal actions are turn_left and turn_right. A value-based learner does not first write a full steering policy. It writes a future-return scoreboard for actions. Today the table says Q(x,turn_left) = 3 and Q(x,turn_right) = 7, so the greedy action is turn_right. The robot tries turn_right, gets reward -1 for using another second, and lands in a state where the best stored next-action value is 10. With gamma = 0.9, the new target is y = -1 + 0.9*10 = 8. If the old estimate was 7 and the step size is alpha = 0.5, the updated entry becomes 7 + 0.5*(8 - 7) = 7.5. The action rule has changed because the scoreboard changed. Now make the next state visible. At x_next, the scoreboard says Q(x_next,charge_now)=10 and Q(x_next,inspect_box)=4. The epsilon-greedy behavior policy explores and actually chooses inspect_box, leading to a slow charger line. SARSA would use the action actually taken: y_SARSA = -1 + 0.9*4 = 2.6, so the same old 7 would update to 7 + 0.5*(2.6 - 7) = 4.8. Q-learning instead uses the greedy target action charge_now: y_Q = -1 + 0.9*10 = 8, giving 7.5. Same first transition, different target. If the estimate for charge_now is high only because the learner has never seen the slick floor after the corner, Q-learning may choose the worse aisle with mathematical confidence.",
        "math": "A state-value function V_pi(x) estimates return starting from state x and then following policy pi. An action-value function Q_pi(x,u) estimates return after taking action u first and then continuing. Value-based reinforcement learning alternates two jobs: policy evaluation, which moves V or Q toward returns or temporal-difference targets, and policy improvement, which chooses actions that look best under the updated values. In a simple Q-learning form, y = r + gamma max_a Q(x_next,a), and Q(x,u) <- Q(x,u) + alpha*(y - Q(x,u)). In the fork example, max_a Q(x_next,a)=10 because charge_now beats inspect_box in the table. The behavior policy is the rule that collected the sample in the real warehouse; here it was epsilon-greedy and picked inspect_box. The target policy is the rule used inside the update; for Q-learning it is greedy, so it prices the next state as if charge_now will be taken. SARSA uses y_SARSA = r + gamma Q(x_next,u_next), where u_next is the action actually taken by the behavior policy, so it gives 2.6 in the explored slow-line sample. Q-learning uses y_Q = r + gamma max_a Q(x_next,a), so it gives 8. The difference is not a naming detail. SARSA learns the value of behaving with exploration still present; Q-learning learns toward the greedy policy while using exploratory data to get coverage. The boundary is representation honesty: if the learned Q function generalizes from smooth floors to slick floors without sensing the difference, argmax will faithfully amplify the wrong number.",
    },
    "policy-optimization": {
        "run": "A small walking robot can choose short_step or long_step. In state x = 'left foot planted, body leaning forward 6 degrees, right knee bent 20 degrees,' its current policy gives pi_theta(long_step|x) = 0.30 and pi_theta(short_step|x) = 0.70. It tries long_step on a rubber mat, travels 0.18 meters, stays upright, and gets return G = 12. It tries short_step in a similar state, travels 0.05 meters, wobbles, and gets return G = 2. The local baseline is baseline b(x)=7, meaning the learner expected about 7 return from this kind of stance before seeing which step was taken. Now the comparison is not just '12 is bigger than 2.' It is A_long = 12 - 7 = +5 and A_short = 2 - 7 = -5. Long_step was better than expected; short_step was worse than expected. Policy optimization does not first fill a Q table and then take argmax. It changes theta so the sampled action with positive advantage becomes more likely in that kind of state, while the sampled action with negative advantage becomes less likely. With a small step, the same state may have pi_theta_new(long_step|x) = 0.38 and pi_theta_new(short_step|x) = 0.62. That is the learned controller changing at the place where actions are chosen. The probability shift is earned by advantage, not by the action name. If the reward forgot knee impact, the method can make long_step more likely even while wearing out the joint.",
        "math": "The objective is expected return under the policy, written as J(theta)=E_{tau~pi_theta}[G(tau)]. A policy-gradient update estimates g = E[grad_theta log pi_theta(u_t|x_t) * A_t], where A_t is a return, reward-to-go, or advantage telling whether the sampled action was better than the local baseline. Then theta_new = theta + eta*g. In a two-action softmax picture, theta can be read as scores before probabilities are normalized. With eta = 0.04, the long-step sample gives Delta score_long = 0.04*5 = 0.20, while the short-step sample gives Delta score_short = 0.04*(-5) = -0.20. Those score moves do not promise the exact 0.30 to 0.38 probability change; they explain the direction and size of the pressure before the softmax turns scores into probabilities. The transcript's surrogate objective idea is an implementation trick: choose a differentiable loss whose gradient is the policy gradient, then use automatic differentiation to get g. Unlike value-based RL, the policy is explicit; no separate argmax over Q is needed at action time. The boundary is sample honesty and step size. Suppose the robot later tries long_step on a tile floor, slips, and gets return G = -8. Against the same baseline, A_tile = -8 - 7 = -15. With eta = 0.20, Delta score = 0.20*(-15) = -3.0, a much larger move. That update may be correct for tile, but rubber mat and tile floor are different states. If the state description does not separate them, or if the step is too large, one bad tile rollout can erase a useful rubber-mat action. Noisy returns can push the probability of a lucky bad action upward, and a large eta can move the policy so far that the collected rollout no longer describes the new controller.",
    },
    "exploration": {
        "run": "A warehouse gripper has learned one safe pull for a drawer handle: approach at 0 degrees, close with 18 newtons, and pull at 0.04 m/s. It succeeds 7 out of 10 times. A nearby unexplored action approaches at 12 degrees with 22 newtons. It might catch the handle better, but it might also scrape the cabinet. If the robot always takes the known action, its data stay crowded around one corner of the state-action space and it never learns whether the angled pull works. If it tries random torques up to 60 newtons, it may break the handle before learning anything useful. Exploration is the controlled decision to spend some trials on uncertain actions because the information may improve future control. For example, an epsilon-greedy policy with epsilon = 0.10 tries a non-greedy pull on about 10 of 100 attempts while using safety limits force <= 25 newtons and handle_angle <= 15 degrees. The known pull has 7/10 = 0.70 success, but the angled pull has no honest number yet because it has not been tested in the same states. A useful exploration batch separates the states instead of mixing them together. On shallow handles, the robot tries 10 shallow-handle trials at 12 degrees and sees 9 successes and 1 slip. On deep handles, it tries 4 deep-handle trials and sees 1 success and 3 scrapes. The lesson is not '12 degrees is good.' The lesson is narrower and more useful: for shallow handles, the new estimate is 9/10 = 0.90, so the gain over the old pull is 0.90 - 0.70 = 0.20. If the warehouse will see 100 more shallow handles, that is about 20 more successful pulls per 100 shallow handles before counting wear or delay. For deep handles, the same action looks bad and the sample is small, so the controller should keep the old pull or collect a safer nearby test. Exploration helped because it made the missing comparison visible in the state where the controller must choose. It did not grant permission to generalize shallow-handle evidence to deep handles.",
        "math": "Exploration changes the distribution over sampled state-action pairs. With epsilon-greedy action choice, pi_explore(u|x) = 1 - epsilon for the current best action plus exploration mass over other legal actions. At epsilon = 0.10, a simple 100-attempt picture is 90 greedy pulls and 10 exploratory pulls, after clipping the legal action set to A_safe(x) = {force <= 25, handle_angle <= 15}. In that problem, force = 60 is outside A_safe(x). It is not bold exploration; it is a test the robot is not allowed to run. Another view is uncertainty bonus: choose the action that maximizes Q(x,u) + beta*uncertainty(x,u), so an action with lower estimated value can be tried when its uncertainty is large. Suppose the current shallow-handle estimates are Q(x,straight)=0.70 with uncertainty(straight)=0.05 and Q(x,angled)=0.60 with uncertainty(angled)=0.40. With beta = 0.5, the straight score is 0.70 + 0.5*0.05 = 0.725, while the angled score is 0.60 + 0.5*0.40 = 0.80. That score makes angled worth a safe trial even though its current value estimate is lower. After the 10 shallow trials produce 9 successes, the estimate can move toward 0.90 and uncertainty drops to 0.10. Now the angled action is not a blind gamble for shallow handles; it is a better-supported choice. The same data do not justify using it on deep handles, because those states produced only 1 success and 3 scrapes in 4 attempts. The useful question is not whether an action is random; it is whether the new sample can change the controller's future decisions enough to justify its cost and risk. The boundary is coverage under constraints. Too little exploration leaves Q or policy gradients blind in rarely visited states; too much exploration makes the data expensive, unsafe, or dominated by states the final policy should never visit.",
    },
    "model-based-rl": {
        "run": "A cart robot must stop 0.20 meters before a shelf. It has only 80 real trials before the bumper wears out. Instead of learning only by trying policies on hardware, it records transitions such as x = (position 1.40 m, velocity 0.60 m/s), u = brake 30 percent, x_next = (position 1.46 m, velocity 0.48 m/s). From many triples like this, it fits a learned dynamics model f_hat(x,u). Now the robot can test candidate action sequences inside the model. Sequence A brakes 20 percent for three steps and the model predicts final position 0.08 meters from the shelf, which violates the 0.20 meter margin. Sequence B brakes 40 percent, then 30 percent, then 20 percent and predicts final position 0.24 meters from the shelf with lower time cost than stopping early. Sequence C brakes 60 percent, then 0 percent, then 0 percent. The learned model predicts it will stop 0.28 meters from the shelf and save 0.4 seconds, so the optimizer likes it. But the old 80-trial dataset had only 3 transitions with brake above 50 percent on dusty floor. On the real cart, that first 60 percent brake makes the wheels slide, and the measured next state is position 1.58 m, velocity 0.55 m/s instead of the model's predicted position 1.54 m, velocity 0.42 m/s. The planner has found a weak spot in the model. Model-based RL is useful because it can reject bad-looking plans before spending hardware trials, but it is dangerous when planning asks the model about states and inputs the data barely covered. A safer loop executes only the first brake command, measures the real next state, adds that transition to the data, and replans. After adding the dusty-floor transition, the next model no longer treats 60 percent braking as a clean stop. The real value is not pretending the model is reality; it is using the model to spend scarce hardware trials on plans that already look plausible, then using real measurements to keep the model honest.",
        "math": "The learned model is a transition predictor, for example x_{t+1}=f_hat(x_t,u_t) or a distribution p_hat(x_{t+1}|x_t,u_t). A model-based RL loop is: run a policy to collect (x_t,u_t,x_{t+1}) data, fit f_hat, optimize a candidate sequence [u_0,u_1,u_2] by rolling it through f_hat, execute u_0, then repeat in receding-horizon form. For Sequence C, the one-step prediction error is visible: f_hat predicts (1.54, 0.42), but reality gives (1.58, 0.55). The position error is 1.58 - 1.54 = 0.04 m and the velocity error is 0.55 - 0.42 = 0.13 m/s after one step. If the same error repeats for three predicted steps, the final stop margin can disappear. With uncertainty, the planner may sample 20 possible models from an ensemble, roll out the same candidate sequence under each model, and score the average predicted return minus a risk penalty. Suppose five ensemble models predict final shelf margins for Sequence C of 0.28, 0.26, 0.09, -0.04, and 0.31 meters. The mean margin is (0.28 + 0.26 + 0.09 - 0.04 + 0.31)/5 = 0.18 meters, which is below the required 0.20 meters, and the spread warns that the model is unsure. Sequence B might have ensemble margins 0.24, 0.23, 0.25, 0.22, and 0.24 meters, giving mean 0.236 meters with much less disagreement. This is where uncertainty changes planning: not by making the model true, but by showing where predictions should be trusted less. This is where model-based RL differs from value-based or direct policy-gradient learning: the learner builds a small simulator of the dynamics and puts planning inside the learning loop. The boundary is model exploitation. If f_hat underestimates braking distance by 0.10 meters near the shelf, the optimizer can choose a sequence that looks safe in the learned model and hits the shelf in the real system. Receding-horizon replanning and adding new transitions narrow the gap between the old data distribution and the state distribution created by the planner, but they do not erase bad sensors, missing floor conditions, or a model that is confident for the wrong reason.",
    },
}


def concept_run(concept: dict[str, Any]) -> dict[str, str]:
    return CONCEPT_RUNS[concept["id"]]


FAMILY_DEEPENING: dict[str, dict[str, str]] = {
    "problem-setup": {
        "pressure": "This family exists because a moving system does not obey wishes. A planner must name what is known, what can be changed, how the world moves, what future is preferred, and which lines cannot be crossed.",
        "operation": "Turn a story into state, action, dynamics, cost, horizon, constraints, and feasibility before choosing any solver.",
        "worked": "For a drone delivery task, 'get there fast' becomes position, velocity, attitude, battery, payload, wind, rotor thrust, no-fly zones, landing pad error, and safe touchdown speed.",
        "wrong_turn": "Choosing a solver before naming these pieces turns a control problem into a guess about tools.",
        "boundary": "The setup is only as good as the state, action set, dynamics, objective, and constraints that were actually written.",
    },
    "optimization-foundations": {
        "pressure": "Before control chooses a path, ordinary optimization teaches what it means for a choice to be locally better, blocked by a constraint, or stuck at a boundary.",
        "operation": "Look at small changes in the decision and ask whether the objective can still be lowered without leaving the legal set.",
        "worked": "A thermostat setting may lower temperature error but hit a power limit. The gradient points toward a better setting; the constraint says whether that setting is legal.",
        "wrong_turn": "Treating a stationary point as a final answer hides boundaries, constraints, and local traps.",
        "boundary": "This family explains one decision snapshot; control still has to carry state through time.",
    },
    "trajectory-optimization": {
        "pressure": "A path is not a drawing between start and finish. Every point along it must be reachable from the previous point using real commands.",
        "operation": "Make the whole path the decision, enforce dynamics along the path, and ask the solver for a legal low-cost history.",
        "worked": "A robot arm moving around a fixture needs joint angles, velocities, and torques at many times, not just a start pose and an end pose.",
        "wrong_turn": "Checking only endpoints can hide collision, torque spikes, or fast motion between the checked points.",
        "boundary": "The path result depends on model accuracy, grid resolution, constraint fidelity, and whether the solver found a good local candidate.",
    },
    "dynamic-programming": {
        "pressure": "Some problems are too large if the controller lists every future action sequence. The repeated structure is that after one action, the remaining future is another control problem.",
        "operation": "Attach a future-cost number to each state, then compare actions by immediate cost plus the future value of the state they create.",
        "worked": "A rover chooses between a short rocky route and a longer smooth route by pricing wheel damage as a worse future state, not only by counting meters.",
        "wrong_turn": "Comparing immediate cost alone erases the burden carried by the next state.",
        "boundary": "The recursion is truthful only if the state contains the information needed for future consequences.",
    },
    "local-structure": {
        "pressure": "Near a planned motion, the full nonlinear problem may be more detail than the controller needs at every instant.",
        "operation": "Replace the local neighborhood with linear dynamics and quadratic cost, compute fast feedback, and use it only while the state stays near that neighborhood.",
        "worked": "A drone hovering near level can push back against a small drift with LQR; after impact, the same approximation is no longer a truthful picture.",
        "wrong_turn": "Using local feedback after the system leaves the local region treats a false approximation as the real machine.",
        "boundary": "The family stops at large deviations, contact changes, saturation, and model regions where linear/quadratic structure no longer describes the behavior.",
    },
    "safety-and-feasibility": {
        "pressure": "A plan can look good and still put the system into a state where no safe future remains.",
        "operation": "Track sets of states that can reach a target, avoid danger, or remain feasible after the next action.",
        "worked": "A car entering a narrow gap should ask whether braking or steering remains possible one second later, not only whether the next two seconds are collision-free.",
        "wrong_turn": "Treating safety as a soft preference can allow a cheap plan that crosses a hard boundary.",
        "boundary": "The set calculation depends on the modeled controls, disturbances, target sets, and time horizon.",
    },
    "replanning": {
        "pressure": "A long open-loop plan goes stale as soon as wind, traffic, contact, or estimation error changes the state.",
        "operation": "Solve a short future problem, apply the first command, measure again, and solve from the new state while protecting the next solve.",
        "worked": "An autonomous car replans after each small movement because nearby cars move and the measured state is more trustworthy than yesterday's prediction.",
        "wrong_turn": "Believing every feasible short-horizon solve is safe misses the state handed to the next solve.",
        "boundary": "Replanning needs terminal structure, backup policy, reachable set, or another guard when short horizons hide delayed danger.",
    },
    "learning-based-control": {
        "pressure": "Sometimes the model, reward, or expert behavior is too hard to write down cleanly, but data can show part of the missing structure.",
        "operation": "Fit a policy, value, reward, or model from demonstrations or experience, then keep asking what state distribution, reward, and safety boundary the learner is actually using.",
        "worked": "A warehouse robot can clone a human drawer-opening motion, then use reward or a learned model to improve, while checking that mistakes do not move it outside the demonstrated states.",
        "wrong_turn": "Treating data as a replacement for control thinking hides distribution shift, reward loopholes, unsafe exploration, and learned-model error.",
        "boundary": "Learning is only credible where the data, reward, model, and deployment state distribution cover the behavior being asked of the controller.",
    },
}


PRIMITIVE_DEEPENING: dict[str, str] = {
    "state": "The state is the present-tense record the controller trusts. If the record leaves out velocity, fuel, contact, or another car, two different futures may look identical.",
    "action": "The action is the command the machine can actually issue, not the outcome it wants. A drone commands thrust; height changes only after dynamics carry thrust forward.",
    "dynamics": "Dynamics are the rule that turns action into the next state. They are where mass, friction, actuator limits, and delay enter the story.",
    "cost": "Cost is the written scoreboard for futures. If damage, discomfort, or risk is missing from it, the controller is free to ignore those things.",
    "constraint": "A constraint is a line the plan may not cross: no collision, no empty battery, no torque beyond the motor, no state outside the safe set.",
    "value": "Value is future cost compressed into a number attached to the current state. It lets the controller compare actions without listing every later move.",
    "policy": "A policy is the rule that turns current information into an action. In closed loop, its own actions create the next states it must handle.",
    "uncertainty": "Uncertainty means the next state is not a single promised outcome. Wind, sensor noise, human drivers, and learned-model error all widen the future.",
    "feasibility": "Feasibility asks whether any legal plan exists before asking which legal plan is best.",
}


PRIMITIVE_TESTS: dict[str, dict[str, str]] = {
    "state": {
        "question": "What must be remembered right now so the next command can be predicted?",
        "run": "Two cars share the same lane position. One is centered and steady; the other is sliding with a fast rear car closing. A position-only state would tell both cars to do the same thing, which is physically wrong.",
        "failure": "Missing state turns different futures into the same record, so the controller acts blind.",
    },
    "action": {
        "question": "What command can the machine actually receive?",
        "run": "A drone can want to rise two meters, but the command is rotor thrust or a lower-level velocity target. The height change arrives only after thrust changes acceleration and velocity.",
        "failure": "A fake action asks the plan to choose an outcome the actuator cannot directly produce.",
    },
    "dynamics": {
        "question": "How does the command change the next state?",
        "run": "The same steering command on dry pavement and ice creates different next states. The dynamics are where tire grip, delay, mass, and actuator limits enter the story.",
        "failure": "Wrong dynamics make a future look legal on paper and fail on the real system.",
    },
    "cost": {
        "question": "Which future is the controller being asked to prefer?",
        "run": "A parking controller that prices only time may scrape a wall. Adding distance, steering effort, wall clearance, and final alignment changes what counts as a good future.",
        "failure": "A thin cost makes the controller obey the written scoreboard while violating the human task.",
    },
    "constraint": {
        "question": "What line may not be crossed even if crossing it lowers cost?",
        "run": "A robot arm may save energy by passing through a shelf. Collision is not a tradeoff to be balanced away; it removes that path from the legal set.",
        "failure": "A missing constraint lets the optimizer find a cheap answer that the world will not allow.",
    },
    "value": {
        "question": "What future burden is attached to standing in this state?",
        "run": "A rover one step from sharp rocks should not ask only about the next meter. It should ask what future travel costs after wheel damage.",
        "failure": "Without value, delayed damage, battery drain, and lost options are invisible to the current action.",
    },
    "policy": {
        "question": "What rule chooses the next action from the current information?",
        "run": "A thermostat policy turns temperature into heat on or off. A robot policy turns camera and joint information into a gripper command, then has to handle the next state its own command creates.",
        "failure": "A policy trained only on clean states may fail after its own small mistake creates an unfamiliar state.",
    },
    "uncertainty": {
        "question": "Which part of the next state is not promised?",
        "run": "A rover crossing gravel may move forward, slip left, or slip right. The action must be priced over possible next states, not a single hoped-for outcome.",
        "failure": "Ignoring uncertainty makes a controller trust a future that wind, gravel, sensors, drivers, or model error can break.",
    },
    "feasibility": {
        "question": "Does any legal future remain from this state?",
        "run": "A car too close to a wall at high speed may have no steering or braking command that avoids collision. Before choosing the best plan, the controller must know whether the legal set is empty.",
        "failure": "If feasibility is skipped, the solver can return emergency behavior or no plan after the system is already boxed in.",
    },
}


FORMULA_EXPLAINERS: list[dict[str, str]] = [
    {
        "name": "Dynamics",
        "shape": "x_next = f(x, u)",
        "problem": "A command is not a teleport. If the car turns the steering wheel, the next state depends on current speed, tire grip, and heading.",
        "object": "The object is a transition rule from present state and action to next state.",
        "operation": "Feed in the state and action, then propagate the consequence one step forward.",
        "worked": "If a drone has upward velocity 1 m/s and the controller cuts thrust, the next height may still rise for a moment while velocity falls. Dynamics explain that delay.",
        "failure": "If the model ignores wind, ice, contact, or actuator lag, the controller prices a future that the real system will not follow.",
        "input": "present state and command",
        "output": "next state or state derivative",
        "wrong_read": "Reading f as a label instead of the physical rule that turns commands into motion.",
    },
    {
        "name": "Objective",
        "shape": "total cost = path costs + terminal cost",
        "problem": "A future is not good just because it reaches the goal. It may use too much fuel, hit a wall, arrive late, or end with unsafe speed.",
        "object": "The object is a cost functional: a rule for scoring a whole history.",
        "operation": "Add the cost paid along the path and the cost left at the end.",
        "worked": "A rocket landing score can add fuel burn every second, then add a large final penalty for height error and touchdown speed.",
        "failure": "If the written cost omits damage or risk, the optimizer can choose a future that is cheap on paper and bad in the world.",
        "input": "a candidate state-action history",
        "output": "one score for comparing that history with another",
        "wrong_read": "Treating the cost as intention instead of the written scoreboard the optimizer will obey.",
    },
    {
        "name": "Bellman Recursion",
        "shape": "V(x) = best action of cost now + value next",
        "problem": "The controller needs to judge a current action by the future state it creates, without listing every complete future.",
        "object": "The object is a value function: future cost stored at each state.",
        "operation": "For each action, add immediate cost to the value of the next state, then choose the best sum.",
        "worked": "A rover may pay one extra minute to avoid sharp rocks because the next state after the rocky shortcut has damaged wheels and worse future value.",
        "failure": "If the state is missing hidden information, the value table attaches the wrong future price to that state.",
        "input": "current state, candidate action, one-step cost, and next-state value",
        "output": "the best future cost attached to the current state",
        "wrong_read": "Reading the recursion as algebra only, without asking what next state each action creates.",
    },
    {
        "name": "Hamiltonian",
        "shape": "H = stage cost + costate times dynamics",
        "problem": "A small action change affects cost now and also pushes the whole future state history.",
        "object": "The object is a local package that combines immediate cost with a backward price on state motion.",
        "operation": "Price a control change by adding what it costs now to what its state change costs later.",
        "worked": "For a rocket, more thrust burns fuel now but changes future velocity. The costate says how valuable that velocity change is later near touchdown.",
        "failure": "Hamiltonian conditions are necessary conditions; they can identify a candidate path without proving it is the best global path.",
        "input": "state, control, current cost, dynamics, and costate price",
        "output": "a local stationarity test for a candidate optimal control",
        "wrong_read": "Treating the Hamiltonian as energy here instead of a cost-and-dynamics bookkeeping device.",
    },
    {
        "name": "MPC",
        "shape": "solve horizon, apply first action, measure, repeat",
        "problem": "A long plan becomes stale after the first gust of wind, moving car, or bad state estimate.",
        "object": "The object is a finite-horizon problem rebuilt from the current measured state.",
        "operation": "Solve, use only the first command, shift the horizon, and solve again.",
        "worked": "A car plans five seconds ahead but executes only 0.1 seconds of steering and throttle before traffic is measured again.",
        "failure": "A short horizon without terminal protection can make a legal first move that leaves no legal move next time.",
        "input": "measured state, model, horizon, cost, and constraints",
        "output": "the first command of a newly solved short plan",
        "wrong_read": "Thinking MPC trusts the whole plan instead of deliberately throwing most of it away after measuring again.",
    },
    {
        "name": "Policy Gradient",
        "shape": "move policy parameters toward higher return",
        "problem": "Sometimes the learner has no clean model or action labels, only rollouts and delayed reward.",
        "object": "The object is a parameterized policy that chooses actions from observations or states.",
        "operation": "Use rollout returns to nudge the policy toward actions that led to higher long-run reward.",
        "worked": "A grasping robot tries many wrist angles; successful lifts increase the probability of similar actions in similar poses.",
        "failure": "Sparse reward, unsafe exploration, or random lucky rollouts can push the policy in the wrong direction.",
        "input": "rollouts, rewards, and current policy parameters",
        "output": "a parameter update direction for the policy",
        "wrong_read": "Treating a successful rollout as proof every action in it deserves credit.",
    },
]


CONCEPT_OVERVIEW_FAMILIES: list[dict[str, str]] = [
    {
        "family": "Problem setup",
        "pressure": "The learner must first stop saying what they want and start naming what the machine can actually know and command.",
        "ordinary_run": "For a drone landing on a pad, state is height, velocity, attitude, battery, payload, and wind estimate; action is thrust or a lower-level motion command; dynamics say how thrust changes motion; cost prices time, energy, landing error, and smoothness; constraints forbid no-fly zones, empty battery, and hard touchdown.",
        "failure_test": "If two physically different situations get the same state, or if the action asks for an outcome instead of a command, the setup is lying before any solver runs.",
    },
    {
        "family": "Trajectory optimization",
        "pressure": "A path is a history, not a line drawn between start and finish. Every piece of that history must be reachable from the previous piece.",
        "ordinary_run": "For a robot arm near a shelf, a short geometric path can pass through a joint state that needs torque above the motor limit. Direct transcription and collocation make the hidden middle of the path visible to the solver.",
        "failure_test": "If the grid is too coarse, a solution can satisfy every written dot while hiding a collision, torque spike, or fast unstable motion between dots.",
    },
    {
        "family": "Dynamic programming",
        "pressure": "The next action matters because it creates the state from which all later actions must be chosen.",
        "ordinary_run": "For a rover choosing between a rocky shortcut and a longer smooth route, Bellman reasoning compares distance now plus the future cost of damaged wheels, not distance alone.",
        "failure_test": "If the state does not include wheel health, battery, or another delayed burden, the value function stores the wrong price for the future.",
    },
    {
        "family": "Local structure",
        "pressure": "Sometimes the full nonlinear problem is too much, but the system is close enough to a planned motion for a local picture to tell the truth.",
        "ordinary_run": "For a hovering drone pushed a few centimeters sideways, linearized dynamics and a quadratic bowl around the target can produce a fast feedback correction.",
        "failure_test": "After impact, contact, actuator saturation, or tumbling, the local picture no longer describes the machine the controller is actually moving.",
    },
    {
        "family": "Safety and replanning",
        "pressure": "A plan can be legal for the next few seconds and still hand the controller a state with no legal future.",
        "ordinary_run": "For a car entering a narrow traffic gap, MPC may find a collision-free two-second path, but recursive feasibility asks whether braking or steering remains possible after the first command.",
        "failure_test": "If today's first action makes tomorrow's optimization infeasible, the controller was not planning safely even though the current solve looked clean.",
    },
    {
        "family": "Learning-based control",
        "pressure": "Data enters when the model, reward, contact strategy, or expert behavior cannot be fully written by hand.",
        "ordinary_run": "For a warehouse robot, demonstrations can teach a drawer-pulling motion, reward can improve repeated attempts, and a learned model can rehearse shelf contacts before hardware trials.",
        "failure_test": "If the learned policy visits states outside the demonstrations, or if the reward omits damage and force, more training can make the wrong behavior more reliable.",
    },
]


REVIEW_WALKTHROUGH: list[dict[str, str]] = [
    {
        "title": "Setup Page Test",
        "sample": "Open State, Action / Control Input, Dynamics, Objective / Cost Function, and Constraints.",
        "pass": "A passing page lets the reviewer rebuild a drone, car, or robot setup before any formal label appears. It says what the controller knows, what command it can issue, how the world changes, what future is preferred, and what is forbidden.",
        "reject": "Reject a page that only defines the term or says the idea matters. The page must show a real command moving a real state and name the visible failure caused by a missing variable, impossible action, wrong model, weak cost, or soft constraint.",
    },
    {
        "title": "Path Page Test",
        "sample": "Open Trajectory Optimization, Direct Transcription, Shooting Methods, and Collocation.",
        "pass": "A passing page makes clear that the answer is a whole history of states and actions. It should show why a smooth-looking path can still be illegal because dynamics, torque, collision, or grid spacing expose a hidden middle.",
        "reject": "Reject a page that treats the method as a solver choice without saying what variables are created, what defects are enforced, what simulation is run, or what can be missed between grid points.",
    },
    {
        "title": "Future-Price Page Test",
        "sample": "Open Value Function, Bellman Recursion, Dynamic Programming, and Stochastic Dynamic Programming.",
        "pass": "A passing page makes future consequence feel like an object attached to the current state. A rover, option, battery, or wheel-damage example should show why the next action is judged by the state it creates.",
        "reject": "Reject a page that only writes the recursion. It must explain what the value stores, why the state must contain delayed burdens, and how uncertainty changes one promised next state into an average over possible next states.",
    },
    {
        "title": "Replanning Safety Test",
        "sample": "Open Model Predictive Control, Recursive Feasibility, Reachability, and Stability Under Replanning.",
        "pass": "A passing page distinguishes a legal short plan from a safe handoff to the next solve. It should show a car, drone, or warehouse robot taking one command and then asking whether the next state still has a legal future.",
        "reject": "Reject a page that praises replanning without naming the first action, the measured next state, the terminal protection, the safe set, or the failure where tomorrow's optimization has no escape.",
    },
    {
        "title": "Learning Page Test",
        "sample": "Open Imitation Learning, Behavioral Cloning, Distribution Shift, Reward, Reinforcement Learning, Policy Optimization, Exploration, and Model-Based RL.",
        "pass": "A passing page keeps control thinking alive after data appears. It names the state distribution, reward loophole, exploration risk, learned-model error, and closed-loop states created by the learner's own actions.",
        "reject": "Reject a page that treats learning as magic performance gain. The page must say what signal is learned from, what the learner can exploit, and what hardware or task failure appears when the signal is incomplete.",
    },
]


QUALITY_TESTS: list[dict[str, str]] = [
    {
        "title": "Start With A Machine, Not A Term",
        "weak": "State is a vector used by the controller.",
        "strong": "A car at the same lane position can need different steering if one version is sliding and the other is moving straight. State is the record that preserves that difference before the controller chooses.",
        "test": "The sentence passes only if a reader can picture the thing being moved and say why the formal object must exist.",
    },
    {
        "title": "Name The Command The World Receives",
        "weak": "The action changes the system.",
        "strong": "A drone cannot command height directly. It commands thrust; thrust changes acceleration, acceleration changes velocity, and velocity changes height.",
        "test": "The sentence passes only if it separates the desired outcome from the command the actuator or policy can issue.",
    },
    {
        "title": "Turn Math Into An Operation",
        "weak": "The Bellman equation relates current and future value.",
        "strong": "For each rover move, add the cost of that move to the stored future cost of the state it creates, then choose the smallest total.",
        "test": "The sentence passes only if the reader can perform the operation on a small example before reading symbols.",
    },
    {
        "title": "Make Failure Visible",
        "weak": "MPC requires care with feasibility.",
        "strong": "A car can fit through a gap for two seconds and still be in trouble if the first acceleration leaves no legal braking or steering move for the next solve.",
        "test": "The sentence passes only if it shows the concrete bad state that appears when the assumption is missing.",
    },
    {
        "title": "Keep Learning Inside Control",
        "weak": "Behavioral cloning learns from demonstrations.",
        "strong": "A cloned gripper policy trains on expert states. If its own small mistake nudges the object eight centimeters sideways, the policy may now face a state the expert data never labeled.",
        "test": "The sentence passes only if it names the data source, the closed-loop state the learner creates, and the failure caused by the gap.",
    },
    {
        "title": "Tie Evidence To The Exact Claim",
        "weak": "The lecture discusses reachability.",
        "strong": "The transcript window names reachable sets and targets; the page adds the learner rule that safety is a question about which states can still avoid a bad target under allowed controls and disturbances.",
        "test": "The sentence passes only if it separates what the transcript says from what the course page adds as explanation.",
    },
    {
        "title": "Use Numbers When They Expose The Tradeoff",
        "weak": "The rocket must balance fuel and landing speed.",
        "strong": "At 80 meters and -18 m/s, a hard one-second burn may leave -12 m/s for the next state, while a weak burn may leave -20 m/s and make the last 30 meters unrecoverable under thrust limits.",
        "test": "The sentence passes only if the numbers change the decision pressure, not if they decorate a claim already made in words.",
    },
    {
        "title": "Say Where The Method Stops",
        "weak": "LQR works near a nominal point.",
        "strong": "LQR can correct a two-centimeter hover drift because the local dynamics and cost still look like the planned model. After a branch strike, tumbling and actuator saturation put the drone outside that local picture.",
        "test": "The sentence passes only if it gives both the inside case and the outside case, so the learner can see the boundary.",
    },
]


PROVENANCE_CHECKS: list[tuple[str, str]] = [
    (
        "Source Capture",
        "Start with the playlist record, then inspect the raw VTT and cleaned transcript for the lecture. The raw file keeps timestamped caption evidence; the clean file makes the words searchable. If either layer is missing, a concept page should not pretend to have local transcript support.",
    ),
    (
        "Evidence Record",
        "Open the matching row in analysis/evidence/evidence-ledger.json. A trustworthy record names the video id, timestamp, local transcript path, transcript window, what the transcript supports, and what the page adds beyond the transcript.",
    ),
    (
        "Teaching Synthesis",
        "Open the concept or teaching artifact that uses the record. The page may explain more than the transcript says, but it must keep the boundary visible. The transcript can support that Lecture 11 discusses reachable sets; the page can then synthesize the learner rule about safe states and bad targets.",
    ),
    (
        "Generated Page",
        "Open the rendered HTML after rebuilding. The page should contain the same evidence anchor and the same first-principles structure: ordinary pressure, object, operation, concrete run, math one level deeper, and boundary.",
    ),
    (
        "Validation Gate",
        "Run the validator after rendering. The validator checks links, evidence anchors, transcript coverage, required teaching markers, word floors, broad anti-filler phrases, and concept-page richness markers.",
    ),
    (
        "Manual Review Override",
        "Some evidence rows need human wording after the automatic transcript match. Those overrides live in analysis/evidence/manual-review-overrides.json. They should make the transcript support sharper, not inflate it into a claim the lecture did not make.",
    ),
    (
        "Durable Edit Rule",
        "If a reviewer wants a richer explanation, the edit belongs in scripts/build_site.py, scripts/build_first_principles_atlas.py, scripts/build_teaching_artifacts.py, or the analysis source files that feed them. Editing only the rendered HTML creates a stale page that the next build will overwrite.",
    ),
    (
        "Cold Rebuild Rule",
        "A clean rebuild is the proof that the course is reproducible. Delete nothing by hand; run the generator chain and validator. If the same 57 pages, 38 concepts, 38 evidence records, and teaching artifacts reappear, the source layer and rendered layer still agree.",
    ),
]


COMPLETION_REQUIREMENTS: list[tuple[str, str, str]] = [
    (
        "Playlist Source Coverage",
        "19/19 lectures have local transcript records and the transcript index reports 207,618 words.",
        "This proves source availability, not teaching quality. A reviewer still has to inspect whether the page uses the transcript honestly.",
    ),
    (
        "Concept Coverage",
        "38 concept pages are generated from the atlas, and each concept page must include ordinary pressure, object, concrete run, math one level deeper, boundary, and transcript evidence markers.",
        "This proves every named concept has the required structure. It does not prove every paragraph has reached the richest possible explanation.",
    ),
    (
        "Evidence Coverage",
        "38 evidence records are rendered with anchors, transcript windows, support statements, and synthesis boundaries; manual review remaining is zero in the audit artifact.",
        "This proves every concept can be traced to a local evidence record. It does not mean the transcript alone proves every teaching sentence.",
    ),
    (
        "Teaching Artifacts",
        "Derivations, worked examples, drills, solutions, and weak-claim repairs are generated from source artifacts and validated for concrete runs, transfer checks, setup hints, grading criteria, and replacement rules.",
        "This proves the practice layer exists and has required fields. A reviewer should still solve at least two drills to test whether the solution reasoning feels transferable.",
    ),
    (
        "Editorial Gates",
        "The validator enforces page markers, concept word floors, top-level word floors, broad anti-filler phrases, evidence anchors, local links, and generated site coherence.",
        "This proves a baseline bar. It cannot replace reading the site against the reference explainers for rhythm, depth, and plain everyday language.",
    ),
]


COMPLETION_SAMPLE_CHECKS: list[tuple[str, str]] = [
    (
        "State And Action",
        "Open state.html and action-control-input.html. The reviewer should be able to say why lane position is not enough for a car and why a drone commands thrust rather than height. If either page starts and ends as a definition, the setup layer is not complete.",
    ),
    (
        "Bellman And Value",
        "Open bellman-recursion.html and value-function.html. The reviewer should see the rover-style future-price idea before symbols: pay now, enter a new state, inherit the future burden from that state.",
    ),
    (
        "MPC And Reachability",
        "Open model-predictive-control.html and reachability.html. The reviewer should see the difference between a short legal plan and a state set that protects future safety under controls and disturbances.",
    ),
    (
        "Learning Boundary",
        "Open behavioral-cloning.html and reward.html. The reviewer should see the exact closed-loop risk: a learned policy visits states outside the data, or a reward omits damage and teaches the wrong behavior.",
    ),
    (
        "Practice Transfer",
        "Open drills.html and solutions.html. The reviewer should be able to change drone delivery to indoor delivery, or traffic MPC to a narrow drone window, and still use the same reasoning.",
    ),
]


LECTURE_DEEPENING: dict[int, dict[str, str]] = {
    1: {
        "problem": "The course first has to make control visible in ordinary systems: a car, drone, thermostat, or robot changes because commands push state through time.",
        "move": "Name the basic pieces before choosing methods: state, action, dynamics, objective, horizon, and constraints.",
        "run": "A drone delivery problem becomes concrete only after height, velocity, attitude, battery, thrust, wind, landing error, and no-fly zones are named.",
    },
    2: {
        "problem": "Before a controller can choose a path, it needs the grammar of a single constrained decision: what can move, what is legal, and what local change lowers cost.",
        "move": "Use finite-dimensional optimization, gradients, open sets, and constraints as the small-scale version of later control problems.",
        "run": "A heater setting that lowers temperature error may violate a power limit; the gradient points downhill, but the constraint says whether that move is allowed.",
    },
    3: {
        "problem": "A path cannot be judged by one point. The whole curve has cost, endpoints, and legal motion along the way.",
        "move": "Shift from choosing numbers to choosing functions or trajectories, then ask how total cost changes when the whole path is nudged.",
        "run": "A rocket arc that starts and ends correctly can still waste fuel in the middle; calculus of variations asks what path-wide nudge would lower the total cost.",
    },
    4: {
        "problem": "A small state error now can change fuel, velocity, and endpoint error later, so present controls need a price for downstream state changes.",
        "move": "Introduce costates and the Hamiltonian as local bookkeeping for immediate cost plus future state sensitivity.",
        "run": "More rocket thrust costs fuel now, but it may reduce a costly terminal velocity error. The costate prices that later benefit.",
    },
    5: {
        "problem": "Necessary equations are not enough if the actual path still has to be computed on a machine.",
        "move": "Connect optimality conditions to computational methods and the practical burden of solving trajectory problems.",
        "run": "A boundary-value condition may describe the landing path, but a solver still needs variables, guesses, tolerances, and checks that the result obeys the dynamics.",
    },
    6: {
        "problem": "A computer cannot optimize over every point of a continuous path directly.",
        "move": "Use direct methods: shooting, collocation, and transcription turn a path problem into finite variables and constraints.",
        "run": "A robot arm path becomes joint states and torques on a grid; defect constraints stop the optimizer from inventing motion between grid points.",
    },
    7: {
        "problem": "Listing every future action sequence becomes impossible when every action creates a new state with later choices.",
        "move": "Use dynamic programming: store future cost at states and solve the problem by now-plus-future recursion.",
        "run": "A rover cell near sharp rocks gets a high future price because entering it damages later mobility, even if the next step is short.",
    },
    8: {
        "problem": "A full nonlinear solve is too much for small deviations near a planned motion.",
        "move": "Exploit linear dynamics and quadratic cost so local feedback can be computed from value curvature.",
        "run": "A hovering drone pushed two centimeters sideways can use a local feedback gain instead of replanning the whole flight.",
    },
    9: {
        "problem": "The next state may be a distribution, not a promise, when wind, gravel, or sensor noise changes the outcome.",
        "move": "Extend dynamic programming so future value is averaged over possible next states.",
        "run": "A rover crossing gravel prices a move by the chance of slipping left, slipping right, or moving as intended.",
    },
    10: {
        "problem": "A controller needs to know which states can still reach a target or avoid danger before optimizing a preferred path.",
        "move": "Use reachability to reason about sets of states under controls, disturbances, and targets.",
        "run": "A car near a wall may look safe by distance, but reachability asks whether any legal steering and braking sequence can still avoid collision.",
    },
    11: {
        "problem": "A plan made at the old state goes stale as soon as the world moves or the model is wrong.",
        "move": "Introduce MPC: solve a finite-horizon problem, apply the first action, observe, and solve again.",
        "run": "A car plans five seconds of steering but executes only a small slice before measuring traffic again.",
    },
    12: {
        "problem": "Repeated planning can make legal moves that leave the next optimization with no legal solution.",
        "move": "Study feasibility, recursive feasibility, and stability conditions for MPC.",
        "run": "A car entering a narrow gap may be collision-free now but have no braking option one second later; recursive feasibility rejects that handoff.",
    },
    13: {
        "problem": "Learning enters only after the course has named what written models and objectives can and cannot supply.",
        "move": "Bridge model-based control to data-driven control: what can be learned, from what signal, and with what new failure modes.",
        "run": "A robot may know its arm physics but not the right contact strategy for a drawer handle; demonstrations or reward can fill that missing piece.",
    },
    14: {
        "problem": "Imitation and reinforcement learning answer different missing-information problems.",
        "move": "Separate learning from demonstrations from learning through reward and interaction.",
        "run": "If an expert can show good grasps, imitation is natural; if success can only be scored after trial, reinforcement learning becomes the tool.",
    },
    15: {
        "problem": "Copying expert actions is not the same as building a controller that recovers after its own small mistakes.",
        "move": "Study imitation learning and behavioral cloning as supervised policy learning with distribution-shift risk.",
        "run": "A cloned driving policy trained near lane center may drift right, then face states the expert almost never visited.",
    },
    16: {
        "problem": "A reward signal can teach behavior without action labels, but delayed credit and unsafe exploration make the learning problem hard.",
        "move": "Introduce reinforcement learning through policy, reward, return, exploration, and objective learning.",
        "run": "A grasp that succeeds after a wrist correction must credit earlier actions, not only the final lift.",
    },
    17: {
        "problem": "The learner may not know the best action, but it can learn which states or state-action pairs lead to better future return.",
        "move": "Use value-based RL to learn future-return estimates from sampled transitions.",
        "run": "A game agent chooses a move by comparing the learned values of the board positions those moves create.",
    },
    18: {
        "problem": "Large continuous action policies may be easier to improve directly than through a table of values.",
        "move": "Use policy optimization to update the action rule from rollout returns.",
        "run": "A walking robot changes neural policy weights so steps that led to longer stable walking become more likely.",
    },
    19: {
        "problem": "Real trial-and-error is expensive when hardware can break or data collection is slow.",
        "move": "Use model-based RL to learn or use a predictive model, rehearse futures, and spend real trials carefully.",
        "run": "A warehouse robot can test shelf-collision futures inside a learned model before risking the real arm.",
    },
}


LECTURE_BLOCKS: list[dict[str, str]] = [
    {
        "title": "Lectures 1-2: Make Control Speak Plainly",
        "extract": "The learner should leave with the grammar of a control problem: state, action, dynamics, cost, horizon, constraints, feasibility, and local improvement.",
        "wrong_turn": "Do not treat these lectures as preliminaries to skip. If the setup is vague, every later solver and learner will solve the wrong problem.",
        "run": "A drone delivery story becomes real only when position, velocity, attitude, battery, wind, thrust, no-fly zones, and touchdown speed are named.",
    },
    {
        "title": "Lectures 3-6: Turn A Path Into Something A Computer Can Check",
        "extract": "The learner should see why a trajectory is the decision: calculus of variations, costates, Hamiltonians, shooting, transcription, and collocation all ask how a whole path obeys dynamics and cost.",
        "wrong_turn": "Do not read these as solver trivia. The danger is a path that looks smooth but hides endpoint error, torque spikes, missed collisions, or dynamics defects.",
        "run": "A robot arm going around a fixture needs states and torques along the path, not only a start pose and an end pose.",
    },
    {
        "title": "Lectures 7-10: Price The Future From The State",
        "extract": "The learner should understand value as stored future burden. Dynamic programming, stochastic outcomes, LQR, and reachability all depend on what the current state says about possible futures.",
        "wrong_turn": "Do not reduce Bellman reasoning to a formula. The real move is judging today's action by the state it creates.",
        "run": "A rover may avoid a short rocky path because wheel damage makes every later move worse.",
    },
    {
        "title": "Lectures 11-12: Replan Without Destroying Tomorrow",
        "extract": "The learner should distinguish a feasible short plan from a safe repeated controller. MPC, recursive feasibility, stability, and reachability ask what state is handed to the next solve.",
        "wrong_turn": "Do not trust the current optimization just because it found a legal two-second path.",
        "run": "A car can fit into a traffic gap now and still leave no legal braking future after the first acceleration.",
    },
    {
        "title": "Lectures 13-19: Learn Missing Structure Without Forgetting Control",
        "extract": "The learner should see learning as filling missing policy, reward, value, or model structure while keeping state distribution, reward loopholes, exploration risk, and model error visible.",
        "wrong_turn": "Do not treat data as a magic replacement for state, action, dynamics, cost, constraints, and safety boundaries.",
        "run": "A warehouse robot can clone drawer-opening demonstrations, but its own small error may put the handle pose outside the demonstrated states.",
    },
]


def main() -> int:
    manifest = load_json(RAW / "course-manifest.json", {"videos": []})
    transcript_index = load_json(
        RAW / "transcript-index.json",
        {"available_transcripts": 0, "videos": len(manifest["videos"]), "total_transcript_words": 0, "records": []},
    )
    concepts = load_json(ANALYSIS / "concepts/concept-atlas.json", [])
    evidence = load_json(ANALYSIS / "evidence/evidence-ledger.json", [])
    primitives = load_json(ANALYSIS / "throughlines/primitives.json", [])
    families = load_json(ANALYSIS / "throughlines/method-families.json", [])
    derivations = load_json(ANALYSIS / "teaching/derivations.json", [])
    worked_examples = load_json(ANALYSIS / "teaching/worked-examples.json", [])
    drills = load_json(ANALYSIS / "teaching/drills.json", [])
    weak_claim_repairs = load_json(ANALYSIS / "teaching/weak-claim-repairs.json", [])
    quality_audit = load_json(ANALYSIS / "audits/course-quality-audit.json", {})
    ev_by_id = evidence_by_id(evidence)
    concepts_by_id = {concept["id"]: concept for concept in concepts}
    missing_concept_runs = [concept["id"] for concept in concepts if concept["id"] not in CONCEPT_RUNS]
    if missing_concept_runs:
        raise SystemExit(f"missing first-principles concept runs: {', '.join(missing_concept_runs)}")
    by_video = {row["video_id"]: row for row in transcript_index.get("records", [])}
    concepts_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for concept in concepts:
        concepts_by_family[concept["family"]].append(concept)

    write(
        SITE / "assets/styles.css",
        """
:root {
  color-scheme: light;
  --ink: #17202a;
  --muted: #5d6875;
  --line: #d7e0e6;
  --paper: #ffffff;
  --wash: #f4f7f9;
  --accent: #0b6b64;
  --accent-2: #8b3f18;
  --soft: #e8f2f0;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--ink);
  background: var(--wash);
  line-height: 1.56;
}
.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  gap: 22px;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  border-bottom: 1px solid var(--line);
  background: rgba(255,255,255,.97);
}
.brand { color: var(--ink); font-weight: 760; text-decoration: none; white-space: nowrap; }
nav { display: flex; flex-wrap: wrap; gap: 10px 12px; }
nav a { color: var(--muted); text-decoration: none; font-size: 13px; }
nav a.active, nav a:hover { color: var(--accent); }
main { max-width: 1160px; margin: 0 auto; padding: 36px 24px 72px; }
.hero {
  display: grid;
  gap: 18px;
  padding: 30px 0 26px;
  border-bottom: 1px solid var(--line);
}
h1 { max-width: 940px; margin: 0; font-size: clamp(34px, 5vw, 62px); line-height: 1; letter-spacing: 0; }
h2 { margin-top: 38px; font-size: 27px; letter-spacing: 0; }
h3 { margin: 0 0 7px; font-size: 18px; letter-spacing: 0; }
p { max-width: 860px; }
a { color: var(--accent); }
.lede { max-width: 900px; color: var(--muted); font-size: 19px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin: 18px 0; }
.stat, .card, .evidence-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
  padding: 16px;
}
.stat strong { display: block; font-size: 30px; color: var(--accent); line-height: 1.1; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(265px, 1fr)); gap: 14px; }
.wide-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 14px; }
.stack { display: grid; gap: 14px; }
.lecture-list { display: grid; gap: 10px; }
.lecture-row {
  display: grid;
  grid-template-columns: 72px 1fr auto;
  gap: 14px;
  align-items: start;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
}
.tag { color: var(--accent-2); font-size: 13px; font-weight: 760; text-transform: uppercase; }
.pill { display: inline-block; margin: 0 6px 6px 0; padding: 3px 8px; border-radius: 999px; background: var(--soft); color: var(--accent); font-size: 13px; }
.muted { color: var(--muted); }
code { background: #eef3f4; padding: 2px 5px; border-radius: 4px; white-space: normal; }
blockquote {
  margin: 12px 0;
  padding: 12px 14px;
  border-left: 4px solid var(--accent);
  background: #f7faf9;
  color: #2c3a40;
}
.fp { border-top: 1px solid var(--line); padding: 26px 0 8px; }
.kick { font-size: 12px; color: var(--accent-2); font-weight: 760; text-transform: uppercase; letter-spacing: .08em; }
.essay p { max-width: 76ch; font-size: 16px; color: #24323a; margin: 10px 0; }
.explain-box {
  border: 1px solid var(--line);
  border-left: 3px solid var(--accent);
  border-radius: 8px;
  background: var(--paper);
  padding: 14px 16px;
  margin: 14px 0;
}
.explain-box p { margin: 7px 0; }
.math {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #eef5f4;
  margin: 14px 0;
}
.math summary {
  cursor: pointer;
  padding: 10px 13px;
  color: var(--accent);
  font-weight: 760;
}
.math div { border-top: 1px solid var(--line); padding: 4px 14px 12px; }
table { width: 100%; border-collapse: collapse; background: var(--paper); border: 1px solid var(--line); }
th, td { padding: 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
th { color: var(--muted); font-size: 13px; text-transform: uppercase; }
@media (max-width: 780px) {
  .topbar { align-items: flex-start; flex-direction: column; }
  .lecture-row { grid-template-columns: 1fr; }
  main { padding: 28px 18px 56px; }
}
""",
    )

    stats = f"""
<section class="stats">
  <div class="stat"><strong>{len(manifest['videos'])}</strong><span>playlist lectures</span></div>
  <div class="stat"><strong>{transcript_index.get('available_transcripts', 0)}</strong><span>local transcripts</span></div>
  <div class="stat"><strong>{transcript_index.get('total_transcript_words', 0):,}</strong><span>transcript words</span></div>
  <div class="stat"><strong>{len(concepts)}</strong><span>concept pages</span></div>
  <div class="stat"><strong>{len(evidence)}</strong><span>evidence records</span></div>
</section>
"""
    entry_cards = [
        ("Course Spine", "Read one coherent route from state and action through Bellman recursion, MPC, imitation learning, and model-based RL.", "course-spine.html"),
        ("Concept Atlas", "Study every required concept with problem, naive failure, math object, operation, example, boundary, and evidence.", "concepts.html"),
        ("Formula Reader", "Translate formulas into what is being controlled, what object carries the burden, and what operation is performed.", "formula-reader.html"),
        ("Drills", "Practice setup, method choice, Bellman recognition, MPC feasibility, reward diagnosis, and repair.", "drills.html"),
    ]
    entries = "".join(card(title, f"<p>{body}</p><p><a href=\"{href}\">Open</a></p>") for title, body, href in entry_cards)
    write(
        SITE / "index.html",
        page(
            "Overview",
            f"""
<section class="hero">
  <p class="tag">Transcript-backed first-principles course companion</p>
  <h1>{esc(manifest['title'])}</h1>
  <p class="lede">Optimal control is the discipline of choosing actions whose consequences unfold through time. Learning-based control extends that discipline when the model, cost, environment, or feedback signal cannot be fully written down in advance.</p>
  <div class="explain-box">
    <p>Start with a car entering traffic. The driver wants the next lane, but the controller cannot command "be in that lane." It can command steering, braking, and acceleration. Those commands move the state through tire forces, speed, heading, and the motion of nearby cars. A one-second action can create a future where braking is still possible, or a future where no legal move remains.</p>
    <p>That small scene is the whole course in miniature: name the state, name the action, write how the world moves, score the future, forbid unsafe states, choose a path, price delayed consequences, replan from new measurements, and learn missing structure only when data is the honest source.</p>
  </div>
  {stats}
</section>
<h2>Strongest Entry Points</h2>
<section class="grid">{entries}</section>
<h2>How To Read This Site</h2>
<div class="essay">
  <p>Start with a simple physical question: what can the system do now, and what future will that action create? Every page comes back to that question. State says what the controller must know. Action says what can actually be commanded. Dynamics say how the command changes the world. Cost says which future is preferred. Constraints say what future is illegal.</p>
  <p>The course then changes tools only when the pressure changes. Direct methods appear when the whole path must be chosen. Dynamic programming appears when future consequence can be stored by state. LQR appears when the world is close enough to a local model. MPC appears when a plan must be rebuilt from fresh measurements. Learning appears when the model, reward, or expert behavior cannot be fully written by hand.</p>
  <p>The evidence links keep the transcript layer honest. The teaching prose goes beyond the transcript, but each evidence record says what the lecture actually supports and where the site is synthesizing.</p>
</div>
<h2>The Route Through The Material</h2>
<section class="stack">
  <article class="card"><h3>1. Make The Problem Physical</h3><p>A controller starts with a moving thing: drone, car, rocket, robot arm, rover, policy, or learned model. The first job is to stop speaking in wishes and name the present-tense record, the command, the transition rule, the score, and the forbidden states.</p></article>
  <article class="card"><h3>2. Choose A Whole Future</h3><p>Trajectory optimization appears when one command is not enough. A landing rocket or robot arm needs a history of states and actions. The path has to obey dynamics at every step, not only look good at the endpoints.</p></article>
  <article class="card"><h3>3. Store Future Burden</h3><p>Dynamic programming appears when the same question repeats after every action. A rover that damages a wheel has changed the future problem. Value stores that future burden at the state so today's action can be judged honestly.</p></article>
  <article class="card"><h3>4. Replan Without Losing Safety</h3><p>MPC plans a short future, applies one action, and measures again. The hard test is the handoff: after that first action, does the next state still have a legal future? Reachability and recursive feasibility make that question explicit.</p></article>
  <article class="card"><h3>5. Learn Where Writing Runs Out</h3><p>Learning-based control enters when demonstrations, rewards, rollouts, or learned models carry structure the designer cannot write cleanly. The control questions remain: what states does the learner visit, what signal is being followed, and what failure can the signal hide?</p></article>
</section>
<h2>What This Site Is Not</h2>
<div class="essay">
  <p>It is not a transcript dump. The transcripts are the source floor, not the finished teaching. It is not a glossary. A definition is only acceptable when it is tied to a machine, an operation, and a failure. It is not a set of solver recommendations. Every method is introduced because some ordinary pressure made the previous framing break.</p>
  <p>The intended reading standard is simple: after a page, you should be able to retell the idea with a new car, drone, robot, rover, or learning setup without hiding behind the course vocabulary.</p>
</div>
<h2>First Read Path</h2>
<div class="essay">
  <p>Read <a href="course-spine.html">Course Spine</a> first if you want the whole argument in order. Then open <a href="concepts/state.html">State</a>, <a href="concepts/dynamics.html">Dynamics</a>, and <a href="concepts/objective-cost-function.html">Objective / Cost Function</a> to see how a story becomes a control problem. Next read <a href="concepts/bellman-recursion.html">Bellman Recursion</a> and <a href="concepts/model-predictive-control.html">Model Predictive Control</a> to see how future cost and repeated measurement change the decision. Finish with <a href="concepts/behavioral-cloning.html">Behavioral Cloning</a> and <a href="concepts/reward.html">Reward</a> to see why data does not remove the need for control reasoning.</p>
  <p>After that path, use the drills as a transfer test. If you can move the drone-delivery setup indoors, move the MPC traffic failure to a narrow drone window, and spot the reward loophole in a new robot task, the site is doing more than naming concepts.</p>
</div>
<h2>Current Build State</h2>
<p>The current build has full transcript coverage, a complete minimum concept atlas, timestamped evidence records with manual deepening, and expanded teaching artifacts for derivations, examples, drills, solutions, and weak-claim repairs.</p>
""",
            "overview",
        ),
    )

    lecture_rows = []
    for video in manifest["videos"]:
        rec = by_video.get(video["id"], {})
        deep = LECTURE_DEEPENING.get(video["lecture"])
        available = bool(rec.get("transcript_available"))
        label = "transcript captured" if available else "missing transcript"
        lecture_concepts = [c for c in concepts if c.get("lecture") == video["lecture"]]
        links = " ".join(f'<span class="pill">{concept_link(c)}</span>' for c in lecture_concepts[:6])
        if len(lecture_concepts) > 6:
            links += f' <span class="muted">+{len(lecture_concepts)-6} more</span>'
        if not deep:
            raise SystemExit(f"missing lecture deepening: lecture {video['lecture']}")
        lecture_rows.append(
            f"""<div class="lecture-row">
  <strong>Lecture {video['lecture']:02d}</strong>
  <div>
    <h3>{esc(video['title'])}</h3>
    <p class="muted">{esc(label)} · {rec.get('word_count', 0):,} words · <a href="https://www.youtube.com/watch?v={esc(video['id'])}">{esc(video['id'])}</a></p>
    <p><strong>The problem:</strong> {esc(deep['problem'])}</p>
    <p><strong>The move:</strong> {esc(deep['move'])}</p>
    <div class="explain-box"><p>{esc(deep['run'])}</p></div>
    <p>{links or '<span class="muted">No primary concept assigned yet.</span>'}</p>
  </div>
  <span class="tag">{'ready' if available else 'gap'}</span>
</div>"""
        )
    lecture_intro = """
<h1>Lectures</h1>
<p class="lede">Read the playlist as one route through a problem, not as nineteen isolated videos. Each lecture adds one pressure: name the moving system, choose a path, price the future, replan safely, or learn the missing structure from data.</p>
<div class="essay">
  <p>The lecture list below keeps transcript counts and source links, but the main job is different: it tells you what new control problem each lecture makes visible and what mathematical move the lecture adds.</p>
  <p>Use the blocks first, then the individual lecture rows. The blocks say what a learner should extract from a cluster of videos. The rows say what each video contributes and which concept pages carry the idea further.</p>
</div>
"""
    lecture_block_cards = "".join(
        card(
            item["title"],
            f"""<p><strong>Extract:</strong> {esc(item['extract'])}</p>
<p><strong>Wrong turn:</strong> {esc(item['wrong_turn'])}</p>
<div class="explain-box"><p>{esc(item['run'])}</p></div>""",
        )
        for item in LECTURE_BLOCKS
    )
    lectures_body = f"""{lecture_intro}
<h2>Lecture Blocks</h2>
<section class="stack">{lecture_block_cards}</section>
<h2>How To Use A Lecture Row</h2>
<div class="essay">
  <p>Read each row in four passes. First, read the problem sentence and ask what pressure entered the course at that point. Second, read the move sentence and identify the mathematical object or method family that answers that pressure. Third, read the concrete run and check whether you can retell it with another machine. Fourth, open the linked concepts and evidence record to separate transcript support from teaching synthesis.</p>
  <p>For example, Lecture 12 should not be remembered as "the MPC lecture after reachability." It should be remembered as the place where repeated planning is tested: today's feasible first command must leave tomorrow's optimization with a legal continuation. Lecture 15 should not be remembered as "imitation learning." It should be remembered as supervised policy learning under a closed-loop distribution problem.</p>
</div>
<h2>Lecture Route Cross-Checks</h2>
<div class="essay">
  <p>Check the route against three other pages. The concept atlas should turn each lecture move into a standalone explanation with ordinary pressure, concrete run, math, evidence, and boundary. The drills should force transfer: a lecture idea should survive a new drone, car, rover, warehouse, or reward setup. The evidence ledger should keep the source trail honest by saying what the transcript directly supports.</p>
  <p>A lecture row fails this cross-check if it only names a topic. "Lecture 7 covers dynamic programming" is not enough. The row must say that dynamic programming stores future cost at states so the controller can judge today's action by the state it creates. "Lecture 19 covers model-based RL" is not enough. The row must say that a learned model lets the robot rehearse futures while model error remains a failure mode.</p>
  <p>The first and last lectures should still feel connected. Lecture 1 asks what state, action, dynamics, cost, and constraints make a control problem. Lecture 19 returns to the same pieces after data enters: the model may be learned, but it still predicts next states for actions inside a control loop under real constraints, hardware limits, and safety checks.</p>
</div>
<h2>Lecture-By-Lecture Route</h2>
<section class="lecture-list">{''.join(lecture_rows)}</section>"""
    write(SITE / "lectures.html", page("Lectures", lectures_body, "lectures"))

    transcript_cards = []
    for video in manifest["videos"]:
        rec = by_video.get(video["id"], {})
        transcript_cards.append(
            card(
                f"Lecture {video['lecture']:02d}: {video['title']}",
                f"<p>{'transcript captured' if rec.get('transcript_available') else 'missing transcript'} · {rec.get('word_count', 0):,} words</p><p><code>{esc(rec.get('clean_text', 'not downloaded'))}</code></p>",
            )
        )
    transcript_intro = f"""
<h1>Transcript Index</h1>
<p class="lede">The transcript layer is the source floor. It keeps the course companion from becoming free-floating explanation.</p>
<div class="essay">
  <p>There are {transcript_index.get('available_transcripts', 0)} local transcripts for {transcript_index.get('videos', 0)} playlist videos, totaling {transcript_index.get('total_transcript_words', 0):,} words. Raw VTT captions stay separate from cleaned text so evidence can be traced back to timestamped source material.</p>
  <p>The site does not treat transcripts as finished teaching. A transcript window can support a claim that a lecture introduced reachability, Bellman recursion, MPC, imitation learning, or policy optimization. The explanation page then has to say what it is synthesizing beyond that window.</p>
  <p>Use this page when auditing source coverage: every lecture should show a captured transcript, a local clean-text path, and a word count large enough to support real review.</p>
  <p>If a lecture has no transcript, no concept page should pretend to quote it or build evidence from memory.</p>
</div>
<h2>How To Use A Transcript</h2>
<div class="essay">
  <p>Start with a narrow claim, not with a whole page. A transcript can prove that a lecture named model predictive control, reachable sets, quadratic cost, behavior cloning, or policy optimization. It can also support the local wording around that concept: for example, whether the lecture connects MPC with feasibility, or whether it frames behavior cloning as supervised learning from demonstrations.</p>
  <p>A transcript cannot by itself prove the whole first-principles synthesis. If a concept page says a car entering a narrow gap may leave no legal braking future, that sentence is teaching synthesis. The transcript may support the course topic of recursive feasibility; the page must still declare the added control interpretation through the evidence record.</p>
  <p>That split is deliberate. The transcript gives the floor; the course page builds the explanation. A reviewer should be able to inspect both layers without guessing which sentence came from source and which sentence came from synthesis.</p>
</div>
<h2>One Transcript Audit Run</h2>
<div class="essay">
  <p>Use Lecture 12 as a model. First open the clean transcript path and search for feasibility or stability. Then open the evidence record for recursive feasibility. The transcript window should show that the lecture discusses persistent feasibility in the MPC pipeline. The evidence record should say what that supports. The concept page can then teach the everyday test: after today's MPC action, does tomorrow's optimization problem still have a legal solution?</p>
  <p>Do the same for a learning concept. A behavior-cloning transcript window can support supervised learning from demonstrated behavior. The page can add the closed-loop warning: if the learned policy drifts into a state outside the demonstrations, action prediction accuracy on the original data is not enough.</p>
</div>
<h2>Transcript Red Flags</h2>
<div class="essay">
  <p>Be suspicious if an evidence record only repeats a keyword, if a concept page quotes no local transcript path, if the raw VTT cannot be traced to a timestamp, or if the explanation claims more certainty than the transcript window supports.</p>
  <p>Also be suspicious of transcript-shaped prose. Captions often contain false starts, repeated phrases, and lecture logistics. A good course page should not merely polish that sequence; it should rebuild the idea in everyday words, then point back to the transcript for source support.</p>
</div>
<h2>What To Record After Review</h2>
<div class="essay">
  <p>After checking a transcript claim, record three things. First, what the transcript directly supports: the lecture names a method, states an assumption, contrasts two families, or gives a formal object. Second, what the page adds: a car example, a drone failure, a reward loophole, or a plain-language operation. Third, whether the boundary is visible: the page should say where the lecture support ends and where synthesis begins.</p>
  <p>This record matters because rich writing can drift. The deeper the explanation gets, the more carefully the evidence trail has to separate source from teaching. The goal is not to make every sentence a quote; the goal is to make every strong teaching sentence auditable.</p>
  <p>A good note is specific: transcript supports quadratic cost terms; page adds the bowl picture and the warning that the approximation only holds near the planned motion. That note is reviewable months later by another course editor during source review work.</p>
</div>
"""
    write(SITE / "transcripts.html", page("Transcripts", f"{transcript_intro}<section class=\"grid\">{''.join(transcript_cards)}</section>", "transcripts"))

    family_sections = []
    for family in families:
        rows = concepts_by_family.get(family["id"].replace("-", " "), []) or [concepts_by_id[cid] for cid in family["concepts"] if cid in concepts_by_id]
        concept_cards = "".join(card(c["name"], f"<p>{esc(c['plain_language_definition'])}</p><p>{concept_link(c)}</p>") for c in rows)
        family_sections.append(f"<h2>{esc(family['name'])}</h2><p>{esc(family['problem'])}</p><section class=\"grid\">{concept_cards}</section>")
    concept_cards = "".join(
        card(c["name"], f"<p>{esc(c['plain_language_definition'])}</p><p><span class=\"tag\">{esc(c['family'])}</span></p><p>{concept_link(c)}</p>")
        for c in concepts
    )
    concept_family_cards = "".join(
        card(
            item["family"],
            f"""<p><strong>Pressure:</strong> {esc(item['pressure'])}</p>
<div class="explain-box"><p>{esc(item['ordinary_run'])}</p></div>
<p><strong>Failure test:</strong> {esc(item['failure_test'])}</p>""",
        )
        for item in CONCEPT_OVERVIEW_FAMILIES
    )
    concept_intro = """
<h1>Concept Atlas</h1>
<p class="lede">The concept atlas is the learner's map from ordinary control pressure to mathematical objects.</p>
<div class="essay">
  <p>Do not read these as vocabulary flashcards. Each concept page has to answer a practical question: what real system is being controlled, what simple approach breaks, what object carries the burden, what operation is performed, and what visible failure appears outside the assumptions.</p>
  <p>The cards below are only doors. The real work is inside each concept page: one concrete run, a math block one level deeper, transcript evidence, and a boundary test.</p>
  <p>A good review path samples one concept from each family before trusting the atlas as complete, balanced, and usable.</p>
</div>
<h2>How To Read A Concept</h2>
<div class="essay">
  <p>Read every concept through the same four-step test. First, name the ordinary pressure: a drone falling, a car merging, a robot arm near a shelf, a rover crossing gravel, or a policy learning from reward. Second, name the burden the concept carries. State carries what must be remembered. Dynamics carry how commands become motion. Value carries future cost. Constraints carry the lines the plan may not cross. Third, name the operation: update, propagate, minimize, price, constrain, replan, sample, or fit. Fourth, name the failure that appears when the assumptions are false.</p>
  <p>For example, a car changing lanes is not only a geometry problem. State must include nearby cars and velocity. Action is steering and acceleration, not the wish to be in the next lane. Dynamics say how quickly the car can move. Cost prices progress and comfort. Constraints protect lane boundaries and collision margins. MPC replans from new measurements, but recursive feasibility asks whether the first command leaves a safe future. Reachability asks which states are already too close to danger under worst-case nearby motion.</p>
  <p>The same reading works for learning. A warehouse robot may clone demonstrations because writing the contact strategy is hard, but cloning only trains on the states in the demonstrations. If the gripper nudges an object eight centimeters sideways, distribution shift has turned the policy into a controller for a state it may never have practiced. Reward can repair part of the behavior, but only if the written reward prices damage, force, smoothness, and safety.</p>
</div>
<h2>Family Pressure Map</h2>
<section class="stack">""" + concept_family_cards + """</section>
<h2>Atlas Doors</h2>
"""
    write(SITE / "concepts.html", page("Concepts", f"{concept_intro}<section class=\"grid\">{concept_cards}</section>", "concepts"))

    for concept in concepts:
        ev_cards = "".join(evidence_card(ev_by_id[eid], depth=1) for eid in concept.get("course_evidence_ids", []) if eid in ev_by_id)
        related = [c for c in concepts if c["family"] == concept["family"] and c["id"] != concept["id"]][:6]
        run = concept_run(concept)
        mathematical_object = sentence_body(concept["mathematical_object"]).lower()
        recognition = recognition_sentence(concept["recognition_test"])
        learning_control_check = ""
        if concept.get("family") == "learning-based control":
            learning_control_check = """
<section class="fp">
  <div class="kick">06 · data inside the loop</div>
  <h2>What the learner changes next</h2>
  <div class="essay">
    <p>Keep the learned piece inside the control loop. The data, reward, value estimate, policy, or learned model does not act in a separate world. It reads a state or observation, helps choose an action, and that action creates the next state the learner must handle.</p>
    <p>Ask three checks before trusting the result. What states did the data actually cover? What behavior does the reward or loss literally pay for? What happens after the learner's own first mistake changes the next input? These checks turn learning back into control instead of letting it become a vague promise that more data will fix the task.</p>
    <p>Use the warehouse drawer case as the common run. A demonstration may show the gripper centered on the handle. A cloned policy can miss by a few centimeters, rotate the handle, and then see a state absent from the demonstrations. A reward may push for quick opening while hiding excessive force. A learned model may rehearse contacts that are slightly wrong. The controller still has to ask what state it visits, what action it issues, and what failure the learned signal can hide.</p>
  </div>
</section>
"""
        body = f"""
<p><a href="../concepts.html">Back to concept atlas</a></p>
<h1>{esc(concept['name'])}</h1>
<p class="lede">{esc(concept['plain_language_definition'])}</p>
<section class="fp">
  <div class="kick">01 · the ordinary pressure</div>
  <h2>Why this idea has to exist</h2>
  <div class="essay">
    <p>{esc(concept['ordinary_problem'])}</p>
    <p>A common wrong first move is: {esc(concept['naive_approach'])} It fails when {esc(concept['why_naive_fails']).lower()}</p>
  </div>
</section>
<section class="fp">
  <div class="kick">02 · the object</div>
  <h2>What the math keeps track of</h2>
  <div class="essay">
    <p>The working object is {esc(mathematical_object)}. {esc(recognition)}.</p>
    <p>What the object does: {esc(concept['operation'])}</p>
  </div>
</section>
<section class="fp">
  <div class="kick">03 · read it with your hands</div>
  <h2>What to inspect first</h2>
  <div class="essay">
    <p>Before naming the method, point to {esc(mathematical_object)} in the setup. Ask what a person could measure, command, update, price, or forbid in one small run.</p>
    <p>Now apply one command or one update. {esc(concept['operation'])} After that operation, ask what changed in the next state, the path, the value, the constraint set, the policy, or the learned model. If nothing concrete changes, the explanation is still only a label.</p>
    <p>The world check is the example: {esc(concept['worked_example'])} Try the same question on another car, drone, rover, robot arm, or reward signal. The concept should still name what changes, what is paid for, and what can fail.</p>
  </div>
</section>
<section class="fp">
  <div class="kick">04 · one concrete run</div>
  <h2>Work it through before naming the formula</h2>
  <div class="explain-box"><p>{esc(run['run'])}</p></div>
  <details class="math"><summary>the actual math, one level deeper</summary><div><p>{esc(run['math'])}</p></div></details>
</section>
<section class="fp">
  <div class="kick">05 · boundary</div>
  <h2>Where the idea stops working</h2>
  <div class="essay">
    <p>{esc(concept['assumption_boundary'])}</p>
    <p>When that condition fails, look for this visible break: {esc(concept['failure_mode']).lower()}</p>
    <p><strong>Recognize it in a new problem:</strong> {esc(concept['recognition_test'])}</p>
  </div>
</section>{learning_control_check}
<h2>Transcript Evidence</h2>
<section class="stack">{ev_cards or '<p class="muted">No evidence record yet.</p>'}</section>
<h2>Nearby Concepts</h2>
<p>{' '.join(f'<span class="pill">{concept_link(item, depth=1)}</span>' for item in related)}</p>
"""
        write(SITE / "concepts" / f"{concept['id']}.html", page(concept["name"], body, "concepts", depth=1))

    spine_items = [
        (
            "01",
            "Name the moving situation",
            "A control problem begins when a choice today changes what choices are available tomorrow. Before formulas, name the moving thing, the information you know now, the command you can issue, the rule that turns that command into motion, the future you prefer, and the lines you cannot cross.",
            "A delivery drone is not controlled by saying 'arrive quickly.' Its state includes position, velocity, attitude, battery, payload, and wind estimate. Its action is thrust or a lower-level motion command. Its cost trades time, energy, landing error, and smoothness. Its constraints include no-fly zones, thrust limits, battery reserve, and safe touchdown.",
            "Once those pieces are named, the course can ask for more than one command. It can ask for a whole legal history of states and actions.",
            "If this move is skipped, every later method is floating. The solver may optimize a wish, the learner may copy labels without knowing state, and the safety check may protect the wrong boundary.",
        ),
        (
            "02",
            "Make the whole path the decision",
            "Static optimization chooses a point. Control chooses a path. Calculus of variations, costates, Hamiltonians, shooting, transcription, and collocation are different ways of saying that a legal answer is not one number; it is a history of states and actions that must fit the dynamics at every step.",
            "For a robot arm moving around a fixture, a shortest geometric curve can still require impossible torque. Direct methods put states and commands on a grid, enforce dynamics between neighboring grid points, and let the solver choose a path that the arm can physically trace.",
            "Once a path can be written as variables and constraints, the course asks how to judge paths whose early choices change later options.",
            "If this move is skipped, the learner may think control is a sequence of disconnected optimizations instead of a time-coupled path through physical states.",
        ),
        (
            "03",
            "Price the future from each state",
            "Dynamic programming appears when the future after the next state is another copy of the same problem. The value function is the price tag on being in a state with all future choices still open. Bellman recursion is the bookkeeping rule: compare actions by the cost now plus the future value of the state they create.",
            "A rover may choose a longer route around rough ground because the short route damages its wheels. The immediate distance is smaller, but the next state has worse future value because every later move is harder.",
            "Once future burden can be stored at a state, the course can exploit local structure: near a planned motion, that value can have a simpler shape.",
            "If this move is skipped, delayed consequences disappear. A controller will prefer the short route, early option exercise, or cheap first action even when it creates a worse future.",
        ),
        (
            "04",
            "Use local structure when the world is near the plan",
            "LQR works when the real motion is close enough to a nominal motion that the dynamics look linear and the cost looks like a bowl. It is not magic feedback. It is a local promise: small errors near the planned state can be pushed back with a fast linear correction.",
            "A hovering drone can use LQR for a small drift. After clipping a branch and tumbling, the same local model is no longer the right picture; the state has left the region where the approximation tells the truth.",
            "Once the boundary of local feedback is visible, the course can explain why a controller replans when the measured state moves away from the old prediction.",
            "If this move is skipped, LQR sounds like a universal controller rather than a local argument with a clear operating region.",
        ),
        (
            "05",
            "Replan without losing tomorrow",
            "MPC turns planning into feedback by repeatedly solving a short future problem and applying only the first command. Reachability and recursive feasibility ask the question MPC alone can miss: after this first command, will the next problem still have a legal escape?",
            "A car can choose a narrow traffic gap that is collision-free for two seconds and still be making a bad control choice if the state after one second has no safe braking or steering option left.",
            "Once replanning and safety are clear, learning can enter without pretending that data removes the need for state, action, dynamics, cost, and constraints.",
            "If this move is skipped, a learner may trust every feasible short-horizon solve and miss the handoff failure where tomorrow has no legal move.",
        ),
        (
            "06",
            "Learn only where written structure runs out",
            "Learning-based control is not a replacement for control thinking. It enters when the model is incomplete, the cost is hard to write, expert behavior is easier to show than specify, or trial feedback is the only teacher. The same questions remain: what is the state, what action is chosen, what future is being priced, and what failure does the learner create?",
            "Behavior cloning can teach a robot a drawer-pulling motion from demonstrations, but the learned policy may drift into a handle angle the expert never showed. RL can improve from reward, but if the reward pays only for speed, the robot may learn to damage the object quickly.",
            "This move returns to the beginning: even when the policy is learned, it still acts on state, issues actions, changes the next state, and creates the future it must handle.",
            "If this move is skipped, learning looks like a separate topic instead of another way to fill missing model, reward, value, or policy structure inside a control loop.",
        ),
    ]
    spine_html = "".join(
        f"""<section class="fp">
  <div class="kick">{num} · course move</div>
  <h2>{esc(title)}</h2>
  <div class="essay"><p>{esc(problem)}</p></div>
  <div class="explain-box"><p>{esc(example)}</p></div>
  <div class="essay">
    <p><strong>Handoff:</strong> {esc(handoff)}</p>
    <p><strong>If skipped:</strong> {esc(if_skipped)}</p>
  </div>
</section>"""
        for num, title, problem, example, handoff, if_skipped in spine_items
    )
    spine_intro = """
<h1>Course Spine</h1>
<p class="lede">The course is one question repeated at larger scale: what should this system do now, knowing that the action changes the future it will have to live in?</p>
<div class="essay">
  <p>Use one car merge to read the whole course. The car is in the right lane, a truck is ahead, a faster car is behind in the left lane, and the controller has two seconds to decide whether to accelerate, brake, or stay put. The state is not just lane position; it includes speed, heading, nearby cars, and enough prediction to know what the next command will change. The action is not "merge"; it is steering, throttle, and brake. Dynamics turn those commands into the next state. Cost prices progress, comfort, and delay. Constraints forbid collision, road departure, and acceleration beyond limits.</p>
  <p>Once that setup exists, the rest of the course is not a list of techniques. It is a sequence of repairs to harder versions of the same pressure. If the whole future path matters, trajectory optimization appears. If the next state changes every later choice, dynamic programming and value appear. If the car is close to a planned lane center, local feedback can help. If traffic moves, MPC replans. If nearby driver behavior, reward, or contact strategy cannot be written cleanly, learning enters. The spine below names each repair and the mistake it prevents.</p>
</div>
<h2>Same Car, Harder Questions</h2>
<div class="essay">
  <p>Read the spine as six passes over one traffic scene. At first the car only needs a truthful setup: speed, heading, nearby cars, steering, throttle, brake, road limits, comfort, and collision. Then the question grows from one command to a whole two-second history. The path must say where the car is after each small time step, what command was used, and whether tire force and acceleration stayed within the physical limits.</p>
  <p>Next the route asks why a cheap first move can be wrong. Accelerating into the gap may reduce delay now, but the next state can be expensive because the left-lane car is closing and the brake margin is gone. That is the value-function idea in ordinary clothes: the present action is judged by the future state it creates, not by the next meter alone.</p>
  <p>Then the car is near a planned lane center, so a local feedback law can correct small drift. This only works while the car remains near the region where the local model is honest. If the tires saturate or the road turns icy, the same local picture stops telling the truth. The course then replans from measurement: solve a short future, use the first command, measure again. But replanning has its own failure. The first command must leave the next solve with legal braking or steering, or the controller has only postponed the crash.</p>
  <p>Learning enters last because some parts of the scene may not be writable by hand. The other driver's behavior may come from data. The reward for comfort may be learned from examples. A policy may be copied from demonstrations. But the learned piece still sits inside the same loop. It receives state, chooses action, changes the next state, and can create states the data did not cover.</p>
</div>
"""
    write(SITE / "course-spine.html", page("Course Spine", f"{spine_intro}{spine_html}", "spine"))

    family_cards = []
    for family in families:
        deep = FAMILY_DEEPENING.get(family["id"], {})
        links = " ".join(
            f'<span class="pill">{concept_link(concepts_by_id[cid])}</span>'
            for cid in family["concepts"]
            if cid in concepts_by_id
        )
        body = f"""
<div class="essay">
  <p>{esc(deep.get('pressure', family['problem']))}</p>
  <p><strong>The move:</strong> {esc(deep.get('operation', family['problem']))}</p>
  <p><strong>Wrong shortcut:</strong> {esc(deep.get('wrong_turn', ''))}</p>
  <p><strong>Boundary test:</strong> {esc(deep.get('boundary', ''))}</p>
</div>
<div class="explain-box"><p>{esc(deep.get('worked', family['problem']))}</p></div>
<p>{links}</p>
"""
        family_cards.append(card(family["name"], body))
    write(
        SITE / "families.html",
        page(
            "Method Families",
            f"""<h1>Method Families</h1>
<p class="lede">A method family is a response to a specific pressure: the path is too large, the future is delayed, the local model is enough, the plan goes stale, or the missing structure must be learned from data.</p>
<div class="essay">
  <p>Read this page as a map of why the course changes tools. The switch from direct methods to dynamic programming is not a change of fashion; it is a change in what is hard. Sometimes the hard part is making a legal path. Sometimes it is pricing all futures from a state. Sometimes it is keeping a short-horizon plan from destroying tomorrow. Sometimes the missing piece has to be learned from demonstrations or reward.</p>
  <p>The same test applies to every family: what real mistake would happen if this family did not exist?</p>
  <p>A second test is transfer. If you can move the family from a car to a drone, or from a robot arm to a warehouse policy, without changing the family question, then the method has been understood as a response to pressure rather than as a name to memorize.</p>
</div>
<h2>Choosing A Family In One Run</h2>
<div class="essay">
  <p>Take a warehouse robot asked to pull a drawer. Problem setup comes first: state is gripper pose, handle pose, joint velocity, contact estimate, and shelf geometry; action is arm motion and gripper force; constraints forbid collision and damaging contact. Trajectory optimization enters if the drawer motion can be planned from a trusted model. Dynamic programming enters if each partial opening changes the value of later choices. Local structure enters near a known motion where small errors can be corrected cheaply. Replanning enters when contact slips and the measured state no longer matches the plan. Learning enters when the contact strategy is easier to demonstrate than write.</p>
  <p>The wrong family choice has a visible failure. Pure geometry misses torque and contact. Pure dynamic programming may be too large without a compact state. Pure local feedback fails after the handle slips. Pure MPC can replan into a state with no safe contact recovery. Pure imitation can drift outside demonstrated handle poses. The family choice is therefore a diagnosis of what is hard in the current problem, not a preference for a fashionable method.</p>
</div>
<section class="stack">{''.join(family_cards)}</section>""",
            "families",
        ),
    )

    primitive_cards = []
    for p in primitives:
        links = " ".join(
            f'<span class="pill">{concept_link(concepts_by_id[cid])}</span>'
            for cid in p["used_by"]
            if cid in concepts_by_id
        )
        test = PRIMITIVE_TESTS.get(p["id"], {})
        body = f"""
<p>{esc(PRIMITIVE_DEEPENING.get(p['id'], p['plain_language']))}</p>
<p><strong>Question it answers:</strong> {esc(test.get('question', ''))}</p>
<div class="explain-box"><p>{esc(test.get('run', ''))}</p></div>
<p><strong>Failure if wrong:</strong> {esc(test.get('failure', ''))}</p>
<p>{links}</p>
"""
        primitive_cards.append(card(p["name"], body))
    write(
        SITE / "primitives.html",
        page(
            "Primitives",
            f"""<h1>Mathematical Primitives</h1>
<p class="lede">These are the reusable pieces. They appear in different formulas, but each one answers an everyday control question.</p>
<div class="essay">
  <p>A primitive is not a small word to memorize. It is a role in the control story. State says what must be carried forward. Action says what can actually be commanded. Dynamics say how the command changes the world. Cost says which future is preferred. Constraint says what cannot be crossed. Value prices the future from here. Policy chooses the next action. Uncertainty admits that the next state may not be the one the planner hoped for.</p>
  <p>Once these pieces are named, the course becomes less mysterious. New methods mostly rearrange the same pieces: direct transcription lays them on a time grid, dynamic programming stores future cost in value, MPC rebuilds them every tick, and learning estimates one of them from data.</p>
  <p>If a plan fails, one primitive is usually lying, missing, or too loosely written. Debug the primitive before blaming the solver.</p>
  <p>Read each primitive as a small test. If you cannot answer the question it asks, run the concrete case, and name the failure when it is wrong, the word has not become usable yet.</p>
</div>
<h2>One Debug Sequence</h2>
<div class="essay">
  <p>Take the car merge from the course spine. The state must include lane position, speed, heading, nearby cars, and enough prediction to know whether the next command leaves room. The action is steering, throttle, and brake. Dynamics say how those commands move the car through tire grip and speed. Cost prices progress, comfort, and delay. Constraints forbid collision and road departure. Value prices the future after the first command. A policy chooses the command from the current state. Uncertainty admits that the rear car may accelerate or the tire grip may be lower than expected. Feasibility asks whether any legal future remains after the first move.</p>
  <p>Now change the object to a drone entering a narrow window. The same primitive sequence still works. State needs position, velocity, attitude, battery, wind, and localization uncertainty. Action is thrust or attitude target. Dynamics carry thrust through acceleration. Cost prices time, energy, and landing accuracy. Constraints enforce clearance and thrust limits. Value prices whether entering the window leaves enough room to stop. Policy chooses the next command. Uncertainty widens the future. Feasibility asks whether the drone can still avoid the frame after the first command.</p>
  <p>That transfer is the point of this page. A primitive is learned only when it survives a change of machine without losing its job in the control feedback loop.</p>
</div>
<section class="grid">{''.join(primitive_cards)}</section>""",
            "primitives",
        ),
    )

    formula_cards = []
    for item in FORMULA_EXPLAINERS:
        body = f"""
<p class="tag">{esc(item['shape'])}</p>
<div class="essay">
  <p>{esc(item['problem'])}</p>
  <p><strong>The object:</strong> {esc(item['object'])}</p>
  <p><strong>The operation:</strong> {esc(item['operation'])}</p>
  <p><strong>Input:</strong> {esc(item.get('input', ''))}</p>
  <p><strong>Output:</strong> {esc(item.get('output', ''))}</p>
  <p><strong>Wrong read:</strong> {esc(item.get('wrong_read', ''))}</p>
</div>
<div class="explain-box"><p>{esc(item['worked'])}</p></div>
<details class="math"><summary>where it fails</summary><div><p>{esc(item['failure'])}</p></div></details>
"""
        formula_cards.append(card(item["name"], body))
    write(
        SITE / "formula-reader.html",
        page(
            "Formula Reader",
            f"""<h1>Formula Reader</h1>
<p class="lede">A formula is a machine for doing one job. Read it by asking what it operates on, what gets changed, what future is being priced, and where the reading becomes false.</p>
<div class="essay">
  <p>The symbols in AA203 are easy to misread as decoration. They are not. Each formula is a small machine: put in a state, an action, a cost, a model, or a rollout; get out a next state, a price on the future, a constraint check, or a policy update.</p>
  <p>The reading order is always the same. First ask what real situation forced the formula to exist. Then identify the object it stores. Then name the operation it performs. Only after that should the symbols matter.</p>
</div>
<h2>One Reading Run</h2>
<div class="essay">
  <p>Use a landing rocket. Dynamics read height, velocity, fuel, and thrust, then return the next height, velocity, and fuel. The objective reads the whole candidate landing history and returns a score built from fuel use, touchdown speed, and final height error. Bellman recursion reads one thrust choice, the next state it creates, and the stored future value of that next state. The Hamiltonian reads immediate fuel cost and the costate price of changing velocity. MPC reads the measured rocket state, solves a short landing problem, applies the first thrust command, then measures again. A policy-gradient formula would read rollout returns from attempted landings and adjust a policy only if the credit signal is credible.</p>
  <p>This is how to reject a shallow formula reading. If the formula does not say what enters, what leaves, what future is priced, and where the reading fails, the symbols have not been explained yet.</p>
</div>
<h2>Three Checks For Any Formula</h2>
<div class="essay">
  <p>First, ask what would go wrong in the world if the formula did not exist. Dynamics exist because commands are not teleportation. Value exists because the next state carries later burden. MPC exists because yesterday's plan goes stale after measurement.</p>
  <p>Second, ask what object the formula carries. A transition rule carries motion, a cost carries preference, a value function carries future burden, a costate carries sensitivity, and a policy update carries evidence from rollouts.</p>
  <p>Third, ask what false reading would hurt a real system. A cost can omit damage. A value can price the wrong state. A local condition can miss the global path. A short MPC horizon can leave no future move. A policy update can reward noise.</p>
</div>
<section class="stack">{''.join(formula_cards)}</section>""",
            "formulas",
        ),
    )

    derivation_cards = []
    for item in derivations:
        linked = " ".join(f'<span class="pill">{concept_link(concepts_by_id[cid])}</span>' for cid in item.get("linked_concepts", []) if cid in concepts_by_id)
        body = f"""
<p><strong>Problem:</strong> {esc(item['problem'])}</p>
<p><strong>Starting point:</strong> {esc(item['starting_point'])}</p>
<ol>{''.join(f'<li>{esc(step)}</li>' for step in item['steps'])}</ol>
<p><strong>Formula shape:</strong> {esc(item['formula_shape'])}</p>
<p><strong>Why it works:</strong> {esc(item['why_it_works'])}</p>
<p><strong>First-principles intuition:</strong> {esc(item.get('intuition', ''))}</p>
<p><strong>Common wrong turn:</strong> {esc(item.get('common_wrong_turn', ''))}</p>
<p><strong>Failure test:</strong> {esc(item['failure_test'])}</p>
<p><strong>Transfer check:</strong> {esc(item.get('transfer_check', ''))}</p>
<p>{linked}</p>
"""
        derivation_cards.append(card(item["title"], body))
    derivation_intro = """
<h1>Derivation Walkthroughs</h1>
<p class="lede">Slow, problem-first derivations that explain why the formula shape exists before asking the learner to manipulate symbols.</p>
<div class="essay">
  <h2>How To Read A Derivation</h2>
  <p>A derivation is not a ritual for moving symbols from one line to the next. It is a way to make a physical accounting rule unavoidable. Start by naming the thing that must be preserved: a state transition, a whole path, a future value, a local sensitivity, a feasibility condition, or a policy update.</p>
  <p>Then ask what one legal step does. For Bellman recursion, one action creates one next state and carries one immediate cost. For the Hamiltonian, one control change has a cost now and a priced effect on later state. For direct transcription, one grid interval must connect neighboring state variables through dynamics. If the one-step move is vague, the derivation will only look formal.</p>
  <p>Finally, read the failure test before trusting the formula. A Bellman derivation fails if the state does not carry the future-relevant information. A local quadratic derivation fails if the system has left the small region where the bowl picture is truthful. An MPC argument fails if the first action leaves no legal next solve. The failure is not a footnote; it tells you what the derivation assumed.</p>
</div>
<h2>One Derivation Run</h2>
<div class="essay">
  <p>Use the rover route from the value pages. The rover can take a rocky shortcut or a longer smooth path. The derivation should not begin with the Bellman symbol. It begins with the fact that the first move changes wheel health, battery, and position. Those variables become the state because they decide what future moves remain possible.</p>
  <p>Now price each first move. The rocky move may have low distance cost, but it creates a next state with damaged wheels. The smooth move pays more now, but leaves a next state with cheaper later travel. The Bellman shape appears because every first move is judged by the same two-part ledger: what it costs now plus the future value stored at the state it creates.</p>
  <p>This is the standard for every card below. The formula shape should feel like the shortest honest way to keep the accounting straight, not like a symbol copied from the lecture.</p>
</div>
<h2>Derivation Cards</h2>
"""
    write(SITE / "derivations.html", page("Derivations", f"{derivation_intro}<section class=\"stack\">{''.join(derivation_cards)}</section>", "derivations"))

    example_cards = []
    for item in worked_examples:
        linked = " ".join(f'<span class="pill">{concept_link(concepts_by_id[cid])}</span>' for cid in item.get("linked_concepts", []) if cid in concepts_by_id)
        body = f"""
<p>{esc(item['setup'])}</p>
<table>
  <tr><th>State</th><td>{esc(item['state'])}</td></tr>
  <tr><th>Action</th><td>{esc(item['action'])}</td></tr>
  <tr><th>Cost</th><td>{esc(item['cost'])}</td></tr>
  <tr><th>Constraints</th><td>{esc(item['constraints'])}</td></tr>
  <tr><th>Method Route</th><td>{esc(item['method_route'])}</td></tr>
  <tr><th>Failure Signal</th><td>{esc(item['failure_signal'])}</td></tr>
  <tr><th>Decision Pressure</th><td>{esc(item.get('decision_pressure', ''))}</td></tr>
  <tr><th>Concrete Run</th><td>{esc(item.get('concrete_run', ''))}</td></tr>
  <tr><th>Method Boundary</th><td>{esc(item.get('method_boundary', ''))}</td></tr>
  <tr><th>Transfer Question</th><td>{esc(item.get('transfer_question', ''))}</td></tr>
</table>
<p>{linked}</p>
"""
        example_cards.append(card(item["title"], body))
    worked_intro = """
<h1>Worked Examples</h1>
<p class="lede">Concrete setups that force the learner to name state, action, cost, constraints, method route, and failure signal.</p>
<div class="essay">
  <h2>How To Read A Worked Example</h2>
  <p>Begin with the moving object, not the method name. A rocket, rover, robot arm, car, or drone has a present condition. It accepts only certain commands. The world changes after each command. Some endings are wanted, some are costly, and some are forbidden. The table is useful only after those pieces are visible.</p>
  <p>Then read the method route as a choice made under pressure. A shooting method is natural when the whole path can be described by a small set of starting guesses. A transcription method is natural when many points along the path must satisfy dynamics and limits. Dynamic programming is natural when the same state can be reached by different earlier choices and the future burden must be stored at that state.</p>
  <p>The failure signal is the part to linger on. If the example says a rocket violates touchdown speed, that is not a small detail; it means the cost or constraint failed to protect the real landing. If the rover chooses sharp rocks because distance is cheap, the future state was priced too weakly. If a learned policy leaves the demonstrated poses, the training data stopped covering the states the controller now visits.</p>
</div>
<h2>Example Cards</h2>
"""
    write(SITE / "worked-examples.html", page("Worked Examples", f"{worked_intro}<section class=\"stack\">{''.join(example_cards)}</section>", "derivations"))

    drill_cards = []
    solution_cards = []
    for item in drills:
        linked = " ".join(f'<span class="pill">{concept_link(concepts_by_id[cid])}</span>' for cid in item.get("linked_concepts", []) if cid in concepts_by_id)
        criteria = section_list([esc(criterion) for criterion in item.get("grading_criteria", [])])
        drill_cards.append(
            card(
                item["title"],
                f"<p>{esc(item['prompt'])}</p><p><strong>Setup hint:</strong> {esc(item.get('setup_hint', ''))}</p><p><strong>Wrong turn to avoid:</strong> {esc(item['wrong_turn'])}</p><p><strong>What a strong answer must include:</strong></p>{criteria}<p><strong>Transfer variant:</strong> {esc(item.get('transfer_variant', ''))}</p><p>{linked}</p>",
            )
        )
        solution_cards.append(
            card(
                f"{item['title']} Solution",
                f"<p><strong>Prompt:</strong> {esc(item['prompt'])}</p><p><strong>Setup hint:</strong> {esc(item.get('setup_hint', ''))}</p><p><strong>Wrong turn:</strong> {esc(item['wrong_turn'])}</p><p><strong>Strong answer:</strong> {esc(item['strong_answer'])}</p><p><strong>Solution walkthrough:</strong> {esc(item.get('solution_walkthrough', ''))}</p><p><strong>Transfer variant:</strong> {esc(item.get('transfer_variant', ''))}</p><p><strong>Grading criteria:</strong></p>{criteria}<p>{linked}</p>",
            )
        )
    drill_intro = """
<h1>Drills</h1>
<p class="lede">Practice prompts that train setup, method choice, future-cost recognition, feasibility diagnosis, reward repair, and approximation boundaries.</p>
<div class="essay">
  <h2>How To Work A Drill</h2>
  <p>Do not begin by hunting for the lecture label. First write the machine in plain words: what is measured now, what command can be sent, what changes next, what future is being paid for, and what line cannot be crossed. If that sentence cannot be written, the answer is still too thin.</p>
  <p>After the setup is physical, choose the method by the kind of pressure in the problem. A path-planning drill asks for many linked states and commands. A Bellman drill asks what future burden is stored at a state. An MPC drill asks whether the short plan leaves a state from which another legal plan can still be made. A learning drill asks which part of the control loop is missing and what new failure data creates.</p>
  <p>The transfer variant is the real test. If a drone delivery answer cannot survive an indoor drone window, it was memorized. If a traffic MPC answer cannot survive a narrower braking margin, it did not understand recursive feasibility. If a reward repair answer cannot survive a different robot task, it only patched the words.</p>
</div>
<h2>Drill Cards</h2>
"""
    solution_intro = """
<h1>Solutions</h1>
<p class="lede">Full solution notes that name the common wrong turn before giving the stronger control explanation.</p>
<div class="essay">
  <h2>What Counts As A Strong Solution</h2>
  <p>A strong solution should sound like an operator could check it. It names the state record, the command, the rule that moves the system, the cost paid along the way, the end condition, and the hard limits. It does not hide behind words such as performance or behavior. It says what changes and why.</p>
  <p>For path problems, the solution should say whether the unknown is a continuous curve, a sequence of knot points, or a feedback rule. For future-price problems, it should say what value is stored and how an action changes the next state before the next value is read. For repeated planning, it should test the state left behind for the next solve. For learning, it should say what the data covers and what happens when the closed loop visits states outside that cover.</p>
  <p>Use the wrong turn as a diagnostic. The wrong answer is not merely incomplete; it usually drops one physical piece. It drops the action limits, drops wind, drops future cost, drops terminal safety, drops distribution shift, or lets reward reward the wrong thing. The stronger answer repairs the missing piece and then checks the repair on the transfer variant.</p>
</div>
<h2>Solution Cards</h2>
"""
    write(SITE / "drills.html", page("Drills", f"{drill_intro}<section class=\"stack\">{''.join(drill_cards)}</section>", "drills"))
    write(SITE / "solutions.html", page("Solutions", f"{solution_intro}<section class=\"stack\">{''.join(solution_cards)}</section>", "drills"))

    base_misconceptions = [
        ("Optimal means globally best", "Many methods produce local candidates or model-conditioned optima, not universal guarantees."),
        ("MPC automatically stabilizes", "Repeated short-horizon solves need terminal structure or other conditions to protect long-run behavior."),
        ("Model-based RL is safe because it plans", "Planning through a learned model can exploit model errors."),
    ]
    misconception_cards = [card(a, f"<p>{esc(b)}</p>") for a, b in base_misconceptions]
    for item in weak_claim_repairs:
        misconception_cards.append(
            card(
                f"Repair: {item['weak']}",
                f"<p><strong>Diagnosis:</strong> {esc(item['diagnosis'])}</p><p><strong>Failure consequence:</strong> {esc(item.get('failure_consequence', ''))}</p><p><strong>Replacement rule:</strong> {esc(item.get('replacement_rule', ''))}</p><p><strong>Stronger version:</strong> {esc(item['strong'])}</p><p><strong>Transfer prompt:</strong> {esc(item.get('transfer_prompt', ''))}</p>",
            )
        )
    misconception_intro = """
<h1>Misconceptions And Weak-Claim Repairs</h1>
<p class="lede">Weak claims are places where the writing has lost the machine, the command, the future, or the boundary.</p>
<div class="essay">
  <h2>How To Repair A Weak Claim</h2>
  <p>First ask what the sentence hides. A claim about a better controller may hide the cost being reduced. A claim about safety may hide the reachable states being protected. A claim about learning may hide which part is learned: policy, reward, value, or model. The repair should name the hidden object in ordinary words before it names the course term.</p>
  <p>Second, ask what would go wrong in a real run. A car planner can look legal for two seconds and still leave no braking path. A model-based learner can plan through a learned model and choose a move that only works inside the model mistake. A reward can be maximized by the wrong action if the reward misses the task goal.</p>
  <p>Third, write the replacement sentence so it can be checked. It should say what state is measured, what action is allowed, what future is priced, what constraint is active, or what data cover is missing. If none of those pieces appears, the sentence is probably still decoration.</p>
  <p>A repair is done only when it changes what the reader would inspect. For MPC, the reader should inspect the state left for the next solve. For imitation learning, the reader should inspect states reached after small policy errors. For reward design, the reader should inspect the action that wins the score and ask whether it also completes the task.</p>
</div>
<h2>Repair Cards</h2>
"""
    write(SITE / "misconceptions.html", page("Misconceptions", f"{misconception_intro}<section class=\"grid\">{''.join(misconception_cards)}</section>", "review"))

    evidence_html = "".join(evidence_card(row) for row in evidence)
    evidence_intro = """
<h1>Evidence Ledger</h1>
<p class="lede">Evidence is the guardrail between lecture source and teaching synthesis.</p>
<div class="essay">
  <p>Each record points to a lecture, video id, timestamp URL, local transcript window, and raw VTT source. The timestamp is only the locator. The record must say what the transcript directly supports and what the site adds beyond the transcript.</p>
  <p>Use this page to check honesty. A keyword match is not evidence by itself. A good evidence record names the lecture argument: for example, that Lecture 11 discusses reachability through reachable sets, or that Lecture 7 frames dynamic programming as state-indexed recursion.</p>
  <p>If a concept page makes a stronger teaching claim, the evidence record should make the boundary visible rather than hiding that synthesis.</p>
</div>
<h2>How To Inspect One Evidence Record</h2>
<div class="essay">
  <p>Read the transcript window first and underline only what the lecture itself says. It may name a method, introduce a formal object, contrast two approaches, or state a condition. Do not let the nearby concept page smuggle in extra meaning yet.</p>
  <p>Then read <strong>Transcript supports</strong>. That sentence should be narrow. For recursive feasibility, a strong support sentence says the lecture discusses persistent feasibility across repeated MPC solves. It should not claim that the transcript proves the whole car-gap story. The car-gap story belongs to teaching synthesis.</p>
  <p>Now read <strong>Synthesis boundary</strong>. This is where the page is allowed to teach in plain words: a first MPC command can leave tomorrow's solve with no legal braking or steering continuation. The boundary is honest only if it tells the reader that this is an interpretation built from the lecture topic, not a quotation from the caption.</p>
  <p>Reject the record if the transcript window only contains a word match, if the support sentence is broader than the quoted window, if the synthesis boundary is blank, or if the concept page has no concrete operation tied to that evidence. Evidence should narrow the claim before the prose becomes rich.</p>
</div>
<h2>Two Good Evidence Shapes</h2>
<div class="essay">
  <p>For a math concept, the transcript should support the object or operation. A Bellman record can support state-indexed recursion, value, and immediate-plus-future accounting. The concept page can then teach the rover shortcut: the rocky path has low cost now but creates a damaged-wheel state with worse future value.</p>
  <p>For a learning concept, the transcript should support the learning setup: demonstrations, reward, policy update, exploration, or learned model. The concept page can then teach the closed-loop risk: a policy trained on centered drawer-handle demonstrations can move the handle off-center and create a state absent from the data.</p>
  <p>In both cases, evidence does not make the page less explanatory. It makes explanation accountable. The richer the page gets, the more visible the source boundary must be.</p>
  <p>A reviewer should leave a record with one clear verdict: source supports the term, source supports the operation, source supports only a nearby topic, or source is too weak for the page claim. That verdict keeps later editing from treating every timestamp as equal, complete, or equally trusted.</p>
</div>
"""
    write(SITE / "evidence.html", page("Evidence", f"{evidence_intro}<section class=\"stack\">{evidence_html}</section>", "evidence"))

    review = [
        (
            "First-principles depth",
            "Open a setup concept, a dynamic-programming concept, an MPC concept, and a learning concept. The page should begin with a real object such as a drone, car, rocket, rover, robot arm, shelf, or reward signal. If the first sentence that teaches the idea is only a formal definition, the page is not done.",
        ),
        (
            "Concrete operation",
            "For each page, identify what gets moved, updated, propagated, minimized, priced, constrained, sampled, or replanned. A good page lets the reader say what the mathematical object does before seeing symbols.",
        ),
        (
            "Evidence discipline",
            "Open evidence records and verify that local transcript windows support the concept vocabulary without pretending to prove the whole synthesis. The record should say what the transcript supports and what the site adds as explanation.",
        ),
        (
            "Practice transfer",
            "Run the drills and read the solutions. A strong solution names the wrong turn, explains why it fails in a control setting, and then repairs the setup or method choice.",
        ),
        (
            "Reference comparison",
            "Compare the main pages with the local reference explainers. They should feel like compact essays: problem, failure, object, operation, concrete run, math one level deeper, and boundary.",
        ),
        (
            "Audit path",
            "Use the completion audit, evidence ledger, and provenance page to verify transcript coverage, timestamp anchors, generated pages, local rebuild commands, and richness gates.",
        ),
    ]
    review_intro = """
<h1>Review Guide</h1>
<p class="lede">Use this page like a reviewer path through the site. The goal is not to confirm that files exist; it is to decide whether the writing teaches control from first principles.</p>
<div class="essay">
  <p>A quick review should sample one page from each part of the course: setup, trajectory optimization, dynamic programming, MPC, imitation learning, reinforcement learning, and model-based RL. On each page, ask whether a learner can retell the idea using a real system before using course vocabulary.</p>
  <p>The review should be strict about order. A page should start with a pressure in the world, then introduce the mathematical object because that object solves a problem. If the reader meets symbols before they know what the symbols are carrying, the page still needs work. If the page has a concrete story but never says where the story breaks, it also needs work.</p>
  <p>The reference standard is an explainer that a learner can retell without memorizing. After reading a page, the learner should be able to say: here is the machine, here is the command, here is what changes next, here is what future gets priced, here is the line the plan cannot cross, and here is the assumption that can fail.</p>
</div>
"""
    walkthrough_cards = "".join(
        card(
            item["title"],
            f"""<p><strong>Sample:</strong> {esc(item['sample'])}</p>
<p><strong>Pass condition:</strong> {esc(item['pass'])}</p>
<p><strong>Reject condition:</strong> {esc(item['reject'])}</p>""",
        )
        for item in REVIEW_WALKTHROUGH
    )
    review_body = f"""{review_intro}
<h2>Reviewer Route</h2>
<section class="stack">{walkthrough_cards}</section>
<h2>Rubric Checks</h2>
<section class="stack">{''.join(card(a,b) for a,b in review)}</section>"""
    write(SITE / "review-guide.html", page("Review Guide", review_body, "review"))

    quality = [
        (
            "First principles",
            "Start from a moving thing and an available command. A sentence is strong when it says what state changes, what action causes the change, what future consequence matters, and what assumption could make the conclusion false.",
        ),
        (
            "Plain language",
            "Use everyday words before course labels. Say the drone commands thrust before saying control input. Say the rover stores future travel cost before saying value function. Say the car must still have a legal braking future before saying recursive feasibility.",
        ),
        (
            "Concrete math",
            "Translate formal objects without flattening their job. A formula block should name the object, the operation, a small run with numbers or time steps, and the failure case.",
        ),
        (
            "Failure boundary",
            "State where the method breaks: model mismatch, infeasibility, coarse discretization, local approximation error, distribution shift, unsafe exploration, reward hacking, or learned-model exploitation.",
        ),
        (
            "Evidence honesty",
            "Separate what the transcript directly supports from synthesis beyond the transcript. A timestamp is not enough; the record must name the lecture argument being used.",
        ),
        (
            "No filler",
            "Remove sentences that only praise a method without naming its job. Replace praise with the state, action, future cost, constraint, approximation, or failure a practitioner would see.",
        ),
    ]
    quality_intro = """
<h1>Quality Rubric</h1>
<p class="lede">This rubric is an editorial test, not a decoration. It exists to keep the AA203 site close to the richer first-principles explainers: concrete, simple, low-jargon, and transferable.</p>
<div class="essay">
  <p>The standard is visible transfer. After reading a page, a learner should be able to recognize the same idea in a new car, drone, robot arm, rover, or learning setup. If the learner can only repeat a definition, the page is not rich enough yet.</p>
  <p>Good writing here is plain but not thin. It uses everyday words to carry real technical load: what is known, what is commanded, what moves, what is priced, what is forbidden, and what breaks.</p>
  <p>A page should also survive a cold read. A learner who has not watched the lecture should still be able to follow the ordinary pressure, then use the evidence link to see what the lecture actually supports. The prose can synthesize, but it should not float away from the transcript or hide the assumption boundary.</p>
  <p>The simplest editorial question is this: can the sentence be tested against a small physical run? If not, rewrite it until it names a state, action, transition, cost, constraint, value, policy, disturbance, or failure.</p>
</div>
"""
    quality_test_cards = "".join(
        card(
            item["title"],
            f"""<p><strong>Weak version:</strong> {esc(item['weak'])}</p>
<p><strong>Stronger version:</strong> {esc(item['strong'])}</p>
<p><strong>Pass test:</strong> {esc(item['test'])}</p>""",
        )
        for item in QUALITY_TESTS
    )
    quality_body = f"""{quality_intro}
<h2>Editorial Tests</h2>
<section class="stack">{quality_test_cards}</section>
<h2>Rubric Rules</h2>
<section class="grid">{''.join(card(a,b) for a,b in quality)}</section>"""
    write(SITE / "quality.html", page("Quality", quality_body, "review"))

    audit_rows = [
        ("Required pages", "present", f"{len(list(SITE.rglob('*.html')))} HTML files generated before this audit page is written"),
        ("Transcript coverage", "pending audit", f"{transcript_index.get('available_transcripts', 0)}/{transcript_index.get('videos', 0)} transcripts before audit reconciliation"),
        ("Concept atlas", "present", f"{len(concepts)} concepts generated"),
        ("Evidence ledger", "pending audit", f"{len(evidence)} evidence records before audit reconciliation"),
        ("Teaching artifacts", "present", f"{len(derivations)} derivations, {len(worked_examples)} examples, {len(drills)} drills, and {len(weak_claim_repairs)} repair cases generated from analysis/teaching"),
        ("Completion readiness", "pending audit", "quality audit not loaded yet"),
    ]
    if quality_audit:
        transcript_gaps = len(quality_audit.get("transcript_coverage", {}).get("gaps", []))
        manual_review = quality_audit.get("evidence", {}).get("manual_review_remaining", len(evidence))
        audit_rows[1] = (
            "Transcript coverage",
            "complete" if transcript_gaps == 0 else "partial",
            f"{transcript_index.get('available_transcripts', 0)}/{transcript_index.get('videos', 0)} transcripts; audit gaps: {transcript_gaps}",
        )
        audit_rows[3] = (
            "Evidence ledger",
            "first pass" if manual_review else "reviewed",
            f"{len(evidence)} evidence records; {manual_review} still need manual review",
        )
        audit_rows.append(
            (
                "Quality audit",
                "present",
                "analysis/audits/course-quality-audit.json and analysis/audits/course-quality-audit.md generated",
            )
        )
        blockers = quality_audit.get("completion_readiness", {}).get("remaining_blockers", [])
        audit_rows[5] = (
            "Completion readiness",
            "clear" if not blockers else "remaining",
            "No audit blockers found." if not blockers else "; ".join(blockers),
        )
    audit_table = "<table><tr><th>Requirement</th><th>Status</th><th>Evidence</th></tr>" + "".join(
        f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in audit_rows
    ) + "</table>"
    completion_requirement_rows = (
        "<table><tr><th>Requirement</th><th>Evidence Now</th><th>What This Does Not Prove</th></tr>"
        + "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in COMPLETION_REQUIREMENTS)
        + "</table>"
    )
    completion_intro = """
<h1>Completion Audit</h1>
<p class="lede">This page is the local proof that the package can be rebuilt and reviewed.</p>
<div class="essay">
  <p>The audit is deliberately mechanical about files, counts, transcript coverage, evidence review, and generated pages. That mechanical check does not replace editorial judgment, but it prevents a different failure: polished prose with missing transcripts, broken links, absent evidence, or stale generated output.</p>
  <p>Read this together with the quality rubric. The audit proves the source layer is present and the site is coherent; the rubric asks whether the writing reaches the first-principles standard.</p>
  <p>A reviewer should be able to rerun the build, reopen the same pages, and see the same transcript-backed route through the course, without hidden manual edits.</p>
  <p>The audit is also careful about what it does not claim. A green build proves that required structures and source trails are present. It does not prove that every page has the same depth as the strongest reference explainers. That final judgment still requires sampling the rendered pages as writing.</p>
</div>
"""
    completion_review = """
<h2>Requirement Evidence</h2>
<div class="essay">
  <p>Use this table before declaring completion. Each row names the current evidence and the boundary of that evidence. The boundary matters because this course goal is not just to generate files; it is to produce pages that teach control from first principles in plain language.</p>
</div>
"""
    completion_final_review = """
<h2>Two Proofs Required</h2>
<div class="essay">
  <p>Completion needs two different proofs. The mechanical proof is local and repeatable: transcripts exist, artifacts rebuild, links resolve, evidence anchors render, and validation passes. The editorial proof is slower: sampled pages must read like first-principles explanations, not polished summaries.</p>
  <p>Do the mechanical proof first. Run the build chain and confirm the numbers on this page: 19 transcripts, 38 concepts, 38 evidence records, 57 HTML pages, zero missing transcript references, and zero remaining manual evidence reviews. If those numbers drift, the site is not ready for editorial judgment because the source layer itself is unstable.</p>
  <p>Then do the editorial proof in the browser. Open a page and ask what physical pressure starts the explanation. A state page should make missing velocity visible. A Bellman page should show why the next state carries future burden. An MPC page should distinguish a legal short plan from a legal next solve. A learning page should show how data, reward, or a learned model changes the next state the controller must handle.</p>
  <p>The reject rule is strict: if a page can be summarized as "this lecture covers this topic," it fails. If it defines a term without a machine, command, future cost, constraint, or failure, it fails. If it links evidence but the evidence only supports a nearby keyword, it fails. If it sounds rich but cannot be traced back to a transcript window and synthesis boundary, it fails.</p>
  <p>For each sampled page, write one sentence in your own words without using the page title. If that sentence cannot name the machine, the command, the future consequence, and the bad outcome, the page has not yet taught the idea. The test is simple because the course promise is simple: a learner should be able to carry the idea to a new car, drone, rover, robot arm, or learned policy.</p>
</div>
"""
    sample_cards = "".join(card(title, f"<p>{esc(body)}</p>") for title, body in COMPLETION_SAMPLE_CHECKS)
    completion_close = """
<h2>Human Review Still Required</h2>
<div class="essay">
  <p>Before calling the course finished, open the course spine, concept atlas, formula reader, review guide, quality rubric, two setup concept pages, two dynamic-programming pages, two MPC or reachability pages, and two learning pages. Each page should survive the same test: ordinary pressure first, concrete operation next, math one level deeper, then the boundary where the idea stops working.</p>
  <p>If a sampled page only summarizes a lecture, defines a term, or praises a method without showing the state/action/future-cost machinery, the course is not done even if this audit table is green.</p>
  <p>The final reviewer should write down at least one pass example and one risk example. A pass example names the ordinary problem, the object, the operation, the concrete run, the math layer, the boundary, and the evidence record. A risk example names the exact page and the sentence or section that still feels thin. That note becomes the next editing target.</p>
</div>
"""
    sample_section = f"""
<h2>Sampled Page Checks</h2>
<section class="stack">{sample_cards}</section>
"""
    write(SITE / "completion-audit.html", page("Completion Audit", f"{completion_intro}{audit_table}{completion_review}{completion_requirement_rows}{completion_final_review}{sample_section}{completion_close}", "review"))

    provenance_cards = "".join(card(title, f"<p>{esc(body)}</p>") for title, body in PROVENANCE_CHECKS)
    write(
        SITE / "provenance.html",
        page(
            "Provenance",
            f"""
<h1>Provenance</h1>
<p class="lede">Provenance explains where the course material came from and how the site is rebuilt from local artifacts.</p>
<div class="essay">
  <p>The canonical source is <a href="{esc(manifest['playlist_url'])}">{esc(manifest['playlist_url'])}</a>. The repo keeps this source layer separate from synthesis so a reviewer can inspect the raw material before trusting the teaching pages.</p>
  <p>Playlist metadata is stored in <code>raw-material/youtube/playlist.json</code>. Caption files are stored under <code>raw-material/youtube/transcripts/raw-vtt/</code>, cleaned text under <code>raw-material/youtube/transcripts/clean/</code>, and availability in <code>raw-material/youtube/transcript-index.json</code>.</p>
  <p>Analysis artifacts live in <code>analysis/concepts/</code>, <code>analysis/evidence/</code>, <code>analysis/throughlines/</code>, and <code>analysis/teaching/</code>. The site under <code>site/</code> is generated output, not the only source of truth.</p>
  <p>The build path is: download or refresh transcripts, build the first-principles atlas and evidence ledger, build teaching artifacts, run the quality audit, render the static site, then validate links, evidence references, and richness gates.</p>
  <p>This separation matters because the writing can improve without losing the source trail. A richer explanation should still point back to the same transcript window and declare what is synthesis. That is the difference between a course companion and an unsupported essay or summary.</p>
</div>
<h2>Source-To-Page Trail</h2>
<section class="stack">{provenance_cards}</section>
<h2>Concrete Claim Check</h2>
<div class="essay">
  <p>Use reachability as the model check. The source layer stores the Lecture 11 caption window that names reachable sets, target sets, controls, disturbances, and safety objectives. The evidence record says that the transcript supports reachability as set-valued reasoning. The concept page then teaches the ordinary rule: from this car state, with this steering and braking limit, which future states can still avoid the wall or bad target?</p>
  <p>The teaching sentence is allowed to be clearer than the transcript, but it is not allowed to pretend the transcript proved every part of the synthesis. A reviewer should be able to move from rendered page to evidence id to local transcript window to raw VTT timestamp without guessing.</p>
  <p>Do the same check for one learning page. For behavioral cloning, the transcript supports supervised learning from demonstrated state-action behavior. The page adds the closed-loop warning: the learned policy can create states the expert did not label. That extra warning is allowed because the provenance trail names it as synthesis rather than transcript quotation.</p>
</div>
<h2>One Claim From Source To Teaching</h2>
<div class="essay">
  <p>Take the sentence: after today's MPC action, tomorrow's optimization problem must still have a legal solution. The raw caption layer should locate the lecture moment where MPC feasibility, terminal structure, or stability is discussed. The cleaned transcript makes that moment searchable. The evidence record states the narrow support: the lecture discusses recursive feasibility as a condition on repeated MPC solves.</p>
  <p>The concept page may then turn that into the traffic-gap example. A car can fit between two vehicles for the next two seconds and still be in a bad state if the first acceleration leaves no braking or steering move for the next solve. That car story is not copied from the transcript. It is the page's teaching move, and provenance is what keeps that move honest.</p>
  <p>A reviewer should be able to ask four questions. What exact transcript window supports the course term? What does the evidence record say the window supports? What did the concept page add to make the idea teachable? What boundary tells the reader where the claim stops? If any answer is missing, the page may still be readable, but it is not yet source-disciplined.</p>
</div>
<h2>What A Rebuild Protects</h2>
<div class="essay">
  <p>A rebuild protects against quiet drift. If a concept is deepened only in rendered HTML, the next generated site can erase it. If the concept data is changed without rebuilding, the visible page can lie about the current source. If the validator is not run, broken evidence anchors and missing transcript files can hide under polished writing.</p>
  <p>The durable route is simple: source material, analysis artifact, generator, rendered page, validator. Each step has a job. Source material keeps the course tied to the playlist. Analysis artifacts organize concepts and evidence. The generator turns those records into pages. The validator checks that required markers, links, word floors, evidence ids, and anti-filler rules still hold.</p>
  <p>This does not make the prose automatically rich. It makes the prose reviewable. The human review still has to compare pages with the reference explainers and ask whether the writing starts with ordinary pressure, names the object, runs the operation, opens the math one level deeper, and shows where the idea breaks.</p>
</div>
<h2>Do Not Trust The Page If</h2>
<div class="essay">
  <p>Do not trust a page if the source path is missing, the evidence record only repeats a keyword, the synthesis boundary is blank, the rendered page has no evidence anchor, the concept page skips the concrete run, or the validator was not run after generation.</p>
  <p>Do not trust a manual edit in <code>site/</code> by itself. The durable source is the generator and analysis artifacts. A real improvement changes the source layer, rebuilds the page, and passes validation.</p>
  <p>Run <code>python3 scripts/build_first_principles_atlas.py</code>, then <code>python3 scripts/build_teaching_artifacts.py</code>, then <code>python3 scripts/audit_course_quality.py</code>, then <code>python3 scripts/build_site.py</code>, then <code>python3 scripts/validate_all.py</code>.</p>
</div>
""",
            "provenance",
        ),
    )
    print(f"built {len(list(SITE.rglob('*.html')))} HTML pages in {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
