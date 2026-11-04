import math
import unittest
from scenes.snake import (SnakeScene,CYCLE,WIDTH,HEIGHT,TICK,MAX_MEMBERS,BORDER_IDS,
    world,route,border_points,arrange_plan,return_plan,step_plan,validate_limit,delta)
from scenes.snake_routes import winding_cycle
from scenes.trajectories import rest,evaluate
from static_shapes import HOME,COUNT,minimum_distance


class SnakeSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=[];cls.finals=[]
        for seed in (1,31):
            scene=SnakeScene(seed=seed).spawn_food()
            for _ in range(160):
                plan=step_plan(scene);cls.cases.append((scene,plan));scene=plan.after
                if scene.members==MAX_MEMBERS and len(scene.snakes)==2:break
            else:raise AssertionError('Both snakes did not finish collecting')
            cls.finals.append(scene)

    def test_all_drones_have_visible_roles_and_twelve_apples_at_start(self):
        scene=SnakeScene().spawn_food()
        self.assertEqual(scene.members,3);self.assertEqual(len(scene.foods),12)
        self.assertEqual(scene.roles().count('border'),4);self.assertEqual(scene.roles().count('parked'),0)
        self.assertEqual(len(scene.states()),COUNT)
        self.assertGreaterEqual(minimum_distance(tuple(s[0] for s in scene.states())),.52)

    def test_seeded_routes_are_winding_unique_grid_cycles(self):
        courses=[winding_cycle(WIDTH,HEIGHT,seed) for seed in (1,31,42)]
        self.assertEqual(len(set(courses)),3)
        for course in courses:
            self.assertEqual(len(set(course)),WIDTH*HEIGHT)
            turns=0
            for i,c in enumerate(course):
                nxt=course[(i+1)%len(course)]
                self.assertEqual(abs(c[0]-nxt[0])+abs(c[1]-nxt[1]),1)
                turns+=delta(c,course[i-1])!=delta(nxt,c)
            self.assertGreaterEqual(turns,30)

    def test_route_is_c2_and_never_stops_at_corners(self):
        for course in (CYCLE,winding_cycle(WIDTH,HEIGHT,31),winding_cycle(4,HEIGHT,132)):
            for k in range(len(course)):
                before,after=route(k-1e-7,course=course),route(k+1e-7,course=course)
                for d in range(3):self.assertLess(math.dist(before[d],after[d]),2e-5)
            for k in range(len(course)*8):
                p,v,a=route(k/8,course=course)
                self.assertGreater(math.dist(v,(0,0,0)),.3)

    def test_eaten_drone_becomes_its_own_snakes_head(self):
        for scene,plan in self.cases:
            if plan.kind=='split':continue
            for old,new,action in zip(scene.snakes,plan.after.snakes,plan.actions):
                if action!='eat':continue
                self.assertEqual(new.actors,(old.launched,)+old.actors)
                self.assertNotIn(old.launched,dict(new.foods))
                self.assertLess(math.dist(evaluate(plan.paths[old.launched],plan.duration)[0],
                                          route(new.head,course=new.course)[0]),1e-7)
        for final in self.finals:
            self.assertEqual(final.members,15);self.assertFalse(final.foods)
            self.assertEqual(sorted(len(s.actors) for s in final.snakes),[7,8])

    def test_handoff_waits_for_original_apple_cell(self):
        for scene,plan in self.cases:
            if plan.kind=='split':continue
            for old,new,action in zip(scene.snakes,plan.after.snakes,plan.actions):
                if action=='launch':
                    actor,phase=old.foods[0]
                    self.assertEqual(old.head,phase-1);self.assertEqual(new.head,phase)
                    self.assertEqual(plan.after.roles()[actor],'food')
                    self.assertLess(math.dist(evaluate(plan.paths[old.actors[0]],plan.duration)[0],
                                              world(old.course[phase%len(old.course)])),1e-7)
                elif action=='eat':self.assertEqual(old.head,dict(old.foods)[old.launched])

    def test_split_preserves_identities_and_separates_regions(self):
        for scene,plan in self.cases:
            if plan.kind!='split':continue
            self.assertEqual(scene.members,9);self.assertEqual(len(plan.after.snakes),2)
            self.assertEqual(scene.actors,plan.after.actors)
            self.assertEqual(set(scene.foods[i][0] for i in range(len(scene.foods))),
                             set(i for i,_ in plan.after.foods))
            left,right=plan.after.snakes
            self.assertTrue(all(x<=3 for x,y in left.course))
            self.assertTrue(all(x>=8 for x,y in right.course))
            self.assertEqual(plan.after.roles().count('head'),1)
            self.assertEqual(plan.after.roles().count('head2'),1)

    def test_continuous_boundaries_and_body_speed(self):
        for scene,plan in self.cases:
            start,end=scene.states(),plan.after.states()
            for i,path in enumerate(plan.paths):
                for d in range(3):
                    self.assertLess(math.dist(path[0].evaluate(0,d),start[i][d]),1e-7)
                    self.assertLess(math.dist(path[-1].evaluate(path[-1].duration,d),end[i][d]),1e-6)
            if plan.kind=='split':continue
            for fraction in (0,.2,.5,.8,1):
                for i in plan.after.actors:
                    self.assertGreater(math.dist(evaluate(plan.paths[i],plan.duration*fraction)[1],(0,0,0)),.3)

    def test_clearance_and_static_border_through_all_programs(self):
        for scene,plan in self.cases:
            self.assertGreaterEqual(plan.bound,.52)
            for fraction in (0,.25,.5,.75,1):
                points=[evaluate(p,plan.duration*fraction)[0] for p in plan.paths]
                self.assertGreaterEqual(minimum_distance(points),.52)
                for i,p in zip(BORDER_IDS,border_points()):self.assertLess(math.dist(points[i],p),1e-8)

    def test_entry_exit_and_small_counts(self):
        scene=SnakeScene().spawn_food()
        self.assertGreaterEqual(arrange_plan(tuple(rest(p) for p in HOME),scene).bound,.52)
        self.assertGreaterEqual(return_plan(self.finals[-1].states()).bound,.52)
        for limit in (3,8):
            small=SnakeScene(limit=limit).spawn_food()
            for _ in range(55):small=step_plan(small).after
            self.assertEqual(len(small.snakes),1);self.assertEqual(small.members,limit)
        for bad in (2,16,19,True,None):
            with self.assertRaises(ValueError):validate_limit(bad)
