import itertools
import unittest
from static_shapes import SHAPES, HOME, planned_segment_distance, MIN_PLANNED_SEPARATION
from transition_planner import plan_transition
from formation_animation_bridge import FormationAnimationController
from test_static_shapes import FakeSwarm
from gesture_bridge import arrival_metrics
from continuous_trajectories import motion, PERIODS


class Feedback:
    arrived = True
    def __call__(self): return self.arrived
    def at(self, points, tolerance=.2): return self.arrived


class TransitionTests(unittest.TestCase):
    def test_routes_can_start_from_current_animation_phase(self):
        for source in PERIODS:
            for phase in range(16):
                start = tuple(state[0] for state in motion(source, PERIODS[source]*phase/16))
                for destination in SHAPES:
                    if destination == source: continue
                    previous = start
                    for stage in plan_transition(start,SHAPES[destination]):
                        self.assertGreaterEqual(planned_segment_distance(previous,stage),MIN_PLANNED_SEPARATION)
                        previous=stage
    def test_measured_seven_cm_hover_bias_does_not_deadlock_transition(self):
        goals = SHAPES['heart']
        measured = tuple((x, y, z-.07) for x,y,z in goals)
        self.assertFalse(arrival_metrics(measured, goals, .06)[0])
        self.assertTrue(arrival_metrics(measured, goals, .10)[0])
        bad = list(measured)
        bad[0] = bad[1]
        self.assertFalse(arrival_metrics(bad, bad, .10)[0])

    def test_only_ideal_backend_gets_faster_pulse(self):
        ctrl = FormationAnimationController(FakeSwarm())
        ctrl.shape = 'heart'
        physics_duration = ctrl.animation_step()[1]
        ctrl.configure_backend('none')
        self.assertLess(ctrl.animation_step()[1], physics_duration)
        ctrl.configure_backend('np')
        self.assertEqual(ctrl.animation_step()[1], physics_duration)

    def test_nonfinite_route_is_rejected(self):
        bad = list(SHAPES['heart'])
        bad[0] = (float('nan'), 0.0, 2.7)
        with self.assertRaises(ValueError):
            plan_transition(tuple(bad), SHAPES['sine'])

    def test_all_ordered_shape_pairs_have_checked_routes_without_grid(self):
        for source, destination in itertools.permutations(SHAPES, 2):
            with self.subTest(source=source, destination=destination):
                previous = SHAPES[source]
                route = plan_transition(previous, SHAPES[destination])
                for stage in route:
                    self.assertNotEqual(stage, HOME)
                    self.assertGreaterEqual(planned_segment_distance(previous, stage), MIN_PLANNED_SEPARATION)
                    previous = stage
                self.assertEqual(previous, SHAPES[destination])

    def test_crossing_paths_use_depth_lanes(self):
        start = SHAPES['sine']
        end = tuple(reversed(start))
        route = plan_transition(start, end)
        self.assertEqual(len(route), 3)
        self.assertTrue(any(abs(y) > .1 for x,y,z in route[0]))

    def setup_controller(self):
        feedback = Feedback()
        ctrl = FormationAnimationController(FakeSwarm(), feedback)
        ctrl.state, ctrl.shape, ctrl.current_goals = 'showing', 'spiral', SHAPES['spiral']
        ctrl.handle('three', 0)
        self.assertEqual(ctrl.state, 'transition')
        return ctrl, feedback

    def test_missing_feedback_blocks_first_and_subsequent_stages(self):
        ctrl, feedback = self.setup_controller()
        feedback.arrived = False
        ctrl.update(1)
        self.assertEqual(ctrl.current_goals, SHAPES['spiral'])
        feedback.arrived = True
        ctrl.update(2)
        commanded = ctrl.current_goals
        feedback.arrived = False
        ctrl.update(ctrl.due + .01)
        self.assertEqual(ctrl.current_goals, commanded)
        self.assertEqual(ctrl.state, 'transition')

    def test_landing_queued_during_route_is_not_overwritten(self):
        ctrl, feedback = self.setup_controller()
        ctrl.land('Keyboard', 0)
        ctrl.handle('peace', 0)
        self.assertEqual(ctrl.route_request, 'palm')
        for _ in range(8):
            ctrl.update(ctrl.due + .01)
            if ctrl.state == 'to_grid': break
        self.assertEqual(ctrl.state, 'to_grid')
        self.assertTrue(ctrl.land_after_grid)


if __name__ == '__main__': unittest.main()
