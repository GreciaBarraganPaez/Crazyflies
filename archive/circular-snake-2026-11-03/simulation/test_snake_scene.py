import math
import unittest
from dataclasses import replace
from scenes.snake import SnakeScene, arrange_plan, return_plan, collect_plan, loop_plan, validate_limit, PICKUP
from scenes.trajectories import rest, evaluate
from static_shapes import COUNT, HOME, minimum_distance


class SnakeSceneTests(unittest.TestCase):
    def test_body_tracks_head_path_with_time_delay_and_scales_to_19(self):
        for count in (3,5,19):
            for direction in (-1,1):
                scene=SnakeScene(count,count,direction)
                plan=loop_plan(scene,0)
                self.assertGreaterEqual(plan.bound,.52)
                for step in range(97):
                    when=24*step/96
                    points=tuple(s[0] for s in scene.states(when))
                    self.assertGreaterEqual(minimum_distance(points),.52)
                    self.assertGreater(min(p[2] for p in points),.6)
                delay=.3/(2*math.pi/24)
                self.assertLess(math.dist(scene.state(0,1-delay)[0],scene.state(1,1)[0]),1e-10)

    def test_entry_turn_and_return_have_certified_clearance_and_c2_joins(self):
        start=tuple(rest(p) for p in HOME)
        entry=arrange_plan(start,0,SnakeScene())
        self.assertGreaterEqual(entry.bound,.52)
        for source,target in zip(start,entry.paths):
            for d in range(3):self.assertLess(math.dist(source[d],target[0].evaluate(0,d)),1e-8)
        for count in (3,19):
            for direction in (-1,1):
                scene=SnakeScene(count,19,direction)
                for phase in range(8):
                    now=24*phase/8
                    source=scene.states(now)
                    for plan in (return_plan(source),arrange_plan(source,now,replace(scene,direction=-direction))):
                        self.assertGreaterEqual(plan.bound,.52)
                        for path in plan.paths:
                            for a,b in zip(path,path[1:]):
                                for d in range(3):self.assertLess(math.dist(a.evaluate(a.duration,d),b.evaluate(0,d)),1e-7)

    def test_collection_requires_proximity_and_increases_chain_without_contact(self):
        for members in (3,18):
            scene=SnakeScene(members,19)
            staged=collect_plan(scene.states(0),0,scene)
            scene=staged.after
            self.assertEqual(scene.members,members)
            self.assertEqual(scene.pickup,members)
            self.assertFalse(scene.can_collect(12))
            with self.assertRaises(ValueError):collect_plan(scene.states(12),12,scene,True)
            self.assertTrue(scene.can_collect(24))
            self.assertGreater(math.dist(scene.state(0,24)[0],PICKUP),.52)
            joined=collect_plan(scene.states(24),24,scene,True)
            self.assertEqual(joined.after.members,members+1)
            self.assertIsNone(joined.after.pickup)
            self.assertGreaterEqual(joined.bound,.52)
            for path,goal in zip(joined.paths,joined.after.states(24+joined.duration)):
                for d in range(3):self.assertLess(math.dist(path[-1].evaluate(path[-1].duration,d),goal[d]),1e-7)

    def test_limits_and_roles_are_explicit(self):
        for bad in (2,20,3.5,True,None):
            with self.assertRaises(ValueError):validate_limit(bad)
        scene=SnakeScene()
        self.assertEqual(scene.roles().count('head'),1)
        self.assertEqual(scene.roles().count('body'),2)
        self.assertEqual(scene.roles().count('waiting'),2)
        self.assertEqual(scene.roles().count('parked'),14)
        with self.assertRaises(ValueError):collect_plan(SnakeScene(3,3).states(0),0,SnakeScene(3,3))
