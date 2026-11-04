#!/usr/bin/env python3
"""Pulsing heart + travelling sine, using completed high-level moves only."""
import math
import time
import simulation.controllers.gesture_bridge as bridge
from simulation.controllers.heart_animation_bridge import HeartAnimationController
from simulation.core.static_shapes import targets
from simulation.core.transition_planner import plan_transition

WAVE_STEPS = 12
WAVE_STEP_SEC = 0.70


def wave_targets(step):
    """Move Z while preserving each drone's assigned X and Y (0.6 m apart).

    Increasing phase sends the wave toward +X. Phase zero is the exact static
    sine so return-to-grid always starts with the validated original mapping.
    """
    step %= WAVE_STEPS
    if step == 0:
        return targets('sine')
    phase = 2 * math.pi * step / WAVE_STEPS
    return tuple((x, y, 2.90 + 1.40 * math.sin(2 * math.pi * x / 5.4 - phase))
                 for x, y, _ in targets('sine'))


class FormationAnimationController(HeartAnimationController):
    animated_shapes = frozenset({'heart', 'sine'})

    def __init__(self, swarm, grid_arrived=None):
        super().__init__(swarm, grid_arrived)
        self.route = []
        self.route_shape = None
        self.route_request = None
        self.route_wait_reported = False
        self.route_report_at = 0.0

    def _start_grid(self, now, next_shape=None, land=False):
        if next_shape and not land and self.state == 'showing' and self.shape:
            # Animation stop restores its canonical resting shape before here.
            try:
                self.route = list(plan_transition(self.current_goals, targets(next_shape)))
            except ValueError as error:
                print(f'Transition refused: {error}. Holding current formation.', flush=True)
                return
            self.route_shape = next_shape
            self.route_request = None
            self.state = 'transition'
            self.pulse_busy = False
            print(f'SHAPE TRANSITION: {self.shape} -> {next_shape}, '
                  f'{len(self.route)} checked stages; no grid.', flush=True)
            self.due = now  # Verify the source pose before entering the first lane.
            return
        super()._start_grid(now, next_shape, land)

    def _next_route_stage(self, now):
        points = self.route[0]
        # Give long depth-lane movements more time instead of compressing them.
        distance = max(math.dist(a, b) for a, b in zip(self.current_goals, points))
        seconds = max(getattr(self, 'route_min_sec', 2.0), distance / getattr(self, 'route_speed', 0.8))
        if not self._move(points, seconds):
            print('Transition stage rejected; holding. Inspect simulator.', flush=True)
            self.due = float('inf')
            return
        self.route.pop(0)
        self.due = now + seconds + bridge.MARGIN_SEC
        self.route_wait_reported = False
        self.route_report_at = 0.0
        print(f'Transition stage commanded: {seconds:.1f} simulation seconds; '
              f'{len(self.route)} stages remaining after arrival.', flush=True)

    def handle(self, label, now=None):
        if self.state == 'transition':
            if label in ('palm', 'fist') or label in bridge.SHAPE_GESTURES:
                if self.route_request != 'palm':
                    self.route_request = label
                print(f'Queued {self.route_request} until checked transition completes.', flush=True)
            return
        super().handle(label, now)

    def land(self, reason='Land', now=None):
        if self.state == 'transition':
            self.armed = False
            self.route_request = 'palm'
            print('Landing queued until checked transition completes.', flush=True)
            return
        super().land(reason, now)

    def update(self, now=None):
        now = self.clock() if now is None else now
        if self.state != 'transition':
            super().update(now)
            return
        if now < self.due:
            return
        feedback = getattr(self.grid_arrived, 'at', None)
        if feedback is not None and not feedback(self.current_goals, tolerance=0.10):
            if time.monotonic() >= self.route_report_at:
                print('Transition waiting: ' + getattr(self.grid_arrived, 'last_status', 'Fresh waypoint feedback required'), flush=True)
                self.route_report_at = time.monotonic() + 5
                self.route_wait_reported = True
            return
        if self.route:
            self._next_route_stage(now)
            return
        self.shape = self.route_shape
        self.route_shape = None
        self.state = 'showing'
        self.pulse_leg = 0
        request, self.route_request = self.route_request, None
        if request:
            self.handle(request, now)

    def animation_step(self):
        if self.shape == 'heart':
            return super().animation_step()
        step = (self.pulse_leg + 1) % WAVE_STEPS
        return (wave_targets(step), WAVE_STEP_SEC,
                f'SINE WAVE: phase {step}/{WAVE_STEPS}, travelling toward +X.', WAVE_STEPS)


if __name__ == '__main__':
    bridge.ACTIONS.update(peace='pulsing heart', three='travelling sine wave')
    print('FORMATION ANIMATIONS: peace=heart pulse; three=travelling sine; OK=static spiral. '
          'Shape switches use checked direct/depth routes; palm/fist return to grid.', flush=True)
    bridge.main(controller_type=FormationAnimationController)
