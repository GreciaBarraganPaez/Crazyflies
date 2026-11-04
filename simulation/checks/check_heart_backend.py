"""Run in WSL: isolated firmware-planner test; never connects to ROS services.

Uses ideal tracking of backend setpoints, not a physics/visual acceptance test.
Checks three simulated planner objects first, then the full nineteen.
"""
import math
import itertools
from crazyflie_sim.crazyflie_sil import CrazyflieSIL
from simulation.controllers.heart_animation_bridge import heart_targets, LEGS
from simulation.controllers.formation_animation_bridge import wave_targets, WAVE_STEPS, WAVE_STEP_SEC
from simulation.core.static_shapes import HOME, DRONES, targets, minimum_distance, MIN_PLANNED_SEPARATION, SHAPES
from simulation.core.transition_planner import plan_transition


def check(count):
    clock = [0.0]
    fleet = [CrazyflieSIL(name, (x,y,0), 'none', lambda: clock[0])
             for name, (x,y,z) in zip(DRONES[:count], HOME[:count])]
    worst = float('inf')

    def advance(seconds, goals):
        nonlocal worst
        start = clock[0]
        for frame in range(1, 202):
            clock[0] = start + (seconds + .2) * frame / 201
            states = [cf.getSetpoint() for cf in fleet]
            for cf,state in zip(fleet, states):
                cf.setState(state)  # ideal tracking, no simulated physics
                assert cf.mode == CrazyflieSIL.MODE_HIGH_POLY
            worst = min(worst, minimum_distance([tuple(s.pos) for s in states]))
        for state,goal in zip(states, goals):
            assert math.dist(state.pos,goal) < 1e-4, (state.pos,goal)

    def move(points, seconds):
        for cf,goal in zip(fleet, points):
            cf.goTo(goal, 0.0, seconds)
        advance(seconds, points)

    for cf in fleet:
        cf.takeoff(2.7, 3.0)
    advance(3.0, HOME)
    move(targets('heart'), 4.8)
    for _ in range(2):
        for scale, seconds in LEGS:
            move(targets('heart') if scale == 1 else heart_targets(scale), seconds)
    # Stop from the enlarged heart, normalize, return to grid, then land.
    move(heart_targets(1.2), 2.0)
    move(targets('heart'), 2.0)
    move(HOME, 4.8)
    move(targets('sine'), 4.8)
    for step in range(1, WAVE_STEPS * 2 + 1):
        move(wave_targets(step), WAVE_STEP_SEC)
    move(wave_targets(5), WAVE_STEP_SEC)
    move(targets('sine'), 2.0)
    move(HOME, 4.8)
    for source, destination in itertools.permutations(SHAPES, 2):
        move(targets(source), 4.8)
        previous = targets(source)
        for stage in plan_transition(previous, targets(destination)):
            seconds = max(2.0, max(math.dist(a,b) for a,b in zip(previous,stage)) / .8)
            move(stage, seconds)
            previous = stage
        move(HOME, 4.8)
    for cf in fleet:
        cf.land(.04, 3.2)
    advance(3.2, tuple((x,y,.04) for x,y,z in HOME))
    if count == 19:
        assert worst >= MIN_PLANNED_SEPARATION, worst
    print(f'{count} isolated backend planners: pulse, wave, all direct shape routes, grid landing passed; minimum spacing {worst:.3f} m')


if __name__ == '__main__':
    check(3)
    check(19)
