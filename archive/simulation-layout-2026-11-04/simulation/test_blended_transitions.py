import itertools
import math
import unittest
import numpy as np
from blended_transitions import compile_blend, certify_relative
from continuous_trajectories import motion, PERIODS
from static_shapes import targets, minimum_distance


class BlendTests(unittest.TestCase):
    def test_whole_curve_certificate_rejects_an_interior_collision(self):
        crossing=np.zeros((1,6,3));crossing[0,:,0]=np.linspace(1,-1,6)
        self.assertFalse(certify_relative(crossing,.52)[0][0])
        crossing[0,:,2]=.8
        self.assertTrue(certify_relative(crossing,.52)[0][0])

    def test_position_velocity_acceleration_are_joined_without_hover(self):
        start=motion('heart',.7)
        plan=compile_blend(start,'sine')
        end=motion('sine',0)
        self.assertGreaterEqual(plan.clearance_bound,.52)
        for i,path in enumerate(plan.paths):
            for d in range(3):
                self.assertLess(math.dist(path[0].evaluate(0,d),start[i][d]),1e-7)
                self.assertLess(math.dist(path[-1].evaluate(path[-1].duration,d),end[i][d]),1e-7)
                for a,b in zip(path,path[1:]):
                    self.assertLess(math.dist(a.evaluate(a.duration,d),b.evaluate(0,d)),1e-7)
        for k in (0,1):
            self.assertGreater(max(math.dist(p[k].evaluate(p[k].duration,1),(0,0,0)) for p in plan.paths),.05)
        for k in range(3):
            for step in range(51):
                points=[p[k].evaluate(p[k].duration*step/50) for p in plan.paths]
                self.assertGreaterEqual(minimum_distance(points),.52)

    def test_all_animation_phases_and_static_shape_pairs(self):
        for source in PERIODS:
            for entry in (False,True):
                for phase in range(16):
                    start=motion(source,PERIODS[source]*phase/16,entry)
                    for target in PERIODS:
                        if target==source: continue
                        with self.subTest(source=source,entry=entry,phase=phase,target=target):
                            plan=compile_blend(start,target)
                            self.assertGreaterEqual(plan.clearance_bound,.52)
        for source,target in itertools.permutations(PERIODS,2):
            start=tuple((p,(0.,)*3,(0.,)*3) for p in targets(source))
            self.assertGreaterEqual(compile_blend(start,target).clearance_bound,.52)

    def test_speed_extremes_preserve_full_curve_clearance_and_target_derivatives(self):
        for speed in (.5,1.25):
            for source,target in itertools.permutations(PERIODS,2):
                for entry in (False,True):
                    for phase in range(32):
                        with self.subTest(speed=speed,source=source,target=target,entry=entry,phase=phase):
                            start=motion(source,PERIODS[source]/speed*phase/32,entry,speed)
                            plan=compile_blend(start,target,speed)
                            self.assertGreaterEqual(plan.clearance_bound,.52)
                            for path,goal in zip(plan.paths,motion(target,0,speed=speed)):
                                for d in range(3):
                                    self.assertLess(math.dist(path[-1].evaluate(path[-1].duration,d),goal[d]),1e-7)


if __name__ == '__main__':unittest.main()
