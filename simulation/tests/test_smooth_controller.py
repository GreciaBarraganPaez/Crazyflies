import unittest
from simulation.controllers.smooth_animation_bridge import SmoothAnimationController
from simulation.controllers.gesture_bridge import SimulationController
from simulation.controllers.formation_animation_bridge import FormationAnimationController
from simulation.core.static_shapes import targets, COUNT
from simulation.tests.helpers import FakeSwarm


class SmoothControllerTests(unittest.TestCase):
    def controller(self):
        swarm=FakeSwarm()
        swarm.allcfs.startTrajectory=lambda trajectory_id,relative:swarm.allcfs.events.append(('trajectory',trajectory_id,relative))
        ctrl=SmoothAnimationController(swarm,grid_arrived=lambda:True)
        ctrl.clock=lambda:0.
        ctrl.continuous=ctrl.use_blends=True
        ctrl.state,ctrl.shape,ctrl.current_goals='showing','heart',targets('heart')
        ctrl.update(0)
        return ctrl,swarm

    def test_preview_has_one_lifecycle_base_and_physics_is_separate(self):
        self.assertEqual(SmoothAnimationController.__bases__,(SimulationController,))
        ctrl,_=self.controller()
        fallback=ctrl.configure_backend('np')
        self.assertIsInstance(fallback,FormationAnimationController)
        self.assertEqual(fallback.state,'grounded')
        self.assertIsNot(fallback,ctrl)

    def test_loop_ticks_do_not_issue_per_frame_goto_or_restart(self):
        ctrl,swarm=self.controller()
        for tick in range(1,1000):ctrl.update(tick*.02)
        self.assertEqual(swarm.allcfs.events,[('trajectory',70,False)])
        self.assertTrue(ctrl.smooth_running)

    def test_new_request_at_shape_arrival_never_starts_old_animation(self):
        ctrl,swarm=self.controller();swarm.allcfs.events.clear()
        ctrl.smooth_running=False;ctrl.state='to_shape';ctrl.due=1.
        ctrl.handle('three',1.01)
        self.assertEqual(ctrl.state,'blending')
        self.assertEqual(swarm.allcfs.events,[('trajectory',82,False)])
        self.assertFalse(ctrl.smooth_running)

    def test_switch_requests_join_without_goto_braking(self):
        ctrl,swarm=self.controller();ctrl.update(.9)
        ctrl.handle('three',.9);ctrl.update(.91)
        self.assertEqual(ctrl.state,'blending')
        self.assertFalse(ctrl.playback.normalizing)
        self.assertEqual(swarm.allcfs.events,[('trajectory',70,False),('trajectory',82,False)])

    def test_palm_stops_once_normalizes_and_lands_from_grid(self):
        ctrl,swarm=self.controller();ctrl.update(.9)
        ctrl.handle('palm',.9);ctrl.handle('three',.91);ctrl.update(.92)
        self.assertFalse(ctrl.smooth_running)
        self.assertEqual(ctrl.stop_request,'palm')
        self.assertEqual(ctrl.current_goals,targets('heart'))
        self.assertEqual(sum(e[0]=='goTo' for e in swarm.allcfs.events),COUNT)
        ctrl.update(ctrl.due+.01)
        self.assertEqual(ctrl.state,'to_grid')
        ctrl.update(ctrl.due+.01)
        self.assertEqual(ctrl.state,'landing')
        self.assertEqual(sum(e[0]=='trajectory' for e in swarm.allcfs.events),1)

    def test_palm_before_entry_returns_grid_without_starting_animation(self):
        ctrl,swarm=self.controller();swarm.allcfs.events.clear()
        ctrl.smooth_running=False;ctrl.state='to_shape';ctrl.due=1.
        ctrl.handle('palm',1.01)
        self.assertEqual(ctrl.state,'to_grid')
        self.assertTrue(ctrl.land_after_grid)
        self.assertFalse(any(e[0]=='trajectory' for e in swarm.allcfs.events))

    def test_keyboard_land_from_resting_outline_does_not_start_entry(self):
        ctrl,swarm=self.controller();swarm.allcfs.events.clear()
        ctrl.smooth_running=False
        ctrl.land('Keyboard',.1)
        self.assertEqual(ctrl.state,'to_grid')
        self.assertTrue(ctrl.land_after_grid)
        self.assertFalse(any(e[0]=='trajectory' for e in swarm.allcfs.events))

    def test_normalization_waits_for_measured_arrival(self):
        ctrl,_=self.controller()
        class Feedback:
            arrived=False
            def at(self,points,tolerance):return self.arrived
            def __call__(self):return True
        feedback=Feedback();ctrl.grid_arrived=feedback
        ctrl.land('Keyboard',.1);ctrl.update(.2)
        ctrl.update(ctrl.due+.01)
        self.assertTrue(ctrl.playback.normalizing)
        self.assertEqual(ctrl.state,'showing')
        feedback.arrived=True;ctrl.update(ctrl.due+.02)
        self.assertEqual(ctrl.state,'to_grid')

    def test_palm_overrides_shape_queued_during_fist_normalization(self):
        ctrl,swarm=self.controller()
        ctrl.handle('fist',.1);ctrl.update(.2)
        ctrl.handle('moon',.3)
        self.assertEqual(ctrl.queued_gesture,'moon')
        ctrl.handle('palm',.4);ctrl.handle('three',.5)
        self.assertIsNone(ctrl.queued_gesture)
        ctrl.update(ctrl.due+.01)
        self.assertEqual(ctrl.state,'to_grid')
        self.assertTrue(ctrl.land_after_grid)
        self.assertEqual(sum(e[0]=='trajectory' for e in swarm.allcfs.events),1)


if __name__=='__main__':unittest.main()
