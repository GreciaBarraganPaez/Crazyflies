import json
from types import SimpleNamespace
import unittest
from smooth_animation_bridge import SmoothAnimationController
from test_static_shapes import FakeSwarm
from static_shapes import targets


class BlendedControllerTests(unittest.TestCase):
    def setup_controller(self):
        swarm=FakeSwarm()
        swarm.allcfs.startTrajectory=lambda trajectory_id,relative:swarm.allcfs.events.append(('trajectory',trajectory_id))
        ctrl=SmoothAnimationController(swarm,lambda:True)
        ctrl.continuous=ctrl.use_blends=True
        ctrl.clock=lambda:0.
        ctrl.state,ctrl.shape,ctrl.current_goals='showing','heart',targets('heart')
        ctrl.update(0)
        return ctrl,swarm

    def deliver(self,ctrl,state,target='sine',**details):
        ctrl._receive_blend(SimpleNamespace(data=json.dumps(dict(state=state,target=target,**details))))

    def test_switch_has_no_goto_brake_or_waypoint_stage(self):
        ctrl,swarm=self.setup_controller()
        ctrl.update(.9)
        ctrl.handle('three',.9)
        self.assertEqual(ctrl.state,'blending')
        for t in (1.,1.2,1.4):ctrl.update(t)
        self.assertFalse(ctrl.playback.normalizing)
        self.assertEqual(swarm.allcfs.events,[('trajectory',70),('trajectory',82)])
        self.deliver(ctrl,'completed',until=5.)
        ctrl.update(5.1)
        self.assertEqual(ctrl.shape,'sine')
        self.assertTrue(ctrl.smooth_running)
        self.assertEqual(ctrl.program_started,-1.)
        ctrl.update(5.2)
        self.assertEqual(len(swarm.allcfs.events),2)

    def test_rejected_plan_keeps_original_playback_without_restart(self):
        ctrl,swarm=self.setup_controller()
        started=ctrl.program_started
        ctrl.handle('three',.9)
        self.deliver(ctrl,'rejected',reason='no clearance certificate')
        ctrl.update(1.)
        self.assertEqual(ctrl.shape,'heart')
        self.assertTrue(ctrl.smooth_running)
        self.assertEqual(ctrl.program_started,started)
        ctrl.update(1.1)
        self.assertEqual(len(swarm.allcfs.events),2)

    def test_queued_palm_cannot_be_replaced_by_a_later_shape(self):
        ctrl,swarm=self.setup_controller()
        ctrl.handle('three',.9)
        ctrl.land('Keyboard',1.)
        ctrl.handle('ok',1.1)
        self.assertEqual(ctrl.blend_queued,'palm')
        self.deliver(ctrl,'completed',until=5.)
        ctrl.update(5.1)
        self.assertEqual(ctrl.stop_request,'palm')
        self.assertTrue(ctrl.smooth_running)
        ctrl.update(5.2)
        self.assertFalse(ctrl.smooth_running)
        self.assertEqual(ctrl.current_goals,targets('sine'))

    def test_static_arrival_request_does_not_start_old_animation(self):
        ctrl,swarm=self.setup_controller()
        swarm.allcfs.events.clear()
        ctrl.smooth_running=ctrl.pulse_busy=False
        ctrl.state='to_shape';ctrl.due=2.
        ctrl.handle('three',2.01)
        self.assertEqual(ctrl.state,'blending')
        self.assertEqual(swarm.allcfs.events,[('trajectory',82)])


if __name__=='__main__':unittest.main()
