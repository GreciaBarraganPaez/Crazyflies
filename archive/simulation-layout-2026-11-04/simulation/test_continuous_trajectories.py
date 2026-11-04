import math
import unittest
from continuous_trajectories import compile_trajectories, motion, PERIODS
from static_shapes import minimum_distance, targets


class ContinuousTests(unittest.TestCase):
    def assert_vector_close(self, a, b):
        self.assertLess(math.dist(a,b), 1e-7)

    def test_c2_continuity_at_every_piece_entry_and_loop_boundary(self):
        for shape in PERIODS:
            entry = compile_trajectories(shape, True)
            loop = compile_trajectories(shape, False)
            for i in range(len(entry)):
                for chain in (entry[i], loop[i]):
                    for a,b in zip(chain,chain[1:]):
                        for derivative in range(3):
                            self.assert_vector_close(a.evaluate(a.duration,derivative),b.evaluate(0,derivative))
                for a,b in ((entry[i][-1],loop[i][0]),(loop[i][-1],loop[i][0])):
                    for derivative in range(3):
                        self.assert_vector_close(a.evaluate(a.duration,derivative),b.evaluate(0,derivative))
                self.assert_vector_close(entry[i][0].evaluate(0),targets(shape)[i])
                self.assert_vector_close(entry[i][0].evaluate(0,1),(0,0,0))
                self.assert_vector_close(entry[i][0].evaluate(0,2),(0,0,0))

    def test_spacing_and_height_along_polynomial_interiors(self):
        for shape in PERIODS:
            for entry in (False,True):
                paths = compile_trajectories(shape,entry)
                for piece in range(len(paths[0])):
                    for step in range(11):
                        points = [path[piece].evaluate(path[piece].duration*step/10) for path in paths]
                        self.assertGreaterEqual(minimum_distance(points),.52)
                        self.assertGreater(min(p[2] for p in points),.6)

    def test_heart_passes_middle_with_nonzero_velocity(self):
        for t in (0,PERIODS['heart']/2,PERIODS['heart']):
            self.assertGreater(max(math.dist(s[1],(0,0,0)) for s in motion('heart',t)),.5)

    def test_speed_scales_time_velocity_acceleration_without_changing_geometry(self):
        for shape in PERIODS:
            for speed in (.5,.75,1.25):
                for entry in (False,True):
                    paths=compile_trajectories(shape,entry,speed=speed)
                    self.assertAlmostEqual(sum(p.duration for p in paths[0]),PERIODS[shape]/speed)
                    for phase in range(17):
                        t=PERIODS[shape]*phase/16
                        for base,scaled in zip(motion(shape,t,entry),motion(shape,t/speed,entry,speed)):
                            for d in range(3):
                                self.assert_vector_close(scaled[d],tuple(v*speed**d for v in base[d]))

    def test_wave_has_no_whole_fleet_hover_at_sample_boundaries(self):
        for step in range(65):
            states = motion('sine',PERIODS['sine']*step/64)
            self.assertGreater(max(abs(s[1][2]) for s in states),1.0)

    def test_spiral_preserves_size_and_reverses_turn_smoothly(self):
        base=targets('spiral')[0]
        radius=math.hypot(base[0],base[2]-3.8)
        for fraction,scale in ((.25,1.),(.75,1.)):
            point=motion('spiral',PERIODS['spiral']*fraction)[0][0]
            self.assertAlmostEqual(math.hypot(point[0],point[2]-3.8)/radius,scale)
        for entry in (False,True):
            for step in range(1,64):
                t=PERIODS['spiral']*step/64;h=1e-4
                before=motion('spiral',t-h,entry)
                states=motion('spiral',t,entry)
                after=motion('spiral',t+h,entry)
                for a,b,c in zip(before,states,after):
                    for axis in (0,2):
                        self.assertAlmostEqual((c[0][axis]-a[0][axis])/(2*h),b[1][axis],places=6)
                        self.assertAlmostEqual((c[1][axis]-a[1][axis])/(2*h),b[2][axis],places=6)

    def test_moon_moves_between_full_and_half_without_changing_right_limb(self):
        full=motion('moon',0)
        half=motion('moon',PERIODS['moon']/2)
        self.assertGreater(max(abs(a[0][0]-b[0][0]) for a,b in zip(full,half)),2.)
        for a,b in zip(full,half):
            if a[0][0]>=-1e-8:self.assert_vector_close(a[0],b[0])
            else:self.assertAlmostEqual(b[0][0],0)


if __name__ == '__main__': unittest.main()
