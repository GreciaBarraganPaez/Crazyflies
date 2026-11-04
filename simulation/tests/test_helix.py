import math
import unittest
from simulation.core.continuous_trajectories import motion,PERIODS,compile_trajectories
from simulation.formations.helix import RADIUS,CENTER_Z
from simulation.visualization.formation_colors import infer_frame,frame_colors
from simulation.scenes.trajectories import certificate
from simulation.core.static_shapes import targets
import simulation.tests.test_blended_controller as helpers


class HelixTests(unittest.TestCase):
    def test_constant_radius_nonzero_depth_motion_and_speed(self):
        for k in range(33):
            states=motion('helix',PERIODS['helix']*k/32)
            self.assertGreater(max(s[0][1] for s in states)-min(s[0][1] for s in states),2.)
            for state,original in zip(states,targets('helix')):
                p,v,a=state
                self.assertEqual(p[0],original[0])
                self.assertAlmostEqual(math.hypot(p[1],p[2]-CENTER_Z),RADIUS)
                self.assertAlmostEqual(math.dist(v,(0,0,0)),2*math.pi*RADIUS/PERIODS['helix'])

    def test_analytic_velocity_and_acceleration_including_entry_ramp(self):
        for entry in (False,True):
            for k in range(1,16):
                t=PERIODS['helix']*k/16;h=1e-5
                before,at,after=(motion('helix',u,entry) for u in (t-h,t,t+h))
                for a,b,c in zip(before,at,after):
                    for axis in range(3):
                        self.assertAlmostEqual((c[0][axis]-a[0][axis])/(2*h),b[1][axis],places=6)
                        self.assertAlmostEqual((c[1][axis]-a[1][axis])/(2*h),b[2][axis],places=6)

    def test_complete_polynomial_paths_are_certified_at_speed_extremes(self):
        for speed in (.5,1.,1.25):
            for entry in (False,True):
                self.assertGreaterEqual(certificate(compile_trajectories('helix',entry,speed=speed)),.52)

    def test_color_phase_tracks_actual_3d_poses(self):
        for k in range(33):
            t=PERIODS['helix']*k/32
            frame=infer_frame(tuple(s[0] for s in motion('helix',t)))
            self.assertEqual(frame.shape,'helix')
            self.assertAlmostEqual(math.remainder(frame.phase-2*math.pi*k/32,2*math.pi),0.)
            self.assertEqual(len(frame_colors(frame)),19)

    def test_keyboard_helix_uses_joined_transition(self):
        ctrl,swarm=helpers.BlendedControllerTests().setup_controller()
        ctrl.keyboard_command('helix')
        self.assertEqual(ctrl.state,'blending')
        self.assertEqual(swarm.allcfs.events[-1],('trajectory',88))
