#!/usr/bin/env python3
"""Experimental pulsing heart; simulation only. Static bridge remains the default.

Complete each high-level goTo before issuing the next. Never enter low-level
streaming mode. Stop requests finish the current pulse leg, restore the original
heart at rest, then use the existing grid return / TF-gated landing sequence.
"""
import simulation.controllers.gesture_bridge as bridge
from simulation.core.static_shapes import targets, minimum_distance, MIN_PLANNED_SEPARATION

CENTER_Z = 2.70  # keep the enlarged lower tip above the 0.6 m geometry floor
LEGS = ((1.20, 2.0), (0.80, 3.0), (1.0, 2.0))
SETTLE_SEC = 0.20


def heart_targets(scale):
    return tuple((x * scale, y, CENTER_Z + (z - CENTER_Z) * scale)
                 for x, y, z in targets('heart'))


class HeartAnimationController(bridge.SimulationController):
    animated_shapes = frozenset({"heart"})
    def __init__(self, swarm, grid_arrived=None):
        super().__init__(swarm, grid_arrived)
        self.pulse_busy = False
        self.pulse_leg = 0
        self.stop_request = None
        self.animation_scale = 1.0
        for scale, _ in LEGS:
            points = heart_targets(scale)
            if min(z for _, _, z in points) <= 0.6:
                raise ValueError('Heart pulse would move below the geometry floor')
            if minimum_distance(points) < MIN_PLANNED_SEPARATION:
                raise ValueError('Heart pulse would compress drone spacing too far')

    def configure_backend(self, backend):
        # Read the actual running backend, never infer it from the launcher title.
        self.animation_scale = 0.40 if backend == 'none' else 1.0
        print(f'Animation backend={backend}; heart cycle ~'
              f'{sum(t for _,t in LEGS)*self.animation_scale + len(LEGS)*SETTLE_SEC:.1f} simulation seconds. '
              + ('Fast ideal-motion preview.' if backend == 'none' else
                 'Physics/unknown backend: conservative timing; may run slower than real time.'), flush=True)

    def _pulse_move(self, points, seconds, now):
        if not self._move(points, seconds):
            self.stop_request = 'fist'
            return False
        self.pulse_busy = True
        self.due = now + seconds + SETTLE_SEC
        return True

    def _request_stop(self, label, now):
        # A landing request cannot be replaced by a later formation gesture.
        if self.stop_request != 'palm':
            self.stop_request = label
        print(f'{self.shape}: finishing animation leg, restoring original outline, then ' +
              ('grid and land.' if self.stop_request == 'palm' else 'grid / next formation.'), flush=True)

    def handle(self, label, now=None):
        now = self.clock() if now is None else now
        if self.shape in self.animated_shapes and self.state == 'showing':
            if label in ('palm', 'fist') or (label in bridge.SHAPE_GESTURES and
                    bridge.SHAPE_GESTURES[label] != self.shape):
                self._request_stop(label, now)
            return
        # Preserve queued palm priority during the initial formation move too.
        if self.queued_gesture == 'palm' and label != 'palm':
            return
        super().handle(label, now)

    def land(self, reason='Land', now=None):
        now = self.clock() if now is None else now
        if self.shape in self.animated_shapes and self.state == 'showing':
            self.armed = False
            self._request_stop('palm', now)
            return
        super().land(reason, now)

    def update(self, now=None):
        now = self.clock() if now is None else now
        if self.pulse_busy:
            if now < self.due:
                return
            self.pulse_busy = False
        super().update(now)
        if self.state != 'showing' or self.shape not in self.animated_shapes:
            self.pulse_leg = 0
            return
        if self.stop_request:
            if self.current_goals != targets(self.shape):
                self._pulse_move(targets(self.shape), 2.0, now)
                return
            label, self.stop_request = self.stop_request, None
            # Bypass this subclass's stop interception after restoring at rest.
            self._start_grid(now, next_shape=bridge.SHAPE_GESTURES.get(label), land=label == 'palm')
            return
        points, seconds, message, leg_count = self.animation_step()
        if self._pulse_move(points, seconds, now):
            print(message, flush=True)
            self.pulse_leg = (self.pulse_leg + 1) % leg_count

    def animation_step(self):
        scale, seconds = LEGS[self.pulse_leg]
        seconds *= self.animation_scale
        points = targets('heart') if scale == 1.0 else heart_targets(scale)
        return points, seconds, f'HEART PULSE: scale={scale:.0%}, move={seconds:.1f} simulation seconds.', len(LEGS)


if __name__ == '__main__':
    bridge.ACTIONS['peace'] = 'pulsing heart (experimental)'
    print('HEART ANIMATION EXPERIMENT: peace pulses; three/OK remain static. '
          'Palm/fist finish the current pulse leg before returning via the original heart to grid.', flush=True)
    bridge.main(controller_type=HeartAnimationController)
