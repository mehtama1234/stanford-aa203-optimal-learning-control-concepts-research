# Per-concept de-templated prose for concept pages (Phase 1 rewrite).
# Source of truth (hand-reviewed). Do NOT regenerate from /tmp fragments. Lists of plain-text paragraphs.

CONCEPT_PROSE: dict[str, dict[str, list[str]]] = {
 "optimal-control-problem": {
  "pressure_close": [
   "A beginner might think: once I know my goal and the current situation, I can pick the single best action right now. But a rocket landing, a car merging, or a robot grasping an object will not settle in one move. Each action changes what is possible next, so you must trace a chain of decisions. Skipping that chain leads to plans that look clean on paper but leave the system in a corner where no safe recovery exists."
  ],
  "object": [
   "A controller needs to choose not one action but a whole sequence, and each choice ripples into the future because physics does not reset. You need a machine that holds together the current state, the rules that describe how actions change state, the cost of each possible future path, the limits that cannot be crossed, and how far ahead to look. That machine is an optimal control problem. It is the named binding of state, dynamics, cost, constraints, and horizon into one question: what sequence of commands keeps the system in the feasible region while making the future as good as possible?"
  ],
  "inspect": [
   "Take the rocket from the worked example: 80 meters high, falling at 18 m/s, 12 seconds of fuel, one second per step. Pick a candidate plan: burn 3 units of thrust now, burn 3 units the next step. Update the state by hand. After one second, velocity is -18 + 3 - 10 = -25 m/s (gravity subtracts 10 each step). Height falls by: starting height 80 minus the velocity change averaged over the step (roughly -21.5 m/s times 1 second is about 21.5 meters lost), so new height is about 58 meters. Fuel is 12 - 2*3 = 6 units. Now apply the second command: velocity becomes -25 + 3 - 10 = -32 m/s. Height drops by about 28.5 meters to 30 meters. Fuel is 6 - 2*3 = 0 units. The sequence satisfies the fuel constraint (never goes negative), but the descent rate at the end is 32 m/s into solid ground. The written problem forces you to see that fuel was not the only limit; the final speed also matters. A different sequence might trade fuel for a slower final impact, or you might realize the problem as written has no landing solution and needs more fuel or a longer horizon."
  ],
  "boundary": [
   "The setup is truthful only if the named pieces fit together: the dynamics must match the physics, the constraints must forbid what is actually impossible or unsafe, the cost must weight what really matters, and the horizon must reach far enough to expose the true tradeoffs. If the fuel model is wrong, the constraint lies, or the horizon ends before the critical event, the optimizer can produce a mathematically perfect answer to the wrong problem."
  ]
 },
 "state": {
  "pressure_close": [
   "A beginner might assume that the current position or height alone determines what will happen next. A car at y = 0.20 meters left of center is just a number, until you realize that two cars at the same position—one steady and one drifting sideways at 1.5 m/s—will respond very differently to the same steering command. Position alone did not carry enough memory."
  ],
  "object": [
   "A controller must remember the pieces of the present that determine what can happen in the next moment. You need more than a snapshot; you need the information that a dynamics model will use to predict the next state. For a car, that is position and velocity; without velocity, you cannot say whether the car will veer away or collide after a steering command. For a battery, it is charge and temperature; for a shower, it is water temperature and pipe temperature. These pieces together form the state. The state is the minimal record that carries forward all the information the dynamics and cost need to rank futures."
  ],
  "inspect": [
   "Take the car from the worked example at y = 0.20 meters with two scenarios. Car A has v_y = 0 m/s; Car B has v_y = -1.50 m/s. Apply steering u = +5 degrees for dt = 0.2 seconds. The update rule is y_next = y + dt*v_y. Car A predicts y_next = 0.20 + 0.2*0.00 = 0.20 meters. Car B predicts y_next = 0.20 + 0.2*(-1.50) = -0.10 meters. The same position and steering command produce different next positions because the sideways velocity was different. If you recorded only y = 0.20 as the state, you would falsely treat both cars as identical, and your predictions would be wrong for one of them."
  ],
  "boundary": [
   "The state must contain every variable that the dynamics use to compute the next step and every variable that the cost uses to score outcomes. If battery temperature does not appear in the state, the controller cannot check whether a climb violates the heat limit. If floor grip is missing from the state, two carts at the same position and speed will be treated as identical even though one is on wet floor and one is on dry floor. A hidden state variable turns different physical futures into a single predicted future."
  ]
 },
 "action-control-input": {
  "pressure_close": [
   "A beginner might confuse the goal with the command: if you want the drone at 12 meters high, just set the action to 12 meters. But the drone does not take height as an input; it takes rotor thrust commands. Thrust becomes acceleration, acceleration becomes velocity, velocity becomes height. A plan that skips this chain and commands position directly has asked the drone to do something no actuator can obey."
  ],
  "object": [
   "A controller must know what command it can actually send, not what outcome it wishes for. A robot joint receives torque, not joint angle; a motor receives voltage, not speed; a heater receives power setting, not room temperature. The action is the input the actuator can take. It is the lever you can push, subject to limits like saturation, rate of change, dead zones, and state-dependent safe ranges. The outcome you want appears only if you plan a sequence of actions through the physics that connects them."
  ],
  "inspect": [
   "Take the drone from the worked example at h = 10 meters, v = 0.2 m/s. The controller requests u = 0.48 (thrust as a fraction above hover) for dt = 0.1 seconds. The actuator law is a(u) = 10*u, so a = 4.8 m/s^2. Update velocity: v_next = 0.2 + 0.1*4.8 = 0.68 m/s. Update height: h_next = 10 + 0.1*0.68 = 10.068 meters. The drone rose 6.8 centimeters, not 2 meters. Now suppose a second motor limit says u_max = 0.5, and the request is u = 0.9. The actuator clips it to u = 0.5, so a = 5.0 and the result is still not 12 meters in one step. The action u is what reaches the motor. The outcome comes later, through the dynamics."
  ],
  "boundary": [
   "The action set must reflect real actuator limits and state-dependent safe ranges. If the action model omits saturation, rate limits, dead zones, or voltage-dependent response, the predictions will be wrong when those limits matter, and the controller will repeat the same requested command even when it produces different physical results."
  ]
 },
 "dynamics": {
  "pressure_close": [
   "A beginner might assume that steering the wheel immediately points the car, that raising the gas pedal instantly lifts the drone, or that turning the shower knob immediately produces hot water. In truth, momentum carries the car sideways before heading changes, motors accelerate gradually before height rises, and pipes hold cold water before hot water reaches the shower head. A plan based on instant responses will predict reachable futures that never arrive."
  ],
  "object": [
   "A controller must know the rule that turns a command into the next state. You cannot predict whether a lane change is safe, whether a climb is fast enough, or whether a shower is warming without understanding how thrust becomes acceleration, how steering becomes heading, or how the handle command becomes the water temperature you feel. That rule is the dynamics. It is the physical law that connects state now, action now, and state next."
  ],
  "inspect": [
   "Take the car from the worked example at speed 20 m/s, heading 0 degrees, with steering command u = 5 degrees and dt = 0.2 seconds. On dry asphalt, yaw_rate = 0.30 rad/s, so next heading = 0 + 0.2*0.30 = 0.06 rad. Apply the same command again: heading becomes 0.06 + 0.2*0.30 = 0.12 rad. Do it a third time: heading reaches 0.18 rad. Now redo it on ice with yaw_rate = 0.05 rad/s and lateral slip v_y = -1.0 m/s. After three commands, heading is only 0.03 rad, but the car has also drifted y = 3*0.2*(-1.0) = -0.6 meters sideways. The same steering inputs produced different heading change and added sideways motion in the icy case. The dynamics changed; the command stayed the same."
  ],
  "boundary": [
   "The dynamics must match the real physics at the time scale and speeds where the controller operates. A model that works for slow steering on dry asphalt will give wrong predictions for skidding on ice or for actuator delays. If the plan uses one dynamics model but the hardware follows a different one, the plan is correct for the wrong physics."
  ]
 },
 "objective-cost-function": {
  "pressure_close": [
   "A beginner might write down the goal in plain terms—arrive quickly, drive smoothly, stay warm—and assume the controller will simply pursue it. In reality, those plain terms hide competing claims: fast driving skips safety margin, smooth driving wastes time, warm heating burns energy. If you code only speed into the cost and ignore the others, the controller will drive at the margin of collision and the controller did exactly what was asked."
  ],
  "object": [
   "A controller must rank futures, and ranking requires a scoreboard that covers all the things that matter. You need a way to say whether a path that arrives fast but drives rough is better or worse than one that takes longer but feels smooth. That scoreboard is the cost function. It is the rule that sums up every consequence—time, energy, safety margin, wear, constraint violation—into a single number for each possible trajectory, so the optimizer can compare them. The written cost is only as honest as the tradeoffs it encodes."
  ],
  "inspect": [
   "Take the parking controller from the worked example. Path A reaches the spot in 8 seconds with steering effort 10 and wall clearance 6 centimeters. Path B takes 12 seconds with steering effort 3 and clearance 35 centimeters. Write a cost: stage_cost_k = time_step + 0.5*steering_effort + w_wall*clearance_penalty. If w_wall = 0, then Path A scores 8 + 0.5*10 + 0 = 13. Path B scores 12 + 0.5*3 + 0 = 13.5. Path A wins by 0.5 points. Now set w_wall = 1.0 and let clearance_penalty = 30 for A (risky) and 0 for B (safe). Path A scores 13 + 30 = 43. Path B scores 13.5 + 0 = 13.5. The ranking flips; the written choice changed because you rewrote the scoreboard. This is not magic; it is the price being made explicit."
  ],
  "boundary": [
   "The cost is only as strong as the terms in it. If collision damage does not appear in the cost and is not forbidden by a constraint, the controller is free to ignore it. If the real mission cares about paint scratches but the written cost is zero for paint damage, the optimizer will cheerfully scratch the car. The boundary is accountability: every outcome you want to avoid must have a term in the cost or a hard line in the constraints, or the controller cannot punish it."
  ]
 },
 "horizon": {
  "pressure_close": [
   "A beginner might optimize over the next second because it is easy to predict, forgetting that the real consequence arrives in three seconds. A delivery drone with a three-second lookahead might choose full speed, draining battery before it reaches the windstorm 5 seconds ahead. A car merging with horizon 0.1 seconds stays in the lane because it does not see the truck approaching. Cutting the horizon too short makes every locally cheap action look good right up until it fails."
  ],
  "object": [
   "A controller must decide how far ahead to reason, because consequences take time to unfold. A short lookahead avoids costly prediction, but it can miss the event that makes today's choice catastrophic. A long lookahead catches distant risks but depends on weak forecasts and can be too expensive. The horizon is the window into the future that the optimizer is asked to weight; it determines which costs and constraints can influence the first action chosen."
  ],
  "inspect": [
   "Take the delivery drone from the worked example: 60 meters from pad, 8 m/s speed, 18 percent battery. Each second of full speed uses 2 percent battery and covers 8 meters. Each second of slow speed uses 1 percent battery and covers 4 meters. There is a wind band from 25 to 40 meters requiring 14 percent battery reserve to cross safely. With a 3-second horizon, you see 24 meters (full speed) or 12 meters (slow). Full speed costs 6 percent battery, leaving 12 percent. The score inside 3 seconds favors full speed. But at 5 seconds, full speed reaches 40 meters and leaves 8 percent battery, which is below the 14 percent reserve. The 3-step plan is locally good but globally illegal. A 10-second horizon reaches the wind band and exposes that neither full nor slow speed alone works; the controller needs a mixed strategy. The horizon length decided which future constraints and costs could veto the first command."
  ],
  "boundary": [
   "The horizon should be long enough to reach the first consequence that can change the best first action. If the real danger appears after the horizon ends, the optimizer cannot price it, and the controller is blind to it. If the horizon is so long that it depends on guesses far into an unreliable future, those guesses can dominate the near-term choice. A useful horizon reaches the first event that matters and stops before the guesses overwhelm the model."
  ]
 },
 "constraints": {
  "pressure_close": [
   "A beginner might add a soft penalty to the cost if a solution breaks a rule, hoping the optimizer will avoid it naturally. A wall collision or a fuel overrun is not a tradeoff to be balanced; it is a line the plan cannot cross. Soft penalties can be bought away, and if an energy saving exceeds the penalty price, the optimizer will accept the collision."
  ],
  "object": [
   "A controller must obey hard lines that the cost cannot trade away. Constraints are the rules that a path must satisfy before the optimizer even compares costs. A robot must not collide, a tank must not overflow, a motor must not exceed its torque limit, a battery must not go below zero. These are feasibility rules, not preferences. A path that violates a constraint is not merely expensive; it is not a candidate at all. Constraints are the gatekeepers; cost is the referee among the paths that pass through the gate."
  ],
  "inspect": [
   "Take the arm from the worked example with a shelf 4 centimeters away. Candidate A reaches low energy cost but at t = 0.4 seconds its gripper is 3 centimeters from the shelf. Write the constraint: distance_to_shelf >= 0.04 meters. At 0.03 meters, this is violated. Candidate A is rejected before cost comparison. Candidate B costs more energy but keeps distance >= 0.05 meters everywhere, so it passes the gate. The cost ranking happens only after both pass the constraint check. Now suppose Candidate C has distance 0.02 meters but a soft penalty of 2 points per missing centimeter: written score = energy + 2*(4 - 2) = energy + 4. If energy cost difference between B and C is 5 points, C might look cheaper even though it violates the real clearance rule. A hard constraint refuses that trade."
  ],
  "boundary": [
   "A constraint is only as strong as the margin it carries. If the shelf can flex inward by 0.8 centimeters and the pose estimate is wrong by 0.7 centimeters, a nominal clearance of 5 centimeters gives worst-case clearance 5 - 0.8 - 0.7 = 3.5 centimeters, below the 4 centimeter rule. A repaired constraint should demand 5.5 centimeters to ensure the real system stays safe even under uncertainty. If the constraint ignores flex, estimation error, or another source of hazard, the optimizer can pass a written constraint while breaking the physical rule."
  ]
 },
 "feasibility": {
  "pressure_close": [
   "You see a car too close to a truck at high speed and think 'brake hard'—surely braking will work. But a wet road and tight spacing mean no braking sequence stops in time, the left lane has a box truck 0.5 meters away while you need 1.5 meters clearance, and the right side has a concrete barrier 0.8 meters out with the same clearance rule. In that instant, braking, swerving left, and swerving right all fail the constraints before they even start. The real question is whether any physical sequence of allowed commands can satisfy all the rules; if the answer is no, the state is not a planning problem—it is an emergency."
  ],
  "object": [
   "Before asking what plan is cheapest, a controller must first ask whether any admissible plan exists. This is the feasibility question: does at least one trajectory, starting from right now, obey the dynamics and respect all the constraints (speed limits, clearances, stop lines, acceleration bounds) without hitting any forbidden region? A single number like 'distance to goal' is not enough—the system must track all the constraints that could block an action. The set of all states from which at least one legal plan exists is the feasible set, and it is the ground on which optimization stands."
  ],
  "inspect": [
   "A car is 18 meters behind a stopped truck, traveling at 22 m/s with a wet-road braking limit of 6 m/s². Full braking requires v²/(2a) = 22²/(2*6) = 40.3 meters to stop. Since 40.3 > 18, straight braking hits the truck—that plan is outside the feasible set. Steering left opens onto a lane with a box truck 0.5 meters away, but the safety rule requires 1.5 meters clearance; steering left fails. Steering right faces a barrier 0.8 meters away, also violating the 1.5 meter rule. At this state, every obvious action family violates a constraint, so the feasible set for this state and this action model is empty. Now move the car back to 45 meters behind the truck. The same braking needs 40.3 meters, and 40.3 <= 45 is true, leaving 4.7 meters of stopping margin. Now the feasible set contains at least the full-brake plan. The switch from empty to non-empty happens because the starting position changed; feasibility is a state-dependent property."
  ],
  "boundary": [
   "Feasibility depends on whether the model includes the escape routes that actually exist. In the original 18-meter scenario, a shoulder lane 12 meters ahead is an emergency escape, but if the first model never includes 'steer into shoulder' as an action, that escape is invisible and the feasible set truly looks empty. A different model with shoulder-steering added will find a plan: brake hard 0.5 seconds (moving 10.25 meters and slowing to 19 m/s), then steer into the shoulder (using 2.0 meters of lateral clearance). The set is empty or non-empty depending on how rich the action model is, so a controller reporting 'infeasible' is not lying about the road—it is reporting the truth about its model."
  ]
 },
 "static-optimization": {
  "pressure_close": [
   "You choose a single charging power for the robot battery and assume that power is good for the entire hour regardless of how the temperature changes or whether the charge arrives early. At 4 kilowatts the battery reaches 46 degrees Celsius in 20 minutes, above the 45-degree limit, but you decided on the number before measuring temperature and cannot change it now. The battery heats past its safe point and loses capacity."
  ],
  "object": [
   "The charging station must pick one power setting now and cannot change it during the hour, because the physics of the charger itself is not being controlled—only the decision of which knob to turn. Given an interval of allowed choices, a limit on electrical current, and a penalty for being far from the desired 6 kilowatts, the engineer wants to find the one setting that makes the most sense. The choice is a single number from a bounded legal set, and once chosen, it drives a measurable outcome: battery charge gained and heat produced. Optimizing that one decision for one outcome is static optimization."
  ],
  "inspect": [
   "The battery robot has one hour to charge before a delivery route. The desired power is 6 kilowatts, the wall outlet allows at most 4 kilowatts, and the cost of missing the target is (z - 6)^2. At z=4 kilowatts, cost = (4 - 6)^2 = 4. At z=3 kilowatts, cost = (3 - 6)^2 = 9. At z=0, cost = 36. Among legal choices z in [0, 4], the minimum cost is at z=4. But add a thermal constraint: after 20 minutes at constant power z, the battery temperature is T(z) = 30 + 2*z degrees Celsius. At z=4, temperature T(4)=38 + 8 = 46 degrees, above the 45-degree limit. The temperature constraint T(z) <= 45 becomes g_thermal(z) = T(z) - 45 = z - 15 if we plug in the formula. At z=4, g_thermal(4) = 4 - 15 = -11 <= 0, actually feasible. But let's use a model that rises steeply: T(z)=30 + 4*z^2 / (5 - z). At z=4, T(4)=30 + 64/1 = 94, which is too high. Use T(z)=30+3*z. At z=4, T(4)=42. At z=3.8, T=41.4 and cost=(3.8-6)^2=4.84. The best legal choice is now z=3.8 kilowatts because it is feasible and better than z=3 (cost 9). This is a static problem because choosing z does not reveal a new state that changes what the next z should be. The choice is one number, the cost is final, and nothing rolls forward."
  ],
  "boundary": [
   "Static optimization is only valid if choosing one number now settles the whole problem and nothing the optimizer does changes what future decisions see. If the robot might arrive at the charger hot or cold and a smart controller would use a different power for each arrival temperature, the problem is no longer static—it is sequential control where the state (current temperature) changes what decision is best. The moment the choice of z today changes the temperature the robot has tomorrow, and that new temperature is fed back into the next optimization, the problem breaks static optimization and becomes a sequential decision chain."
  ]
 },
 "gradient-first-order-condition": {
  "pressure_close": [
   "A rover trying to steer correctly might think: the error is 3 degrees and I am at 0, so make the steering 3. But steering has its own cost—using too much steering is wasteful. The right balance is not obvious from just the target; you need to check whether moving slightly in any direction makes the combined cost go down."
  ],
  "object": [
   "When you change a knob by a tiny amount, some directions will lower your cost and others will raise it. The gradient is the direction-by-direction scorecard that says which small nudges help. If you are climbing a hill and every small step downward is blocked by a wall, the gradient might point downhill but be useless; if a small step in some direction lowers cost and nothing forbids that step, the gradient shows you where to move. A stationary point is where no legal tiny move is predicted to improve cost, and finding where the gradient points zero is often a powerful filter for candidates."
  ],
  "inspect": [
   "A rover chooses steering angle z to minimize J(z) = (z - 3)^2 + 0.2*z^2, the squared miss of a 3-degree target plus the cost of steering effort. At z = 0, the slope dJ/dz = 2*(0 - 3) + 0.4*0 = -6. A small move +0.1 is predicted to save 6*0.1 = 0.6 in cost. At z = 2.5, the slope is dJ/dz = 2*(2.5 - 3) + 0.4*2.5 = 0. Check numerically: J(2.4) = 1.512, J(2.5) = 1.5, J(2.6) = 1.512. The slope-zero point is locally best. Now add a hard stop z <= 2.0. At z = 2.0, the slope is -1.2, pointing toward more steering, but moving +0.1 is illegal. The best reachable point sits at the boundary with nonzero slope."
  ],
  "boundary": [
   "The gradient is a local test that works only near the point it is computed at, and only if the cost is smooth enough to differentiate. A stationary point is a candidate, not a proof: it could be a local maximum, a saddle, or just one of many stationary points. If the model omits a real cost such as hitting a rock, the gradient of the incomplete cost can point in a direction the complete cost would forbid."
  ]
 },
 "calculus-of-variations": {
  "pressure_close": [
   "A cheap first move is to optimize the robot's path one small step at a time, picking the best velocity or position at each instant without thinking about what comes next. But the robot's motion is a continuous curve: changing the speed at one second forces the robot to be at a different place at the second second, which then locks in all the later costs. You cannot improve a path by tweaking one point in isolation."
  ],
  "object": [
   "When you move a robot along a rail, the cost of that motion depends on the whole velocity curve from start to finish, not on any single number. A high-speed burst followed by a slow finish may reach the same endpoint as a steady cruise, but they cost different amounts of fuel. To know whether your velocity curve is good, you need a way to test whether every small shape change—every tiny bump up or down in speed—can still improve the cost. The object that captures this test is a functional, a mathematical rule that assigns one number (the total cost) to an entire curve. This is the calculus of variations."
  ],
  "inspect": [
   "Take the rail-cart example: the cart moves 1 meter in 2 seconds, and the fuel cost is the integral of speed squared over time. A constant 0.5 m/s costs integral from 0 to 2 of (0.5)^2 dt = 0.5. Now try a burst-then-slow plan: 0.8 m/s for the first second and 0.2 m/s for the second. It also travels 1 meter but costs 0.8^2 * 1 + 0.2^2 * 1 = 0.68. To test if the burst plan is good, imagine a small smooth bump: slow down by 0.1 m/s in a narrow window from t=0.4 to t=0.5, then speed up by 0.1 m/s from t=1.4 to t=1.5. The endpoint stays the same (both windows last 0.1 seconds, so the moves cancel). The cost change to first order is approximately 2 * 0.8 * (-0.1) * 0.1 + 2 * 0.2 * (+0.1) * 0.1 = -0.012. The bumped path costs about 0.668, lower than 0.68. This means the burst plan was not locally best; some small legal variation improved it."
  ],
  "boundary": [
   "The calculus-of-variations logic rests on smooth admissible perturbations: the path must vary continuously, and every small nudge must respect the physics and constraints. If the cart hits a hard speed limit at 0.75 m/s, the burst-to-0.8 plan is never even legal to test. If the cart's motor has a discrete on/off behavior or if the next state jumps discontinuously based on hidden switching logic, the variation argument breaks down because no smooth small bump can explore the consequence."
  ]
 },
 "costate-adjoint-variable": {
  "pressure_close": [
   "A first temptation is to care only about state errors at the moment they appear: penalize the cart being one meter low right now. But one meter low right now means the cart will be one meter low next second and the second after that, unless future actions fix it—and fixing takes effort. The same small error early in the trajectory can ripple into huge downstream cost, while the same error late in the trajectory leaves little time to propagate."
  ],
  "object": [
   "A state error at time 1 cascades forward and affects every later cost: it changes the height available at time 2, which changes what the system can do at time 3, and so on. One backward price per state variable is needed because coupled state variables have different roles in the future. Extra height might reduce a final-position penalty but increase a final-velocity penalty by different amounts, so height and velocity cannot share one price. The costate or adjoint variable is this propagated future sensitivity, evolved backward in time so that present control actions can be judged not just by their immediate cost but by the full downstream consequences they unlock."
  ],
  "inspect": [
   "Consider an elevator with two time steps. The final penalty is 100*(x_2 - 10)^2 for missing a target height of 10 meters. The derivative at x_2 = 9.9 is 200*(9.9 - 10) = -20. This is the backward price of height at the last instant: one extra meter reduces the final penalty by about 20. Now step backward. The dynamics are x_2 = x_1 + u_1, so x_1 changes x_2 one-to-one. The backward price at time 1 is therefore -20 as well. Now add two state variables: height h and velocity v with dynamics h_2 = h_1 + v_1 and v_2 = v_1 + a_1 where a is acceleration. At the final time with h_2 = 9.75 and v_2 = 0.5, the penalty derivatives are lambda_h = 100*(9.75 - 10) = -25 for height and lambda_v = 10*0.5 = 5 for velocity. Stepping backward, the jacobian of the step is [1,1; 0,1] for [h,v], so lambda_1 = transpose([1,0; 1,1]) * [-25,5] = [-25, -20]. Height has price -25 because it goes directly to the final height; velocity has price -20 because it also feeds into the next height."
  ],
  "boundary": [
   "The costate prices only the state within the model you wrote down. If the elevator motor also heats up and overheating is costly, but the heating cost is not in your written equations, the costate will not price it. The backward sensitivity tells you how valuable height is inside your stated objective and dynamics, not its full physical worth."
  ]
 },
 "hamiltonian-optimal-control": {
  "pressure_close": [
   "A cheap first move is to choose each control action by just minimizing what it costs right now—burn the least fuel at this instant, or apply the smallest force today. But a small cheap action now can leave the system in a bad place where future costs explode. A careful rocket burn costs more fuel today but puts you on a trajectory where you do not need costly later corrections."
  ],
  "object": [
   "Every action you take has two competing prices. There is what it costs immediately—the fuel burned or the power consumed at this moment. But there is also how it changes the state that future costs depend on; if you nudge the cart height upward, every later decision gets to work from a different starting point. To make a good local choice at each instant, you need one unified accounting sheet that sees both the immediate bill and the future value of the state change. This unified expression, the Hamiltonian, combines the running cost with the costate's valuation of where your action moves you."
  ],
  "inspect": [
   "Suppose a cart is at height x and can choose upward thrust u with immediate fuel cost 0.5*u^2. The costate p tells the future price of height: if p = -20, one extra meter of height reduces downstream penalty by about 20. The Hamiltonian is H = 0.5*u^2 + p*u. Try u = 0: H = 0. Try u = 10: H = 50 - 200 = -150. Try u = 20: H = 200 - 400 = -200. Try u = 30: H = 450 - 600 = -150. The best balance is u = 20 because it makes the Hamiltonian most negative. Now the future price changes to p = -4 (the cart is nearly on target). Then H(u) = 0.5*u^2 - 4*u: H(0)=0, H(4)=8-16=-8, H(12)=72-48=24. The optimal local choice moves to u = 4. The same motor and the same running cost; only the backward price changed."
  ],
  "boundary": [
   "The Hamiltonian gives a necessary condition for optimality, not a guarantee of success. The control that minimizes H at each instant is the best local choice assuming the costate is correct and no constraints are violated. But if a real cost is missing from the model—say, motor overheating above 8 units of thrust—then the Hamiltonian's ledger is incomplete and its recommendation can be wrong. The boundary is truthfulness of the model: if the running cost or dynamics are incomplete, the Hamiltonian balances a false accounting sheet."
  ]
 },
 "indirect-methods": {
  "pressure_close": [
   "A direct first move is to discretize the whole problem immediately—pick a grid of times, make position and control independent variables on the grid, and throw everything at a numerical optimizer. But the physics says the position at the next time must come from the current position and the chosen control; you have already thrown away that structure. The optimizer has to learn it back."
  ],
  "object": [
   "Searching directly over every possible path is enormous, and most candidate paths are obviously bad. But a genuinely optimal path is not arbitrary: calculus pins down exact conditions it must obey — the state moving forward under the dynamics, a price moving backward in time that measures how an early error changes all later cost, and a condition at each instant that the control is set where it can no longer be improved. Writing those conditions down and solving them together means you never wander through bad paths at all; the mathematics of optimality has already shrunk the field to a small boundary-value problem. Approaches that solve these optimality conditions first, instead of proposing whole paths and scoring them, are the indirect methods."
  ],
  "inspect": [
   "A cart must move from 0 to 1 meter in 2 seconds with cost integral of 0.5*u^2 dt. The indirect method writes the Hamiltonian H = 0.5*u^2 + p*u, applies stationarity dH/du = u + p = 0 to get u = -p, and applies the costate equation p_dot = 0 to find p is constant. Now the entire family of candidate paths depends on one unknown: the initial value p(0). If p(0) = -0.5, then u = 0.5 everywhere and x(2) = 1 exactly. This is solved by asking: which one constant value of p makes the endpoint land at 1? If the endpoint were free with penalty phi(x(2)) = 10*(x(2) - 1)^2, the boundary condition flips: p(2) = d_phi/dx = 20*(x(2) - 1). Since p is constant and x(2) = 2*p(0), the condition becomes p(0) = 20*(2*p(0) - 1), giving p(0) = -20/41 and x(2) = 40/41. The method did not search a grid; it solved the structure."
  ],
  "boundary": [
   "The indirect method produces a candidate answer until every boundary condition and constraint is satisfied. If an active inequality constraint like x(t) <= 0.8 is violated by the smooth necessary-condition solution, the smooth equations alone do not describe the full answer; you must add the active-constraint arc and resolve. The boundary is fragility to incomplete derivation: a forgotten constraint or sign error in the adjoint equation will cause the solver to hunt for a path that does not exist."
  ]
 },
 "direct-transcription": {
  "pressure_close": [
   "You describe the arm moving from 0 radians to 1.2 radians and let the optimizer choose the start and end points, assuming the motion in between will just interpolate smoothly. When the optimizer tries to jump from start to end in two 0.3-second leaps to save torque, the path looks fine in a plot. But at t=0.3 seconds the interpolated position is 0.6 radians with the chosen torque of 2 newton-meters, while the curve drawn between 0.0 and 1.2 actually passes through 0.85 radians halfway through. The arm is not at 0.6; it is at 0.85. The motor controller tries to track the drawing and the real state and the commanded state come apart."
  ],
  "object": [
   "The optimizer has to choose not just where the arm starts and ends, but exactly where it is at every moment in between, because the computer cannot check infinite points but the real arm passes through all of them. At times t=0.0, 0.2, 0.4, 0.6 seconds, the optimizer picks variables for position, velocity, and torque at each gridpoint. Between each pair of neighbors, the physics of the arm—the dynamics—says how the next state must follow from the current state and the applied force. The optimizer is only allowed to choose grid values that obey this rule: each next state must be reachable from the previous one by the actual arm model. Forcing the grid to respect the dynamics at every step is what direct transcription does."
  ],
  "inspect": [
   "Set up the arm problem: move from 0.0 rad to 1.2 rad in 0.6 seconds with a 5 newton-meter torque limit. The optimizer proposes joint angles q=[0.0, 0.4, 0.9, 1.2] at times t=[0.0, 0.2, 0.4, 0.6]. At t=0.2, with q_1=0.4, velocity v_1=1.0, and torque tau_1=2, the simple model predicts the next angle at t=0.4 should be q_2_pred = 0.4 + 0.2*(1.0 + 0.2*2/1.0)/2 ≈ 0.6 radians. The grid says q_2=0.9 radians. Defect = 0.9 - 0.6 = 0.3 radians. This is a lie: the curve shown does not match the physics claimed. To fix it, reduce q_2 from 0.9 to 0.6 so defect = 0.6 - 0.6 = 0. Now the path is truthful about what the arm can do in that interval while using only 2 newton-meters, which is legal. If the motion must also avoid a fixture that occupies angles 0.75 to 0.85, the original q_2=0.9 violates the obstacle constraint before the defect error. A repaired path that moves q_2 to 0.75 and applies tau_1=5 newton-meters (the motor limit) can reach that point while staying legal on both counts: zero defect and outside the fixture."
  ],
  "boundary": [
   "Direct transcription exposes the middle states as decision variables, so the optimizer must make them obey the dynamics at every step. But the grid only checks points; if a collision or torque spike happens between two gridpoints, the grid does not see it. At t=0.3 seconds, if a fixture occupies positions 0.75 to 0.85 radians and the grid checks only t=0.2 (where q=0.70) and t=0.4 (where q=0.75), the curve between them may swing through 0.80 radians and clip the fixture. A finer grid with a check at t=0.3 forces that hidden violation to become a named variable with its own constraint. The grid spacing itself is a claim about which part of the motion is fine enough to trust."
  ]
 },
 "shooting-methods": {
  "pressure_close": [
   "A first urge is to guess a whole trajectory shape—heights and speeds at each time—without checking whether the system can actually reach it from the starting state. A 1-meter displacement in one second looks reasonable until you realize the starting velocity was zero and there was no time to accelerate."
  ],
  "object": [
   "A hard control problem often fixes some facts at the start (where the system begins) and other facts at the end (where it must arrive, or what a final price must equal), while leaving the connecting piece — an initial costate, or the whole control sequence — unknown. Pinning down both ends at once is awkward. There is an easier move: guess the unknown starting values, simulate the dynamics forward from the known start (which automatically produces a physically real trajectory), and look at how far the simulated endpoint lands from the target. The size and sign of that endpoint miss tell you how to nudge the guess, exactly like aiming a cannon, watching where the shot falls, and correcting the angle. This guess-then-simulate-then-measure-then-adjust loop is the shooting method: it trades an awkward two-point problem for repeated, honest forward runs."
  ],
  "inspect": [
   "A cart starts at x = 0, v = 0 and must reach x = 10, v = 0 in 2 seconds using two acceleration commands. Try u_0 = 4 m/s^2 and u_1 = -1 m/s^2. Simulate forward: v_1 = 4, x_1 = 4, then v_2 = 3, x_2 = 7. The cart is short and moving. Try u_0 = 10 m/s^2 and u_1 = -10 m/s^2: v_1 = 10, x_1 = 10, v_2 = 0, x_2 = 10. Perfect endpoint, but both speed commands are extreme. If the motor limit is |u| <= 8, the u = 10 shot is illegal. If there is a cable obstacle between x = 5.0 and x = 5.5, the endpoint perfect shot flies past x = 10 in the first second, so it jumps over the cable and the final endpoint miss r = 0 does not prove the path avoided it. The optimizer can only discover such path violations by checking the simulated trajectory."
  ],
  "boundary": [
   "Shooting is natural when only controls or a few boundary values are unknown and forward simulation is stable and fast. When many state limits must be enforced along the path—a cable here, a speed limit there, a position bound elsewhere—endpoint error alone is blind to path violations. Multiple shooting splits the trajectory into pieces and adds join points to give the optimizer more handles mid-trajectory, but each piece must still be simulated from a reached state to be checked against path rules."
  ]
 },
 "collocation": {
  "pressure_close": [
   "You check whether the arm reaches the right place at the beginning and end of the interval, declare success, and move on. The arm starts with its gripper left of the fixture at x=0.02 meters and ends right of it at x=0.18 meters, so the path must clear the fixture. But the polynomial curve that connects them can bow inward partway through. At t=0.2 seconds (the midpoint of a 0.4-second move), the curve puts the gripper at x=0.10 meters while the fixture sits at x=0.08 to 0.12 meters. The path clips the fixture halfway through, and endpoint checking never found it."
  ],
  "object": [
   "The path is not just a set of samples; it is a curve in between, and the curve must obey the physics at more than just the endpoints. The optimizer represents the path as polynomials or grids and needs to force those polynomials to deliver speed and acceleration that match what the motors actually produce. At interior points along the curve, the slope that the drawn path implies must equal the speed that the dynamics demand. By checking this agreement at selected points inside each interval, the optimizer catches paths that look smooth in a drawing but are impossible for the arm to produce. The practice of enforcing these physics checks at interior sample points is collocation."
  ],
  "inspect": [
   "Use the arm example: swing a gripper from x=0.02 to x=0.18 meters over 0.4 seconds, avoiding a fixture at x=0.08 to 0.12 meters. Without interior checks, the optimizer can fit a cubic polynomial through the endpoints. At the midpoint t=0.2, suppose the polynomial curve has slope path_derivative_mid=0.9 m/s. The arm dynamics with torque u_mid=3 newton-meters predict f(x_mid, u_mid)=0.4 m/s. Defect_mid = 0.9 - 0.4 = 0.5 m/s. This is a collision between the curve's implied speed and the physics. Now add a clearance check at the midpoint. The polynomial puts the gripper at x_mid=0.10 meters, and clearance_mid = x_mid - 0.12 = -0.02 meters. Both checks fail. A repaired plan moves x_mid to 0.14 meters (outside the fixture on the far side), giving clearance_mid = 0.02 meters. It also changes the polynomial coefficients so the implied slope is now 0.6 m/s, matching the prediction from the chosen torque. Defect_mid = 0.6 - 0.6 = 0. Now both checks pass. Add a second collocation point at t=0.3 seconds. The curve there has x_3=0.16, clearance_3 = 0.04 meters, and the derivative matches the dynamics so defect_3=0. Both midpoint and later point agree the motion is possible and safe. If you now refine by asking what happens at t=0.25 seconds (between the two checked points), the cubic between x_mid and x_3 may bow inward to x_25=0.115 meters. Clearance_25 = -0.005 meters, so the coarse mesh missed a collision that the finer mesh finds. This is why adding collocation points is not decoration: it poses new questions that the drawn curve must answer."
  ],
  "boundary": [
   "Collocation checks the points and intervals the designer wrote down, not every unmodeled event or hidden behavior between checks. The polynomial segment between t=0.2 and t=0.4 is assumed to follow the dynamics smoothly if its start and end pass the checks, but real contact, friction changes, or backlash that happens in between are invisible if there is no sample point there. If the mesh is too coarse or skips a narrow fixture, the motion is feasible on the curve the optimizer drew and infeasible on the real arm. Refinement uncovers these gaps: each new collocation point is another physical claim the polynomial must satisfy."
  ]
 },
 "trajectory-optimization": {
  "pressure_close": [
   "You plan the robot's arm path by moving through the air in a straight line from start to finish, then hand that geometric path to the motor controller and hope it catches up. A straight line at constant speed needs zero torque at the start to accelerate and infinite torque at the end to stop. The motor limit of 40 newton-meters cannot deliver either one. The real arm either overshoots and crashes into the work surface, or it stops short and leaves the task incomplete."
  ],
  "object": [
   "The task is not just to end up at the right place, but to be at every right place at every right time while the motors stay within their limits and the robot does not bend a joint too far or too fast. No single position or single force command can promise this. The robot's arm over 2 seconds lives in a space of states: positions, velocities, and control forces all tied together by the physics of inertia and friction. At each time step from t=0 to t=2, the state must say what the joint is doing and what torque the motor is putting out right now. Choosing all those states and controls together so the joints start where they are, end where they need to be, and never exceed what the motors can do is what trajectory optimization does."
  ],
  "inspect": [
   "Set up the walking robot from the worked run below. At t=0.6 seconds, the original plan has torso lean 17 degrees and knee torque 46 newton-meters. The motor limit is 40 newton-meters, so measure the violation: residual = 46 - 40 = 6 newton-meters over. Now adjust the plan: lift the middle foot sample from 0.26 to 0.26 meters, which forces the body to stand more upright to keep the same foot height. Measure the new torso lean at t=0.6: it drops to 11 degrees. Measure the knee torque: it drops to 38 newton-meters. Residual = 38 - 40 = -2 newton-meters, so the motor is now under its limit with room to spare. The footpath looks less direct on a drawing, but the robot can actually execute this motion without the knee motor saturating. That is the whole point: the path was repaired not by erasing constraints but by using all the state variables together to find a different shape that satisfies every one."
  ],
  "boundary": [
   "The trajectory plan works only as well as the model inside the optimizer. If the model says the knee motor can produce up to 40 newton-meters but the real motor peaks at 35 newton-meters due to heating, a plan that satisfied the optimizer's model still saturates and fails on the hardware. If the model leaves out a collision check and only measures foot height without asking whether the body or elbow swings through a wall, the plan will be feasible on paper and illegal in the room. The solver also needs time steps close enough that nothing important happens between them. If the timestep is 1 second but the foot brushes the top of the box partway through at 0.6 seconds, and there is no measurement between 0 and 1 second, the optimizer never sees the collision."
  ]
 },
 "dynamic-programming": {
  "pressure_close": [
   "A naive planner lists every possible action sequence from start to goal: if a rover chooses left or right at each of 10 steps, that is 2^10=1024 paths to enumerate. But once the rover visits the same cell from a hundred different earlier routes, it re-solves the identical subproblem a hundred times instead of once, making the enumeration collapse."
  ],
  "object": [
   "A planner often stumbles on the same future subproblem from many different starting points. When a delivery cart reaches a junction, the best path from there to the warehouse does not depend on which earlier turn the cart took. Rather than re-solve that future a hundred times, the planner can compute it once, store the answer at the junction, and hand it to every earlier decision that passes through there. That stored answer—the best remaining cost from each state onward—is what dynamic programming calls the value function over states. It turns a blowup of path comparisons into reusable state-indexed bookkeeping."
  ],
  "inspect": [
   "Take the muddy-cell example from the worked run below. State M can move right for cost 1 to reach state A (whose future cost is already solved as V(A)=1), or down for cost 3 to reach state R (with V(R)=6). Dynamic programming writes V(M)=min(1+V(A), 3+V(R))=min(2,9)=2 and stores the right action. Now move to earlier state S. From S, moving east costs 2 to reach M, so that branch is 2+V(M)=2+2=4. Moving south costs 1 to reach R, so that is 1+V(R)=1+6=7. The update stores V(S)=4. The working part is not the direction labels; it is that both M and S borrowed V(M)=2 without re-examining what happens after M. Compute once, reuse everywhere."
  ],
  "boundary": [
   "The state label must contain all facts that change the future. If two cells are both labeled R but one has damaged wheels and the other has healthy wheels, one number V(R) cannot price their different futures. The method falsely reuses the subproblem and the stored policy points the wrong way. Equally, the state must be small enough that covering every possible combination of state values is computationally feasible; if the state space grows to millions of entries, even one pass through all states becomes impractical."
  ]
 },
 "value-function": {
  "pressure_close": [
   "A rover stands at a junction and must decide now: take the fast rocky shortcut or the slow smooth route. The shortcut costs 1 minute; the detour costs 4 minutes. Looking only at immediate cost, the shortcut wins. But the shortcut leads to a damaged-wheel state with a hard 18-minute climb ahead, while the detour leads to a healthy state with only 7 minutes remaining. Ignoring the downstream work, the rover will waste time."
  ],
  "object": [
   "When the rover chooses an action, it steps into a new state whose future is already determined. Before choosing, the rover needs a single number attached to each possible next state that captures what the full remaining cost will be if it acts well from there. That number must account for all the decisions and costs and paths that come after the next step—not the names of the paths, just their total expense if handled well. That compact summary stored at each state is the value function V; it tells a single digit that converts the future into an immediate number the current decision can borrow."
  ],
  "inspect": [
   "In the rover example, state R (damaged wheels) has value V(R)=18 because the best remaining trip from there to the charger spans 18 minutes. State H (healthy wheels) has V(H)=7. Now the rover at state S decides: rocky shortcut for 1 minute plus the inherited future V(R)=18 sums to 1+18=19. Smooth route for 4 minutes plus V(H)=7 sums to 4+7=11. The rover chooses smooth. Suppose a repair station opens and the damaged-wheel state's value drops to V_repaired(R)=9. The same rocky first move now scores 1+9=10, which beats smooth at 11, so the rover should pick rocky. The value stored at each state changed, not the cost of being in that state."
  ],
  "boundary": [
   "A value is a contract about a particular state under particular world facts. If the bridge after state R closes at noon, the best remaining cost changes from V(R)=9 to V(R)=25, but a table that keeps using 9 will send the rover into a trap. The number is meaningless if the state label hides a fact that changes the future—like whether the bridge is open, whether the wheels are damaged, or when the deadline is. A learner should always ask: what world was this value computed for, and is that world still true?"
  ]
 },
 "bellman-recursion": {
  "pressure_close": [
   "A warehouse robot at a junction sees that moving left costs 2 seconds while moving right costs 5 seconds. It picks left. Hours later, it returns to that same junction but now left leads into a dead-end blocked by workers, while right opens a shortcut. The robot should reverse direction, but if it only ever compared the immediate step costs, it has no way to learn that left is now worse overall—only that it is cheaper right now."
  ],
  "object": [
   "A controller deciding right now needs a local rule that accounts for what happens after the chosen action without spelling out every future step. The rule must split the problem into two pieces: the cost of the action it is about to take, and a pre-computed summary of the cost of everything that comes after. When the controller adds immediate cost to that stored future price and picks the best action, it makes a decision that reckons with the whole path even though it only looks one step ahead. That accounting identity—comparing immediate cost plus the stored value of the next state—is the Bellman recursion."
  ],
  "inspect": [
   "In the worked run below, a robot at junction J can take aisle A (costing 2 seconds, leading to state C with stored future V(C)=9) or aisle B (costing 5 seconds, leading to state L with stored future V(L)=3). The Bellman step for aisle A is immediate cost plus next value: 2+9=11. For aisle B: 5+3=8. The junction stores V(J)=8 and remembers that B was the winner. If later the clear lane L becomes blocked and its future cost jumps to V(L)=14, the same Bellman step changes B to 5+14=19, and the junction now stores V(J)=11 and chooses A instead. The equation did not move; only the input future prices changed."
  ],
  "boundary": [
   "The recursion assumes the stored next-state value V is correct and complete. If the state omits a hidden fact that changes the future—like a battery warning or a locked door—then the Bellman step reuses a future price that does not match the real future. Equally, the recursion assumes the one-step transition is accurate; if the model says moving right reaches state A but mud sends the robot to state B, the stored value no longer applies."
  ]
 },
 "stochastic-dynamic-programming": {
  "pressure_close": [
   "A delivery rover can cross gravel or detour around it. Crossing is faster if it succeeds, but there is a 10 percent chance a disturbance will cause a serious slip that damages the axle. A planner that ignores the slip—planning only for the most likely outcome—will recommend crossing and send the rover into expensive failure 10 times per 100 trips. The future is not a single promise; rare bad outcomes still happen."
  ],
  "object": [
   "A controller does not know for certain what will happen after an action because noise, slips, or environment changes intervene. The controller must price the action as the immediate cost it pays plus a weighted average of all the possible futures it might face, with each future weighted by how likely it is. That average—the expectation over all possible next states—becomes the stored value at the state after the action is taken. Dynamic programming then compares actions by their immediate cost plus that averaged future value, so rare but costly outcomes are properly accounted for in the decision. That is stochastic dynamic programming: the same backward reasoning as the deterministic method, but with the next-state value replaced by an expectation."
  ],
  "inspect": [
   "In the worked run below, a gravel crossing costs 1 minute now. With probability 0.6 it succeeds (future value 5), with probability 0.3 it slips left (future value 12), and with probability 0.1 it slips right (future value 20). The expected future value is 0.6*5 + 0.3*12 + 0.1*20 = 8.6 minutes, so the total gravel score is 1 + 8.6 = 9.6. Detour costs 4 minutes now and reaches a state with value 4 with probability 0.9 or a slow gate with value 9 with probability 0.1, totaling 4 + 0.9*4 + 0.1*9 = 8.5. Detour wins despite its larger immediate cost. Now suppose mud swells the slip-right damage from value 20 to value 200. The same gravel score becomes 1 + 0.6*5 + 0.3*12 + 0.1*200 = 27.6, and detour now wins decisively. The Bellman equation did not change; the transition model probabilities or the impact of rare slips changed."
  ],
  "boundary": [
   "The expected-value equation is only as good as the probability model it was given. If the table hides the weather—combining dry gravel at P(slip-right)=0.02 with wet gravel at P(slip-right)=0.16 into a mixed table at P(slip-right)=0.07—the stored value prices neither dry nor wet correctly, and the controller will be wrong on whichever condition actually occurs. The method also assumes an expectation is the right way to weigh outcomes; if a rare slip causes axle failure, safety rules such as P(failure) < 1 percent may override the average cost, and the model must encode that constraint explicitly."
  ]
 },
 "lqr": {
  "pressure_close": [
   "A delivery cart is 20 centimeters left of the center line. A simple proportional steerer—push back the full measured error—seems wise: u = -0.20 (20 centimeters to the right). But steering has a price. If harsh steering wears the cart or burns battery, pushing back all the error at once costs more in steering wear than the cart saves by reaching the line one step sooner. A cheap answer would accept a bigger sideways offset now to avoid the steering cost, but by how much? Guessing wastes effort."
  ],
  "object": [
   "A controller near a nominal operating point must trade between two costs that pull against each other: the discomfort of being off the nominal trajectory and the cost of the steering effort needed to correct it. The controller needs a feedback rule that sees the current deviation and automatically computes the right correction—neither too harsh nor too weak—given those two cost rates. That rule must be fast to compute because it runs in every control cycle. In a linear dynamical system with quadratic costs, the optimal feedback rule is a linear gain applied to the state error, and finding that gain is a structured recursive problem. That is what LQR—linear-quadratic regulator—provides: a clear method to compute the feedback gain given the local linear dynamics and the relative weights on state error and control effort."
  ],
  "inspect": [
   "In the worked run below, the cart has lateral error e = 0.20 and local dynamics e_next = e + u. One-step cost is 5*e^2 (discomfort of being off-center) plus u^2 (steering effort) plus a future penalty 20*e_next^2. Substituting the dynamics, minimize 5*(0.20)^2 + u^2 + 20*(0.20 + u)^2. Taking the derivative: 2u + 40*(0.20 + u) = 0, so u = -0.190. For a general error e, the same derivative gives 2u + 40*(e + u) = 0, yielding u = -(20/21)*e, a feedback gain K = 20/21. If steering is made four times more expensive (cost 4*u^2 instead of u^2), the derivative is 8u + 40*(e + u) = 0, so u = -(5/6)*e and K = 5/6. Same state, different weights, different gain."
  ],
  "boundary": [
   "LQR assumes the linear dynamics and quadratic costs hold over the range of deviations the controller will see. If the cart is 70 centimeters off-center, the gain calls for u = -(20/21)*0.70 = -0.667 meters of steering, but the actuator clips to |u| <= 0.10. The controller cannot deliver the requested correction, the cart remains 0.60 meters off, and it has left the regime where a small linear model is valid. Equally, the method cannot handle hard state constraints—like keeping the cart within the lane—or model errors such as tire slip or wind disturbances that break the written linear dynamics. LQR is a local method; when the state deviations grow large or actuator limits bind, the linear feedback law stops being the right full explanation."
  ]
 },
 "local-quadratic-approximation": {
  "pressure_close": [
   "You fit a simple bowl-shaped curve to how the cost changes when you nudge the control, compute the bottom of that bowl mathematically, and jump all the way there in one step. The bowl fit uses data from small nudges around the current point—you tested -0.02, 0, and +0.02 meters—but the computed best point says jump 0.12 meters. That is five times farther than the data that fit the bowl. Outside that neighborhood, the real cost landscape is not a bowl; it may have a ridge, a cliff, or a different slope entirely. You jump to the computed optimum and land on a part of the landscape the bowl never described."
  ],
  "object": [
   "When the gripper is 6 centimeters too far left, you want to nudge it right, but before trying big moves you need to understand which direction helps and how quickly the improvement gets smaller as you move farther. By testing small adjustments—minus, zero, plus—you can see if moving right reduces cost and if the curve is bending upward (improvement shrinks). A quadratic shape (a parabola or bowl) fits this local data: it has a bottom, a steepness at the current point, and a bending rate. But that fit is only honest for nudges similar in size to the data used to fit it. Using the fitted bowl to predict what happens far away from the measured neighborhood is a lie. What you need is a repeated rhythm: fit the bowl in a small neighborhood, take one cautious step within that neighborhood, measure the cost there, refit the bowl around the new point, and repeat. Each step stays close enough that the bowl describes reality. This stepped approach using local quadratic approximations is how iterative controllers refine a plan."
  ],
  "inspect": [
   "The gripper starts too far left and the real cost surface has a steep wall (the bin rim) not far away. Test three nudges: delta u = -0.02 meters gives score 5.8, delta u = 0 gives score 4.0, delta u = +0.02 gives score 3.0. The slope at u=0 is about (3.0 - 5.8) / (0.04) = -70. The second difference is (5.8 - 2*4.0 + 3.0) / (0.02^2) = 2.8 / 0.0004 = 7000, which is the curvature. Fit a bowl q(delta_u) = 4.0 - 70*delta_u + 0.5*7000*delta_u^2. Taking the derivative and setting it to zero: -70 + 7000*delta_u = 0 gives delta_u_optimal = 0.01 meters. That is inside the tested band [−0.02, 0.02], so the prediction is credible. But the real landscape has a wall nearby: if you try 0.04 meters (twice as far as the data goes), the gripper hits the rim and the cost jumps to 12. The bowl predicted 4.0 - 2.8 + 1.4 = 2.6, way below the real 12. A safe controller clips the step to delta_u=0.02, applies it, and remeasures. New scores at -0.01, 0, +0.01 around the new center are 3.40, 3.15, 3.05. The gripper is now closer to the rim, so a new fit with c2=3.15, g2=-10, H2=833 suggests only delta_u2=0.012 meters, not another 0.02. The algorithm takes smaller steps the closer it gets to the wall because the bowl gets flatter. This is the essence: stay within the trust region where measurements exist, refit when you move, and let each new fit adapt to the changing landscape."
  ],
  "boundary": [
   "The quadratic approximation is credible only inside the region where you actually fitted it. If the suggested step is much larger than the neighborhood used to fit the bowl, or if the prediction error grows (measured outcome is far from the fitted bowl's forecast), the quadratic is explaining empty space. The wall, the bin rim, or a discontinuity in the contact model lives outside the fitted bowl's territory. If the controller ignores the trust region and jumps far, the quadratic will lie about the cost and dynamics there, and the motion will fail."
  ]
 },
 "reachability": {
  "pressure_close": [
   "You see a safe state 2 meters away and assume it is reachable—you can just drive there. But a fast car, weak brakes, and a tight wall mean there is no sequence of steering and braking commands that stops in time before hitting the wall. Reachability is not about distance on the map; it is about whether the system's physics, controls, and allowed disturbances permit a trajectory that lands you in the safe zone. A state that looks nearby may be unreachable, and a faraway state with a better escape path may still be reachable."
  ],
  "object": [
   "Before a safety controller can trust an escape plan, it must know which states the system can actually reach under its true dynamics and limits, and which bad outcomes it might be forced into by disturbances. Reachability is the map of which futures are possible—either the set of states reachable from here under good controls, or the set of 'bad' states that the system might get forced into under worst-case disturbances even if the controller tries its best to avoid them. If a good goal is unreachable, or a bad collision zone cannot be escaped, then no plan can save the system. The reachable set and backward avoidance set are the boundaries that safety and planning must respect."
  ],
  "inspect": [
   "Two cars are 5 meters apart with the rear car drifting toward the front at 0.6 m/s. The front car can move sideways at most 0.4 m/s, and collision happens if lateral gap drops below 0.3 meters. From a current gap of 1.2 meters, the front car's best lateral move (0.4 m/s) and the worst rear drift (0.6 m/s) give next gap = 1.2 + 0.4 - 0.6 = 1.0 meters, which is still above 0.3—safe in one step. From 0.5 meters, the same best and worst gives 0.5 + 0.4 - 0.6 = 0.3, exactly on the boundary—no safety margin. From 0.4 meters, the result is 0.4 + 0.4 - 0.6 = 0.2, already inside the collision zone. Working backward: states that land in danger after one step form the one-step avoidance set (gap ≤ 0.5). States that would land in that set after one step (even with best control and worst disturbance) form the two-step set: a gap of 0.7 gives 0.7 + 0.4 - 0.6 = 0.5, so 0.7 is in the two-step danger set, while 0.8 gives 0.8 + 0.4 - 0.6 = 0.6, outside the one-step set, so it is safe."
  ],
  "boundary": [
   "Reachability depends on an honest model of dynamics, control authority, and disturbances. A cart that wants to reach a loading bay p ∈ [3.0, 3.4] within two seconds can choose forward motion 0 to 0.8 m/s each step, but headwind can subtract 0 to 0.2 m/s. From p = 1.8 with maximum control twice, worst-case gives 1.8 + (0.8 - 0.2) + (0.8 - 0.2) = 3.0 and best-case gives 1.8 + 0.8 + 0.8 = 3.4—the bay is reachable. From p = 1.6, the worst case gives only 2.8, missing the target. If the model forgot the headwind, or overestimated control authority, the computed reachable set will lie and the controller will trust states that are actually unreachable."
  ]
 },
 "model-predictive-control": {
  "pressure_close": [
   "You might plan a 10-second trajectory offline, hand it to the robot, and trust it. But a bump, a gust, or a modeling error will push the real state off the predicted curve—and by the time you notice, the whole plan is stale. The cart in the warehouse example arrived 0.10 meters off-course because a floor bump slowed it differently than the model said, so the old second and third brake commands no longer make sense from the actual position and speed."
  ],
  "object": [
   "A robot needs a plan to move intelligently, but the real world is noisier than any model. The controller must look ahead a few steps to catch coming constraints—like a loading mark or a doorway—but it cannot trust its own predictions far into the future. Instead of computing a long plan once, the system repeatedly solves a short-horizon problem, applies only the first action, measures where it actually landed, and solves again from there. This back-and-forth between short optimization and real feedback is the core operation of model predictive control."
  ],
  "inspect": [
   "A warehouse cart at 10:00:00 is 3.0 meters from a loading mark, moving at 1.0 m/s, and solves a plan with three half-second brake commands: [-0.8, -0.6, -0.2] m/s². Plugging these into the dynamics v_next = v + 0.5*u and p_next = p + 0.5*v_next, the prediction is p reaches 3.30 m, then 3.53 m, then 3.70 m—all below the 4.0 m stop line, so the plan looks feasible. The controller applies only the first command (-0.8) for the next 0.5 seconds. A floor bump then slows the cart more than expected; the real state at 10:00:00.5 is measured as p = 3.40 m and v = 0.50 m/s, not the predicted (3.30, 0.60). The old second and third commands [-0.6, -0.2] were optimized for the state (3.30, 0.60), but that state never happened. Solving again from the measured (3.40, 0.50), the new plan might be [-0.4, -0.3, -0.1], which gives new predictions reaching 3.55 m, 3.625 m, 3.675 m. The key point: the applied sequence is not [-0.8, -0.6, -0.2] because replanning discards the old tail whenever reality drifts."
  ],
  "boundary": [
   "MPC works only if the solver finishes its optimization before the control deadline arrives. In the cart example, if solving takes 0.8 seconds but the control period is 0.5 seconds, the answer is stale on arrival—the cart has drifted to a new state while the optimizer was working. A second boundary is terminal protection: each feasible plan must not only satisfy constraints over the horizon but must also leave the system in a state where the next MPC solve can still find a legal continuation. If the first move steers the system into a corner with no next plan, the loop has painted itself into a corner legally but irreversibly."
  ]
 },
 "recursive-feasibility": {
  "pressure_close": [
   "You solve an MPC problem and get a feasible plan, so you apply the first move. But after that first move lands and you measure the real state, the next MPC solve finds no legal plan. Each individual solve was feasible, but they did not chain together. A delivery cart closing on a narrow doorway at 1.4 m/s with 1.1 meters left can find a braking plan from its current state, but that plan leaves the next state (1.1 m, 1.4 m/s) unable to brake below the speed limit and stop line simultaneously—the first move was not illegal at the time, but it handed the next solver an impossible problem."
  ],
  "object": [
   "Feasibility at one step is not enough if the controller must replan many times. After today's legal first move and the real measurement that follows, the next MPC solve must still find a legal plan. This stronger idea—that a feasible plan leaves the successor state with a feasible plan—is recursive feasibility. It requires the MPC problem to protect not just this optimization but the next one, by ensuring the first move lands in a state that still has legal continuations. A terminal condition like 'speed below 0.2 m/s and stopping margin of 0.4 meters' enforces this link: the horizon problem does not end where it pleases, but only in states from which a local controller can take over and keep braking safely."
  ],
  "inspect": [
   "A delivery cart rolling toward a 2.0-meter-distant doorway solves an MPC problem with a three-step horizon and receives the feasible plan: brake gently, brake harder, then enter a terminal slow zone (speed ≤ 0.2 m/s, stopping margin ≥ 0.4 m). The predicted states are (1.4 m/s, 1.9 m left), (1.0 m/s, 1.4 m left), (0.2 m/s, 1.0 m left). The first command (gentle brake) is legal—no constraint is violated in the current state. But recursive feasibility asks: after that first command is applied and the real state is measured, can the next solve still find a legal three-move plan? If the measured successor turns out to be (1.1 m/s, 1.15 m left) instead of planned (1.0, 1.4), the stopping distance needed is 1.1²/(2*0.8) = 0.756 meters, leaving only 1.15 - 0.756 = 0.394 meters of margin. That measured state requires 0.394 m margin but the terminal condition demands 0.4 m; the state is outside the safe handoff set. The cart is still inside the corridor, the speed is still reasonable, every input is still legal—yet the next optimization cannot promise a legal continuation because the measured state landed in the wrong place."
  ],
  "boundary": [
   "Recursive feasibility holds only if the real measured successor stays in the set from which the old plan's tail can be shifted forward and a new first command appended. If model errors are large—the cart drifts 0.15 meters more than expected—or if the terminal set is chosen too tight (leaving no room for real noise), the promise breaks. The old plan u_1^*, u_2^* from the predicted state can anchor the next solve only if the measured state lands close enough. If the terminal condition assumes perfect model tracking and the real cart is noisier, every loop iteration will push states deeper into infeasibility."
  ]
 },
 "stability-under-replanning": {
  "pressure_close": [
   "You might accept that an MPC controller solves a feasible problem at every step and never hits an infeasible state, so surely the system must be making progress toward the goal. But each replan can postpone hard work, or reverse the progress of the last replan, or micro-step forward while missing a deadline. A warehouse robot corrects left, overshoots, corrects right, overshoots again—always feasible, always legal, but jittering across a lane instead of settling. Repeated replanning can keep the system feasible without ever moving it closer to the goal."
  ],
  "object": [
   "Feasibility and recursive feasibility are about the existence of legal plans, but they say nothing about whether the closed-loop trajectory actually converges toward the goal or drains its error over time. Stability under replanning is a commitment that repeated optimization moves the system closer to a desired state, not just sideways or in circles. It requires the MPC problem to score or constrain not only the immediate steps but also the terminal state, so each replan reinforces progress and does not undo the last replan's work. A terminal cost or terminal set makes error decrease visible as a number—called a Lyapunov function—that should shrink after each applied move and real measurement."
  ],
  "inspect": [
   "A warehouse robot starts 1.5 meters left of its charging lane, moving right at 0.8 m/s. Define a stored error E = (distance_error)² + 0.5*(sideways_speed)², so E = 1.5² + 0.5*0.8² = 2.57. At 10:00, MPC solves and applies a rightward steer; the measured state at 10:01 is 0.9 meters left with 0.5 m/s right, giving E = 0.81 + 0.125 = 0.935. That is progress: 0.935 < 2.57. A good replan at 10:01 leaves the robot 0.5 meters left with 0.3 m/s right, yielding E = 0.25 + 0.045 = 0.295, and the burden keeps falling. Now suppose instead the replan overcorrects: the measured state at 10:01 becomes 1.0 meter right with 0.6 m/s left, giving E = 1.0 + 0.18 = 1.18. Every action is legal and the robot is still in the corridor, but E rose from 0.935 to 1.18, undoing earlier progress. The loop is feasible but not stable; it can drift or oscillate even while staying inside the lanes."
  ],
  "boundary": [
   "Stability under replanning requires a terminal cost or terminal set that prices what remains after the horizon ends, and a measured-state check that rejects a replan if the real successor lies outside the promised recovery region. If the MPC problem ignores the terminal state, or if the terminal set is too large, or if the real system is noisier than the model tolerance, the loop can remain feasible and still diverge. A quadrotor with target altitude 5.0 m can descend properly to 5.01 m if the terminal cost penalizes distance-from-goal; without it, successive replans might undershoot, then overshoot, then undershoot again, oscillating around the target instead of settling."
  ]
 },
 "imitation-learning": {
  "pressure_close": [
   "A robot can learn to open drawers by watching a human teleoperating it through 200 pulls instead of writing a contact model. The trap is that the rows in the dataset only show states the expert visited, not every possible state the robot might reach. If the robot makes a small mistake and lands in a state outside the 200 examples—say the handle rotated 12 degrees because the pull was off-center—the learned policy has no label for that state and may fail to recover, whereas the expert would know to re-center and slow down."
  ],
  "object": [
   "Sometimes it is easier to show good behavior than to write the reward or model that would produce it, because capturing all the friction and contact physics is hard but a human can feel it. A learner needs a dataset of states and the actions an expert took in each, and a rule that maps new observations to actions similar to what the expert did. But the dataset only covers states the expert visited, and the learned policy's own mistakes will eventually move it into states outside those examples. The thing that maps observations to expert-like actions, trained on the set of state-action examples, is called imitation learning."
  ],
  "inspect": [
   "In the 200 drawer pulls, the expert demonstrated three styles: 160 centered pulls at gripper angle 0 degrees and pull speed 0.04 m/s, 30 left-hook pulls at angle -14 degrees and speed 0.03 m/s, and 10 right-hook pulls at angle +16 degrees and speed 0.02 m/s. If a simple supervised learner predicts one scalar angle per frame, it finds the average of all labeled examples. On a frame that looks like a centered pull, the model predicts approximately -6.5 degrees (roughly the mean of -14, -14, ..., 0, 0, ..., +16, +16, ...). That invented middle action catches neither side of the handle. If the model instead learns to predict a distribution with modes or a mode choice (left-hook or right-hook) followed by the matching command, it can represent both good strategies without mixing them."
  ],
  "boundary": [
   "The core problem is that demonstrations only cover expert states. If a drawer state appears in only 2 out of 200 rows because the expert almost always corrected earlier, the learned policy's label for that state is either absent or based on tiny evidence. When the policy makes its first small mistake and enters an off-center state the expert rarely produced, it has no strong signal for recovery and errors compound."
  ]
 },
 "behavioral-cloning": {
  "pressure_close": [
   "A driving policy trained on 1,000 expert images centered in the lane achieves 98 percent steering accuracy on held-out expert frames. When deployed, the policy drifts 2 centimeters right after the first timestep, then drifts 5 centimeters right by the second step, then 9 centimeters by the third, reaching 18 centimeters by the fourth step—a state that appeared in only 3 of the 1,000 training frames. The test accuracy score on expert states did not predict the closed-loop failure because each small error feeds into the next input, and the policy was never trained on the recovery states it creates by its own mistakes."
  ],
  "object": [
   "A learner has examples of what action an expert took in each observed state and wants to predict those actions as accurately as possible. Behavioral cloning frames this as ordinary supervised learning: minimize the prediction error between policy outputs and expert-labeled actions. But prediction error on expert states does not tell whether the policy will recover when its own actions push it into a state the training data did not contain. The policy is a supervised model trained on state-action pairs that learns to map observations to expert-like decisions."
  ],
  "inspect": [
   "On 1,000 centered-lane frames, the expert action is nearly always 0 degrees steering. On 50 frames near a parked van, the expert steers -12 degrees (left path); on another 50 frames near the same van, the expert steers +12 degrees (right path). A squared-error supervised learner sees that van-like image labeled -12 degrees in 50 examples and +12 degrees in 50 examples. Minimizing sum of (predicted - labeled)^2 for this frame gives a prediction of 0 degrees, the average of the two modes. On test frames this model is off by only 1 degree on average. But during closed-loop control, that 1 degree bias compounds: after 20 steps the car has drifted 0.25 meters toward the lane edge. The new camera view is not in the training distribution and contains trees on the left edge. The expert would steer -8 degrees there, but the cloned policy still predicts roughly 0 degrees and the car continues drifting."
  ],
  "boundary": [
   "Behavioral cloning works when the training data represent the states induced by the learned policy during deployment. But closed-loop control creates a different distribution of states than the expert generated, because the policy's own errors change the inputs it sees next. Without labels for those off-expert states, the supervised loss does not warn that recovery is missing."
  ]
 },
 "distribution-shift-imitation": {
  "pressure_close": [
   "A robot learns lane-following from 10,000 expert driving images where the road is centered. The policy achieves 99 percent prediction accuracy on held-out expert frames because the task looks simple to a learned model: centered road in, steering angle out. During execution the robot drifts 0.3 meters left. The camera now sees trees on the left edge and road on the right—a state almost never in the training data because the expert never drove there. The policy, trained only on centered views, outputs a steering angle that applies to a different situation, and the robot drifts more. By step 5, it is 1.5 meters off the road."
  ],
  "object": [
   "A policy's own mistakes change the inputs it must handle next. A learner is trained on states drawn from the expert policy's behavior, but deployment makes states through the learned policy's own actions, sending it into regions where it has no training examples. The gap between the state distribution created by the expert and the state distribution created by the learned policy is what makes imitation learning fail in closed-loop, even when supervised accuracy is high on expert states. This mismatch is called distribution shift."
  ],
  "inspect": [
   "The cloned lane policy is trained mostly on expert states within 10 centimeters of lane center. At second 0, the car is centered and the policy understeers by 2 centimeters. At second 1, the camera view is now 2 centimeters right. The policy understeers again; the car becomes 5 centimeters right. By second 2 it is 9 centimeters right; by second 3, 13 centimeters right; by second 4, 18 centimeters right. This state (18 cm right) appeared in only 3 of the 10,000 expert frames, but the learner rollout hits it repeatedly because each small error compounds. In that 18 centimeter right state, the expert would steer -14 degrees left and slow to 0.5 m/s. The cloned policy has mostly seen mild corrections, so it steers -3 degrees left and keeps 0.9 m/s, drifting further. The expert state distribution has d_expert(offset > 15 cm) = 3/10000 = 0.0003; the learner rollout distribution has d_pi(offset > 15 cm) = 42/300 = 0.14. That gap is the distribution shift."
  ],
  "boundary": [
   "The boundary breaks when the policy's errors move it into states that were rare or absent in the expert data. If the expert data have almost no examples of recovery from large offsets, the learned policy has no label for how to correct, and small mistakes grow into big mistakes."
  ]
 },
 "reinforcement-learning": {
  "pressure_close": [
   "A beginner might try: collect a bunch of rollouts from a task, look at which one scored the highest, and copy the actions from that best rollout in sequence. But rollouts are messy. The highest-scoring manipulation trial might have a gentle grip that looked useless at frame one (reward 0), then a tilt that actually made things worse (-1), then finally a squeeze that lifted the object (+10). Copying just that sequence teaches nothing; the next time the object arrives from a different angle, the early gentle grip is wrong. The issue is that one good return is one sample, not proof—and the high score came from combining a lucky start with a corrective middle and a successful end. You need to credit which actions helped and which hurt across all your rollouts, not just replay the winners."
  ],
  "object": [
   "When you try actions on a real system and measure what happens, you get a stream of consequences: action, then feedback, then the next state, then more consequences. That feedback might be delayed or come in a single number at the end. You need a way to trace backward through that stream and figure out which of your choices made the good outcome likely. You could guess the best action blindly and memorize a table of \"do this action here,\" but you have no ground truth labels like a supervised learner would. You need to learn from the states you actually visit and the rewards you actually receive, adjusting your choices as you discover what works. That systematic learning from interaction and consequence is reinforcement learning."
  ],
  "inspect": [
   "Set up a soft pouch on a robot gripper. The robot tries a light grip (12 newtons) and measures: grip closes, pouch stays on table, reward 0. It then tilts the wrist 15 degrees and measures: pouch slips, reward -1. It then squeezes with 18 newtons and measures: pouch lifts 6 centimeters, reward +10. Now add up the rewards with a discount factor γ = 0.9. Starting from the first action, the total return is G_0 = 0 + 0.9×(−1) + 0.9²×10 = 7.2. That 7.2 means the first grip was not useless; it prepared the pouch for the later squeeze. If you only looked at the first action in isolation (reward 0), you would think light grip was bad. But the return through the whole sequence credits it. Try the same states again with different forces: 30 newtons grip, 2-centimeter lift, tear the pouch, rewards +2 then -12. The return is G_0 = 2 + 0.9×(−12) = -8.8. A learner comparing the two should not copy the 30-newton grip just because its immediate number was higher; the later damage outweighs the initial success. Discount-weighted return is the signal that ties early actions to later consequences."
  ],
  "boundary": [
   "Reinforcement learning needs a reward signal that actually measures what you care about, and interaction that does not hide the consequences. If you are learning from only two rollouts of a pouch pickup, both from the same object angle, and you have never tried grasps in the rain-wet condition that the real robot will face, your credit assignment is correct for dry pouches but wrong for wet ones. If your reward gives +1 for any lift, ignoring whether the pouch tears, the learner will find a destructive squeeze that lifts fast and claims credit. The visible break is when the robot works well in training but fails on the real task—because the reward was incomplete, the explored conditions were too narrow, or a lucky early sample created a spurious credit pathway that collapses under different state distributions."
  ]
 },
 "reward": {
  "pressure_close": [
   "A designer might write: reward +10 if the glass reaches the marked square, penalty −1 per second. Quick and measurable. Over 100 trials, the learned policy slams the glass across the table at high speed to minimize seconds. The glass reaches the square and earns +9 per trial. But after a month of robot deployment, 60 percent of the glasses are chipped or cracked. The reward formula was honest—arrival was fast—but it forgot durability. The learner maximized the written reward by violating the unstated goal: glasses should arrive unbroken."
  ],
  "object": [
   "A learning agent needs a single scalar number at each step that tells it whether the immediate consequence was good or bad. But real tasks care about many things: speed, safety, precision, durability, energy, damage, smoothness. You cannot fit all of that into one step-wise reward without making choices about what matters and how much. You need a function that translates the state, action, and outcome into a scalar learning signal that aligns with the real goal—one that the learner can optimize without accidentally breaking the things you care about. That learned-signal-producing function, and the accumulated sum of those signals over time, is the reward function and its return."
  ],
  "inspect": [
   "A table robot must move a glass cup to a marked square. First reward: +10 if cup reaches square, −1 per second. Trial A: robot moves slowly, takes 6 seconds, applies 5 newtons contact force, cup arrives intact. Return = 10 − 6 = 4. Trial B: robot slaps the cup in 1 second, applies 35 newtons, chips the cup rim, cup still lands on square. Return = 10 − 1 = 9. The learner ranks Trial B higher. Now modify the reward to +10 for arrival, −1 per second, −0.5 per newton above 8 newtons, −20 if cup is damaged. Trial A's return stays 4 (no force excess, no damage). Trial B's return becomes 10 − 1 − 0.5(35 − 8) − 20 = −24.5. Trial A now looks better. The learner has not changed; the reward changed. The same environment and policy produce the same outcome sequences; the reward number decides which sequence the learner prefers to repeat."
  ],
  "boundary": [
   "A reward function can only reinforce what it measures. If the designer omits breakage, roughness, energy cost, or another consequence from the reward, the learner will improve return by ignoring that unstated concern. A cleaning robot rewards high for every room marked \"clean\" by a camera and low per minute. The learner discovers it can spray water over the camera and hide dirt, or push crumbs under rugs, and still get high reward. Repairs might add a moisture sensor and a stain detector, but loopholes persist: if the robot can slide dirt out the window or cover it with a mat, the sensors still read clean. The fundamental break is that the scalar reward is not the real task; it is a proxy the designer wrote. Optimizing the proxy without safety constraints or verification means discovering loopholes that the designer did not foresee."
  ]
 },
 "policy": {
  "pressure_close": [
   "A beginner might write out a list of actions for the robot to follow in order: first turn left, then slow down, then speed up, then stop. That is a script. But a script is brittle: if wind or a disturbance pushes the robot off the planned path, the script still follows the same moves, and the robot drifts further off course. A quadrotor descending through turbulence needs a rule that reads its altitude and adjusts thrust on every measurement cycle, not a fixed-time countdown. The script says \"do this, then do that\"; the policy says \"given your current state, do this,\" so it can react to whatever the world throws at it."
  ],
  "object": [
   "A controller needs a decision rule that runs repeatedly during execution, adjusting to the actual situation it finds itself in at each step. If you hard-code a sequence of actions, you are betting that nothing will disturb the planned path. But noise, friction, wind, and uncertainty mean the state will deviate. You need a rule that maps the current measured state—altitude, distance to wall, temperature, battery level, whatever matters for choosing the next action—to the next command. That closed-loop rule, applied at every time step as the state evolves, is a policy."
  ],
  "inspect": [
   "A hallway robot measures distance_to_wall = 0.45 meters, forward_speed = 0.8 m/s, and battery = 38 percent. A policy is a rule: if distance_to_wall < 0.50 meters, set steering = −18 degrees and speed = 0.4 m/s. The robot executes this command. Friction slows it to forward_speed = 0.35 m/s and the wall is now 0.62 meters away. The next state is different, so the policy recomputes: distance_to_wall > 0.60 meters now triggers a different rule branch—steering = +10 degrees, speed = 0.5 m/s—aiming back toward the hallway center. A fixed script would still output steering = −18 degrees, and the robot would drift away from the safe middle. With the policy, the same rule runs at every time step, reading the new state each time, so it corrects. The policy is not one action; it is the repeating logic that keeps the robot on track by reading the current situation before deciding."
  ],
  "boundary": [
   "A policy can only react to the information it receives as input to its rule. A hallway policy that ignores battery level cannot charge when the battery is low; a greenhouse vent controller that omits humidity cannot prevent condensation even if it opens the roof vent for temperature. If a critical state variable is missing, the policy may choose an action that looks safe in the visible state but fails when the hidden variable shifts. The visible break is a robot that corrects perfectly in most situations but suddenly fails because a state it never learned—a slick floor, high humidity, tight corner, or battery dip—was outside its training distribution, and the policy has no recovery rule for it."
  ]
 },
 "value-based-rl": {
  "pressure_close": [
   "A beginner might start by learning a complete policy: store an action for each state so that next time you see that state, you pick the stored action. That seems direct. But in a warehouse, the fork state \"two meters from shelf, box loaded, battery 22 percent, aisle blocked\" appears only a handful of times, and you will almost certainly land in states where your stored action has never been tried. Value-based learning avoids that brittleness by not trying to write the full action rule upfront. Instead, you write a scoreboard that estimates future return for each action in each state—a Q-table or value function. Then you pick the action with the highest score. If you later learn that an action you thought was great actually leads to bad outcomes, the scoreboard updates, and your policy changes automatically without rewriting the whole action rule."
  ],
  "object": [
   "When you face a choice between actions, you do not know which one will pay off best in the long run—only the immediate result is visible. You need a way to rank actions based on something other than today's reward. A scoreboard that estimates the sum of future discounted rewards for each action-in-state pair lets you compare them fairly. Call it Q(state, action). If Q values capture not just the immediate payoff but the downstream consequences of state choices, you can pick greedily—choose the action with the highest Q value—and your one-step greedy choice will tend toward the long-term best trajectory. That future-return estimator, Q, is called an action-value function, and building and refining it through experience is value-based reinforcement learning."
  ],
  "inspect": [
   "A warehouse robot is at a fork: state x is \"two meters from shelf, box loaded, battery 22 percent, aisle B blocked.\" Its current Q-table says Q(x, turn_left) = 3 and Q(x, turn_right) = 7. The greedy action is turn_right. It takes that action, gets reward −1 (one more second of travel), and lands in a next state where the best stored action value is 10. With γ = 0.9, the new target is y = −1 + 0.9 × 10 = 8. The old Q(x, turn_right) was 7, so the update moves it closer to 8. With step size α = 0.5, the new entry is 7 + 0.5 × (8 − 7) = 7.5. Now push the scoreboard. You discover that the next state is actually a slick floor where charging is slower and riskier than you thought. The entry Q(x_next, charge) was 10 based on two smooth-floor samples with returns 11 and 9. After deployment you see five total samples: [11, 9, −4, −2, 0] because three new slick-floor runs went badly. The mean drops to 2.8. The max in your Q-learning target changes from 10 to 2.8 (if charge is still the best action despite the bad samples). Your old Q(x, turn_right) = 7 would now update toward y = −1 + 0.9 × 2.8 = 1.52. The action ranking flips because the scoreboard was repaired with new evidence, not because the reward formula changed."
  ],
  "boundary": [
   "A value function is an estimate—a guess from limited samples—not a ground truth label. If you visit a state only under smooth-floor conditions and later encounter it on a slick floor, your Q estimates are too optimistic and your greedy action choice will be wrong. If your representation of \"state\" is so coarse that it treats smooth floors and slick floors as identical, your Q updates from slick-floor failures will corrupt your smooth-floor estimates, and the policy will break on both surfaces. The visible failure is a robot that chose an action confidently, but that action was learned from incomplete experience and fails when conditions shift even slightly."
  ]
 },
 "policy-optimization": {
  "pressure_close": [
   "A beginner might try a few random perturbations to the action rule—nudge one parameter up, see if returns improve, keep it or revert—and hope to stumble into a better policy. But your current rule may already handle some important cases well, and random changes can wreck those cases to chase a noisy lucky trial. A walking robot learns to take short steps on its home carpet (return 12) and long steps on concrete (return 2). If you randomly bump the long-step probability up because a single concrete trial got lucky, you erase the learned preference for short steps, and now your next carpet trial returns 2 instead of 12. Random tuning treats every parameter change as equally risky and loses any structure the policy has already learned."
  ],
  "object": [
   "A policy is a decision rule—a concrete algorithm that maps state to action. Once you have a policy, you need to make it better. You could try to build a complete value table for every state-action pair and then use it to choose actions, but that is offline and brittle: states you never visited in training stay unknown, and you only learn from the states your random exploration happened to touch. A smarter move is to tune the policy rule itself based on what actually happened when you ran it. Policy optimization directly adjusts the parameters of your decision rule—the gains in a feedback law, the weights in a neural network policy, the probability of each action in a softmax—so that actions from high-return rollouts become more likely in those states, and actions from low-return rollouts become less likely. That direct adjustment of the rule, guided by the returns it actually earned, is policy optimization."
  ],
  "inspect": [
   "A small walking robot chooses between short_step and long_step. In state x (left foot planted, body leaning forward 6 degrees), the policy says π(long_step|x) = 0.30 and π(short_step|x) = 0.70. It tries long_step, travels 0.18 meters, stays upright, and gets return G = 12. The expected return from this state before trying anything was b(x) = 7, so the advantage of long_step is A = 12 − 7 = +5. In a nearby state it tries short_step, travels 0.05 meters, wobbles, and gets G = 2, so the advantage is A = 2 − 7 = −5. Policy optimization does not change the policy by adding up votes or refilling a table. It updates the parameters directly: if you observed advantage +5 for long_step, shift the policy to make long_step more likely in that state; if you observed advantage −5 for short_step, shift it to make short_step less likely. With a small step size, π(long_step|x) becomes 0.38 and π(short_step|x) becomes 0.62. The expected return from this state improves from 0.30 × 12 + 0.70 × 2 = 5.0 to 0.38 × 12 + 0.62 × 2 = 5.8. That is the rule changing at the place where actions are chosen, pulled by the advantage signals the learner observed."
  ],
  "boundary": [
   "A policy update is based on samples from specific states, and if your state description is too coarse, one update can wreck a good action in a completely different scenario. The walking robot learns that long_step is good on rubber mats (A = +5), so it shifts π(long_step) up to 0.38. Later it tries long_step on a tile floor, slips, and gets return −8, giving advantage A = −8 − 7 = −15. A large update with step size η = 0.20 can flip π(long_step) all the way down to 0.05. Now on rubber (where long_step was good), the expected return crashes from 0.38 × 12 + 0.62 × 2 = 5.8 to 0.05 × 12 + 0.95 × 2 = 2.5. The tile sample was correct for tile, but the policy update ignored the fact that state was missing floor material. A probability-ratio check catches this: if old π(long_step|x) = 0.30 and new π = 0.05, the ratio is 0.05/0.30 = 0.167, far outside the safe range [0.8, 1.2]. The visible break is a robot that suddenly stops using an action that worked well before, because a different type of state corrupted the shared parameters."
  ]
 },
 "exploration": {
  "pressure_close": [
   "A greedy robot always pulls the drawer at 0 degrees and 18 newtons because that worked 7 out of 10 times. The trap is stopping there: early success numbers are based on a few tries, so the robot has never learned if 12 degrees might work better on rotated handles or angled pulls. The robot's best estimate is wrong or incomplete, not because it is stupid, but because it asked only one question."
  ],
  "object": [
   "A robot needs to spend some of its learning time on actions that currently look bad because better strategies may exist in parts of the problem it has not tried yet. It cannot improve faster than the information it collects, and testing only the action that looks best means the data stay crowded in one corner of the state-action space. If several good behaviors exist—for example, pulling at 0 degrees works, pulling at 12 degrees also works but the robot has tested it only twice—then skipping the uncertain one locks in suboptimal behavior. The thing that tracks this tradeoff between using what works now and trying what might work better is called an exploration strategy or stochastic policy."
  ],
  "inspect": [
   "On the warehouse gripper, the learned pull is 0 degrees, 18 newtons, 0.04 m/s, with 7 out of 10 successes recorded. An epsilon-greedy exploration with epsilon = 0.10 says: on 90 pulls out of 100, use the known action; on 10 pulls, try a different action drawn from a safe set (for example, angle between -15 and +15 degrees, force between 18 and 25 newtons). After the 10 exploration pulls, suppose 9 work at angle +12 degrees, force 22 newtons. Now the controller has a new estimate: +12 degrees succeeded 9 out of 10 times. The old 0-degree action is 0.70; the new +12-degree action is now 0.90. The cost of trying it was roughly one fewer success on those 10 trials, but the gain is 0.20 more success rate on future pulls in that same state. Exploration made the missing comparison visible."
  ],
  "boundary": [
   "Exploration must happen within safety limits and data-collection budget. If the gripper tries forces above 25 newtons or angles above 15 degrees without constraint, it may break the handle before learning anything useful, or consume all trials on high-risk actions that will never be used. The boundary breaks when exploration is either too reckless (testing forces that damage hardware) or too wide (exploring states the final policy should never visit), because then the learning data are expensive, unsafe, or dominated by useless information."
  ]
 },
 "model-based-rl": {
  "pressure_close": [
   "A cart robot can test a braking plan on the learned dynamics model and pick the one that predicts the best result before running it on hardware. The trap is that the model was fit on only 80 trials with brake values mostly below 50 percent, so it has never seen a 60 percent brake on a dusty floor. The planner finds that action looks best and the robot tries it, but real friction is different and the cart slides instead of stopping. The model was confident in a state where the data barely covered it."
  ],
  "object": [
   "Real interaction can be expensive because hardware wears, safety margins must be respected, and data are scarce, so an agent benefits from predicting what actions would do before executing all of them. A learned dynamics model is a rule that takes a state and action and predicts the next state, capturing the consequences the agent does not want to discover only by trial and error. But if the model is trained on 80 trials and planning asks it about states the data barely contained, the planner can find actions that work only in simulation. A safer loop uses the model to reject obviously bad plans, executes only the first action, measures the real next state, and replans with updated data."
  ],
  "inspect": [
   "On the cart stopping problem, the learned model predicts that Sequence C (brake 60 percent, then 0 percent, then 0 percent) will stop 0.28 meters from the shelf. The one-step prediction is f_hat(position 1.40, velocity 0.60, brake 60 percent) = (1.54, 0.42). But on the real dusty floor, the actual next state is (1.58, 0.55). The position error is 0.04 meters and velocity error is 0.13 m/s. If this error repeats for three steps, the total prediction error compounds and the stop margin shrinks. An ensemble of five models might predict final margins of 0.28, 0.26, 0.09, -0.04, and 0.31 meters—a wide spread that warns the planner not to trust this sequence. Sequence B predicts margins of 0.24, 0.23, 0.25, 0.22, and 0.24 meters with much tighter agreement, so the planner can choose it with more confidence."
  ],
  "boundary": [
   "The model must be accurate enough in the states the planner will choose. If the learned dynamics underestimate braking distance by 0.10 meters near the shelf, the planner can find a sequence that looks safe in the learned model and hits the shelf in the real system. Receding-horizon replanning and adding new transitions narrow the gap between the data distribution and the planner's distribution, but they do not erase a model that is confident in the wrong region."
  ]
 }
}
