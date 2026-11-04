import unittest
import gesture_bridge as bridge
from formation_animation_bridge import FormationAnimationController, wave_targets, WAVE_STEPS
from static_shapes import targets, minimum_distance, planned_segment_distance
from test_static_shapes import FakeSwarm


class WaveTests(unittest.TestCase):
    def start_wave(self):
        ctrl = FormationAnimationController(FakeSwarm(), grid_arrived=lambda: True)
        ctrl.arm(0)
        ctrl.handle('one', 0)
        t = bridge.TAKEOFF_SEC + bridge.MARGIN_SEC + .01
        ctrl.update(t)
        ctrl.handle('three', t)
        ctrl.update(ctrl.due + .01)
        return ctrl

    def test_cycle_preserves_assigned_x_and_clearance(self):
        for step in range(WAVE_STEPS):
            a, b = wave_targets(step), wave_targets(step + 1)
            self.assertGreaterEqual(planned_segment_distance(a, b), .599)
            for point, original in zip(a, targets('sine')):
                self.assertEqual(point[:2], original[:2])
                self.assertGreaterEqual(point[2], 1.49)
                self.assertLessEqual(point[2], 4.31)
            # Restoring any phase to the canonical sine also keeps X spacing.
            self.assertGreaterEqual(planned_segment_distance(a, targets('sine')), .599)
        self.assertEqual(wave_targets(WAVE_STEPS), targets('sine'))
        self.assertNotEqual(wave_targets(1), wave_targets(0))

    def test_repeats_two_cycles_without_leaving_sine(self):
        ctrl = self.start_wave()
        for _ in range(WAVE_STEPS * 2):
            ctrl.update(ctrl.due + .01)
            self.assertEqual(ctrl.state, 'showing')
            self.assertEqual(ctrl.shape, 'sine')
            self.assertTrue(ctrl.pulse_busy)

    def test_palm_waits_for_grid_and_cannot_be_overridden(self):
        ctrl = self.start_wave()
        ctrl.handle('palm', ctrl.due - .1)
        ctrl.handle('peace', ctrl.due - .05)
        ctrl.update(ctrl.due + .01)
        self.assertEqual(ctrl.current_goals, targets('sine'))
        ctrl.update(ctrl.due + .01)
        self.assertEqual(ctrl.state, 'to_grid')
        ctrl.grid_arrived = lambda: False
        ctrl.update(ctrl.due + .01)
        self.assertEqual(ctrl.state, 'to_grid')
        ctrl.grid_arrived = lambda: True
        ctrl.update(ctrl.due + .02)
        self.assertEqual(ctrl.state, 'landing')

    def test_wave_switches_to_heart(self):
        ctrl = self.start_wave()
        ctrl.handle('peace', ctrl.due - .1)
        ctrl.update(ctrl.due + .01)
        ctrl.update(ctrl.due + .01)
        self.assertEqual(ctrl.state, 'transition')
        for _ in range(6):
            if ctrl.state != 'transition':
                break
            ctrl.update(ctrl.due + .01)
        self.assertEqual(ctrl.state, 'showing')
        self.assertEqual(ctrl.shape, 'heart')
        ctrl.update(ctrl.due + .01)
        self.assertTrue(ctrl.pulse_busy)
        self.assertEqual(ctrl.shape, 'heart')


if __name__ == '__main__':
    unittest.main()
