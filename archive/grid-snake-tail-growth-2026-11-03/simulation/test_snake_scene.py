import math
import unittest
from scenes.snake import (SnakeScene,CYCLE,INDEX,WIDTH,HEIGHT,CELL,world,delta,adjacent,
                          arrange_plan,return_plan,step_plan,validate_limit)
from scenes.trajectories import rest,evaluate
from static_shapes import HOME,minimum_distance


class SnakeSceneTests(unittest.TestCase):
    def test_board_cycle_visits_every_cell_with_orthogonal_edges(self):
        self.assertEqual(len(set(CYCLE)),WIDTH*HEIGHT)
        for a,b in zip(CYCLE,CYCLE[1:]+CYCLE[:1]):self.assertTrue(adjacent(a,b))

    def test_autonomous_policy_grows_without_reverse_wall_or_body_collisions(self):
        seen_turns=set()
        for seed in range(40):
            scene=SnakeScene(seed=seed).spawn_food()
            for step in range(1000):
                after=scene.advance()
                move=delta(after.body[0],scene.body[0])
                dot=sum(a*b for a,b in zip(move,scene.heading))
                self.assertIn(dot,(0,1))
                seen_turns.add(scene.heading[0]*move[1]-scene.heading[1]*move[0])
                self.assertEqual(after.body[1:],scene.body if after.members>scene.members else scene.body[:-1])
                self.assertEqual(len(set(after.body)),after.members)
                self.assertTrue(all(c in INDEX for c in after.body))
                self.assertNotIn(after.food,after.body)
                scene=after
                if scene.members==19:break
            self.assertEqual(scene.members,19,seed)
            for _ in range(40):scene=scene.advance()
        self.assertEqual(seen_turns,{-1,0,1})

    def test_exact_grid_paths_merge_straights_and_keep_corner_rest_states(self):
        scene=SnakeScene().spawn_food();merged=False
        for _ in range(18):
            plan=step_plan(scene);after=plan.after
            merged|=plan.cells>1
            self.assertGreaterEqual(plan.bound,.52)
            for i in range(scene.members):
                a,b=world(scene.body[i]),world(after.body[i])
                fixed=[k for k in range(3) if abs(a[k]-b[k])<1e-9]
                self.assertGreaterEqual(len(fixed),2)
                for piece in plan.paths[i]:
                    for t in (0,piece.duration*.5,piece.duration):
                        p=piece.evaluate(t)
                        for axis in fixed:self.assertAlmostEqual(p[axis],a[axis],places=8)
                for derivative in (1,2):
                    self.assertLess(math.dist(plan.paths[i][0].evaluate(0,derivative),(0,0,0)),1e-8)
                    self.assertLess(math.dist(plan.paths[i][-1].evaluate(plan.paths[i][-1].duration,derivative),(0,0,0)),1e-7)
            scene=after
        self.assertTrue(merged)

    def test_food_drone_leaves_cell_and_joins_tail_without_contact(self):
        for target in (3,18):
            scene=SnakeScene().spawn_food()
            while not (scene.members==target and scene.next_cell()==scene.food):scene=scene.advance()
            plan=step_plan(scene)
            self.assertEqual(plan.kind,'eat')
            self.assertEqual(plan.after.members,scene.members+1)
            self.assertEqual(plan.after.body[-1],scene.body[-1])
            self.assertGreaterEqual(plan.bound,.52)
            for f in range(65):
                points=[evaluate(p,plan.duration*f/64)[0] for p in plan.paths]
                self.assertGreaterEqual(minimum_distance(points),.52)
            self.assertEqual(plan.after.states()[scene.members][0],world(scene.body[-1]))

    def test_entry_return_and_limits(self):
        scene=SnakeScene().spawn_food()
        plan=arrange_plan(tuple(rest(p) for p in HOME),scene)
        self.assertGreaterEqual(plan.bound,.52)
        self.assertGreaterEqual(return_plan(scene.states()).bound,.52)
        self.assertAlmostEqual(return_plan(tuple(rest(p) for p in HOME)).duration,.2)
        for bad in (2,20,3.5,True,None):
            with self.assertRaises(ValueError):validate_limit(bad)
        self.assertEqual(scene.roles().count('food'),1)
        self.assertEqual(scene.roles().count('body'),2)
        self.assertIsNone(SnakeScene(limit=3).spawn_food().food)
