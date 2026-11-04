import math
import sys
from pathlib import Path
import unittest
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from app.hand_steering import HandSteering
from scenes.play_snake import PlayerScene,DRONES,HOME,TICK,world,step_plan,enter_plan
from scenes.trajectories import evaluate,rest
from play_snake_controller import PlayerController
from test_static_shapes import FakeSwarm
from static_shapes import minimum_distance
from gesture_bridge import parse_gesture


def scripted_direction(scene):
    """A deliberate test-only route collecting the five fixed apples."""
    if scene.score==0:return 'right'
    if scene.score==1:return 'left' if scene.trail[-1][1]>=6 else 'up'
    if scene.score<3:return 'left'
    if scene.score==3:return 'right' if scene.trail[-1][1]<=1 else 'down'
    return 'right'


class PlaySnakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=[];scene=PlayerScene()
        for _ in range(80):
            plan=step_plan(scene,scripted_direction(scene))
            if plan.after is None:raise AssertionError('Test path unexpectedly returned to grid')
            cls.cases.append((scene,plan));scene=plan.after
            if not scene.foods:break
        else:raise AssertionError('Test route failed to collect all apples')

    def test_eight_actual_drones_and_one_snake(self):
        scene=PlayerScene()
        self.assertEqual(len(DRONES),8);self.assertEqual(len(HOME),8)
        self.assertEqual(len(scene.foods),5);self.assertEqual(scene.members,3)
        for old,plan in self.cases:
            self.assertEqual(len(plan.after.snakes),1)
            self.assertEqual(plan.after.roles().count('head'),1)
            self.assertEqual(set(plan.after.actors)|{i for i,c in plan.after.foods},set(range(8)))

    def test_apple_becomes_head_when_old_head_reaches_pickup_cell(self):
        for scene,plan in self.cases:
            if plan.kind!='launch':continue
            apple=next(i for i,cell in scene.foods if cell==scene.trail[-1])
            self.assertEqual(plan.after.actors,(apple,)+scene.actors)
            old_head=evaluate(plan.paths[scene.actors[0]],plan.duration)[0]
            self.assertLess(math.dist(old_head,world(dict(scene.foods)[apple])),1e-7)
        self.assertEqual(self.cases[-1][1].after.members,8)

    def test_full_paths_have_clearance_and_continuous_boundaries(self):
        for scene,plan in self.cases:
            self.assertGreaterEqual(plan.bound,.52)
            before,after=scene.states(),plan.after.states()
            for i,path in enumerate(plan.paths):
                for d in range(3):
                    self.assertLess(math.dist(path[0].evaluate(0,d),before[i][d]),1e-7)
                    self.assertLess(math.dist(evaluate(path,plan.duration)[d],after[i][d]),1e-6)
            for u in (0,.25,.5,.75,1):
                poses=[evaluate(path,plan.duration*u)[0] for path in plan.paths]
                self.assertGreaterEqual(minimum_distance(poses),.52)
                for i in scene.actors:self.assertGreater(math.dist(evaluate(plan.paths[i],plan.duration*u)[1],(0,0,0)),.3)

    def test_turns_preserve_committed_source_and_reverse_is_ignored(self):
        scene=PlayerScene()
        straight,up,reverse=(step_plan(scene,d) for d in ('right','up','left'))
        self.assertEqual(straight.after.trail,reverse.after.trail)
        self.assertNotEqual(straight.after.trail,up.after.trail)
        for i in range(8):
            for d in range(3):self.assertLess(math.dist(straight.paths[i][0].evaluate(0,d),up.paths[i][0].evaluate(0,d)),1e-7)

    def test_wall_returns_through_certified_grid_exit(self):
        scene=PlayerScene()
        for _ in range(15):
            plan=step_plan(scene,'right')
            if plan.after is None:break
            scene=plan.after
        else:self.fail('No exit at wall')
        self.assertEqual(plan.kind,'grid');self.assertGreaterEqual(plan.bound,.52)
        for path,point in zip(plan.paths,HOME):self.assertLess(math.dist(evaluate(path,plan.duration)[0],point),1e-7)

    def test_entry_is_certified_for_eight_drone_grid(self):
        self.assertGreaterEqual(enter_plan(tuple(rest(p) for p in HOME)).bound,.52)


class SteeringTests(unittest.TestCase):
    def test_four_directions_dwell_repeat_and_neutral(self):
        for x,y,direction in ((.1,.5,'left'),(.9,.5,'right'),(.5,.1,'up'),(.5,.9,'down')):
            gate=HandSteering()
            self.assertIsNone(gate.update(x,y,0.))
            self.assertEqual(gate.update(x,y,.16),direction)
            self.assertIsNone(gate.update(x,y,.2))
            self.assertEqual(gate.update(x,y,.6),direction)
            self.assertIsNone(gate.update(.5,.5,.7))

    def test_tracking_loss_and_nonpointing_cancel_direction(self):
        gate=HandSteering();gate.update(.1,.5,0.)
        self.assertIsNone(gate.update(.1,.5,.2,pointing=False))
        self.assertIsNone(gate.update(None,None,.4))
        self.assertIsNone(gate.update(float('nan'),.5,.5))
        self.assertIsNone(gate.update(.1,.5,.6))
        self.assertEqual(gate.update(.1,.5,.8),'left')

    def test_directions_only_accepted_in_player_mode(self):
        self.assertIsNone(parse_gesture(b'left'))
        self.assertEqual(parse_gesture(b'left',set(PlayerController.INPUT_ACTIONS)),'left')

    def test_manual_takeoff_and_steering_are_lifecycle_gated(self):
        swarm=FakeSwarm();swarm.allcfs.crazyfliesByName={n:swarm.allcfs.crazyfliesByName[n] for n in DRONES}
        c=PlayerController(swarm,lambda:True);sent=[];c.send_command=sent.append
        c.handle('left');c.handle('one');self.assertEqual(swarm.allcfs.events,[])
        c.arm();c.handle('one');c.update(c.due+.1);self.assertEqual(c.state,'ready')
        c.handle('peace');c.handle('up')
        self.assertEqual(sent,[dict(action='start',limit=8,seed=31),dict(action='turn',direction='up')])
        c.handle('palm');c.handle('down');self.assertEqual(sent[-1],dict(action='return'))
