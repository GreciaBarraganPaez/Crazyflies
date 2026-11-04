"""Offline geometry and controller regression tests for the opt-in heart pulse."""
import unittest
import gesture_bridge as bridge
from heart_animation_bridge import HeartAnimationController, heart_targets, LEGS
from static_shapes import (DRONES, targets, minimum_distance,
                           planned_segment_distance, MIN_PLANNED_SEPARATION)
from test_static_shapes import FakeSwarm


class HeartTests(unittest.TestCase):
    def start_heart(self):
        swarm = FakeSwarm()
        ctrl = HeartAnimationController(swarm, grid_arrived=lambda: True)
        ctrl.arm(0)
        ctrl.handle('one', 0)
        t = bridge.TAKEOFF_SEC + bridge.MARGIN_SEC + .01
        ctrl.update(t)
        ctrl.handle('peace', t)
        t += bridge.SHAPE_MOVE_SEC + bridge.MARGIN_SEC + .01
        ctrl.update(t)
        self.assertTrue(ctrl.pulse_busy)
        return ctrl, swarm, t

    def test_geometry_and_symmetry_entire_cycle(self):
        previous = targets('heart')
        for scale, _ in LEGS:
            points = targets('heart') if scale == 1 else heart_targets(scale)
            self.assertGreaterEqual(planned_segment_distance(previous, points), MIN_PLANNED_SEPARATION)
            for i in range(101):
                u = i / 100
                frame = tuple(tuple(a + u*(b-a) for a,b in zip(p,q)) for p,q in zip(previous,points))
                self.assertGreaterEqual(minimum_distance(frame), MIN_PLANNED_SEPARATION)
                self.assertGreater(min(p[2] for p in frame), .6)
            outline = {(round(x,4), round(z,4)) for x,y,z in points}
            self.assertTrue(all((-x,z) in outline for x,z in outline))
            previous = points

    def test_no_repeated_commands_during_leg(self):
        ctrl, swarm, t = self.start_heart()
        count = len(swarm.allcfs.events)
        ctrl.update(t + .5)
        self.assertEqual(len(swarm.allcfs.events), count)
        ctrl.update(ctrl.due + .01)
        self.assertEqual(ctrl.current_goals, heart_targets(.8))

    def test_palm_restores_outline_then_verified_grid_then_lands(self):
        ctrl, swarm, t = self.start_heart()
        ctrl.handle('palm', t + .1)
        ctrl.handle('three', t + .2)
        self.assertEqual(ctrl.stop_request, 'palm')
        ctrl.update(ctrl.due + .01)
        self.assertEqual(ctrl.current_goals, targets('heart'))
        ctrl.update(ctrl.due + .01)
        self.assertEqual(ctrl.state, 'to_grid')
        ctrl.grid_arrived = lambda: False
        ctrl.update(ctrl.due + .01)
        self.assertEqual(ctrl.state, 'to_grid')
        ctrl.grid_arrived = lambda: True
        ctrl.update(ctrl.due + .02)
        self.assertEqual(ctrl.state, 'landing')
        self.assertEqual(swarm.allcfs.events[-1][0], 'land')

    def test_switch_to_sine_through_original_heart_and_grid(self):
        ctrl, swarm, t = self.start_heart()
        ctrl.handle('three', t + .1)
        ctrl.update(ctrl.due + .01)
        ctrl.update(ctrl.due + .01)
        self.assertEqual(ctrl.state, 'to_grid')
        ctrl.update(ctrl.due + .01)
        self.assertEqual(ctrl.state, 'to_shape')
        self.assertEqual(ctrl.current_goals, targets('sine'))

    def test_keyboard_shutdown_uses_same_landing_sequence(self):
        ctrl, swarm, t = self.start_heart()
        ctrl.land('Shutdown', t + .1)
        self.assertEqual(ctrl.stop_request, 'palm')
        self.assertFalse(any(e[0] == 'land' for e in swarm.allcfs.events))


if __name__ == '__main__':
    unittest.main()
