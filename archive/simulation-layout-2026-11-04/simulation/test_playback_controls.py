import math
import unittest
from formation_registry import FORMATIONS, BLEND_REQUESTS, SHAPE_GESTURES, validate_speed
from static_shapes import SHAPES, HOME, targets
from playback_controls import DemoSequence
import test_blended_controller as helpers


class PlaybackTests(unittest.TestCase):
    def test_registry_matches_geometry_and_has_unique_reserved_ids(self):
        self.assertEqual(set(FORMATIONS),set(SHAPES))
        ids=[i for f in FORMATIONS.values() for i in (f.entry_id,f.loop_id,f.blend_id)]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertNotIn(90,ids)
        self.assertEqual(set(BLEND_REQUESTS.values()),set(FORMATIONS))
        self.assertEqual(set(SHAPE_GESTURES.values()),set(FORMATIONS))

    def test_speed_rejects_nan_infinite_and_out_of_range(self):
        for bad in (math.nan,math.inf,-math.inf,0,.49,1.26,'no'):
            with self.assertRaises(ValueError):validate_speed(bad)

    def test_demo_uses_simulation_time_and_waits_for_running_formation(self):
        demo=DemoSequence();demo.start()
        self.assertEqual(demo.poll('ready',None,False,0,0),'peace')
        self.assertIsNone(demo.poll('to_shape','heart',False,10,3.2))
        self.assertIsNone(demo.poll('showing','heart',True,10,3.2))
        self.assertIsNone(demo.poll('showing','heart',True,21.99,3.2))
        self.assertEqual(demo.poll('showing','heart',True,22,3.2),'three')
        self.assertIsNone(demo.poll('blending','heart',False,30,3.2))
        self.assertIsNone(demo.poll('showing','sine',True,35,12))
        self.assertEqual(demo.poll('showing','sine',True,59,12),'ok')
        self.assertIsNone(demo.poll('showing','spiral',True,60,8))
        self.assertEqual(demo.poll('showing','spiral',True,76,8),'moon')
        self.assertIsNone(demo.poll('showing','moon',True,80,10))
        self.assertEqual(demo.poll('showing','moon',True,100,10),'helix')
        self.assertIsNone(demo.poll('showing','helix',True,101,6))
        self.assertEqual(demo.poll('showing','helix',True,113,6),'peace')
        demo.poll('landing','sine',False,60,12)
        self.assertFalse(demo.active)

    def controller(self):return helpers.BlendedControllerTests().setup_controller()

    def test_speed_change_is_grounded_only_and_disarms(self):
        ctrl,_=self.controller();uploads=[]
        def upload(speed):uploads.append(speed);ctrl.speed=speed
        ctrl._upload_animations=upload
        ctrl.keyboard_command('speed 1.25')
        self.assertEqual(uploads,[])
        ctrl.state='grounded';ctrl.armed=True
        ctrl.keyboard_command('speed 0.75')
        self.assertEqual(uploads,[.75])
        self.assertFalse(ctrl.armed)
        self.assertAlmostEqual(ctrl.period('spiral'),8/.75)
        ctrl.keyboard_command('speed nan')
        self.assertEqual(uploads,[.75])

    def test_demo_starts_at_airborne_grid_without_recursion(self):
        ctrl,swarm=self.controller()
        ctrl.state='ready';ctrl.shape=None;ctrl.current_goals=HOME;ctrl.smooth_running=ctrl.pulse_busy=False
        ctrl.keyboard_command('demo')
        ctrl.update(0)
        self.assertEqual(ctrl.state,'to_shape')
        self.assertEqual(ctrl.shape,'heart')
        self.assertTrue(ctrl.demo.active)

    def test_manual_gesture_and_keyboard_landing_cancel_demo(self):
        for label in ('peace','three','palm','fist'):
            ctrl,_=self.controller();ctrl.keyboard_command('demo')
            self.assertTrue(ctrl.demo.active)
            ctrl.handle(label,.1)
            self.assertFalse(ctrl.demo.active)
        ctrl,_=self.controller();ctrl.keyboard_command('demo');ctrl.land('Keyboard',.1)
        self.assertFalse(ctrl.demo.active)

    def test_demo_off_keeps_native_animation_running(self):
        ctrl,swarm=self.controller();ctrl.keyboard_command('demo')
        events=list(swarm.allcfs.events)
        ctrl.keyboard_command('demo off')
        self.assertFalse(ctrl.demo.active)
        self.assertTrue(ctrl.smooth_running)
        self.assertEqual(swarm.allcfs.events,events)

    def test_keyboard_moon_uses_checked_transition_and_cancels_demo(self):
        ctrl,swarm=self.controller();ctrl.keyboard_command('demo')
        ctrl.keyboard_command('moon')
        self.assertFalse(ctrl.demo.active)
        self.assertEqual(ctrl.state,'blending')
        self.assertEqual(swarm.allcfs.events[-1],('trajectory',86))

    def test_demo_cannot_arm_or_take_off_from_ground(self):
        ctrl,swarm=self.controller();ctrl.state='grounded';ctrl.smooth_running=ctrl.pulse_busy=False
        before=list(swarm.allcfs.events)
        ctrl.keyboard_command('demo')
        ctrl.update(0)
        self.assertFalse(ctrl.demo.active)
        self.assertFalse(ctrl.armed)
        self.assertEqual(swarm.allcfs.events,before)

    def test_rejected_demo_transition_cancels_cycling(self):
        ctrl,_=self.controller();ctrl.keyboard_command('demo')
        ctrl.update(0);ctrl.update(12)
        self.assertEqual(ctrl.state,'blending')
        helpers.BlendedControllerTests().deliver(ctrl,'rejected',reason='No certified route')
        ctrl.update(12.1)
        self.assertFalse(ctrl.demo.active)
        self.assertTrue(ctrl.smooth_running)
        self.assertEqual(ctrl.shape,'heart')

    def test_completed_blend_uses_scaled_period(self):
        ctrl,_=self.controller();ctrl.speed=.5
        ctrl.handle('three',.1)
        helpers.BlendedControllerTests().deliver(ctrl,'completed',until=20)
        ctrl.update(20)
        self.assertEqual(ctrl.program_started,8)
        self.assertEqual(ctrl.current_goals,targets('sine'))
