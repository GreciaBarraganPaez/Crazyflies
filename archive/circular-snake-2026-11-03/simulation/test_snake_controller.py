import json
import unittest
from types import SimpleNamespace
from snake_controller import SnakeController
from test_static_shapes import FakeSwarm


class SnakeControllerTests(unittest.TestCase):
    def controller(self):
        swarm=FakeSwarm();ctrl=SnakeController(swarm,lambda:True)
        ctrl.clock=lambda:0.
        sent=[];ctrl.send_command=sent.append
        return ctrl,swarm,sent

    def test_start_preserves_manual_arming_and_takeoff(self):
        c,s,sent=self.controller();c.keyboard_command('snake')
        self.assertEqual(sent,[])
        c.handle('one');self.assertEqual(s.allcfs.events,[])
        c.arm();c.handle('one');c.update(c.due+.1)
        self.assertEqual(c.state,'ready')
        c.handle('peace')
        self.assertEqual(sent,[dict(action='start',direction=-1,limit=5)])

    def test_palm_upgrades_grid_return_and_grid_feedback_gates_landing(self):
        c,s,sent=self.controller();c.state='snake'
        c.handle('fist');c.handle('palm');c.handle('ok')
        self.assertEqual(sent,[dict(action='return')])
        self.assertTrue(c.land_after_grid)
        c.receive_status(SimpleNamespace(data=json.dumps(dict(event='grid',members=0))))
        c.grid_arrived=lambda:False;c.update(1.)
        self.assertEqual(c.state,'to_grid')
        self.assertEqual(s.allcfs.events,[])
        c.grid_arrived=lambda:True;c.update(1.1)
        self.assertEqual(c.state,'landing')
        self.assertFalse(c.armed)

    def test_collection_rejection_does_not_cancel_pending_landing(self):
        c,_,_=self.controller();c.state='snake';c.land()
        c.receive_status(SimpleNamespace(data=json.dumps(dict(event='rejected',action='stage',reason='busy'))))
        self.assertTrue(c.returning)
        self.assertTrue(c.land_after_grid)

    def test_direction_gestures_and_count_configuration(self):
        c,_,sent=self.controller();c.keyboard_command('count 19')
        self.assertEqual(c.limit,19)
        c.state='snake';c.handle('three')
        self.assertEqual(sent[-1],dict(action='turn',direction=1,limit=19))
        c.keyboard_command('count 3');self.assertEqual(c.limit,19)
        c.handle('ok');self.assertEqual(sent[-1],dict(action='collect'))

    def test_landing_queued_during_takeoff_has_priority(self):
        c,_,sent=self.controller();c.arm();c.handle('one')
        c.handle('palm');c.handle('peace')
        self.assertEqual(c.queued_gesture,'palm')
        c.update(c.due+.1)
        self.assertEqual(c.state,'to_grid')
        self.assertTrue(c.land_after_grid)
        self.assertEqual(sent,[])

    def test_grid_queue_starts_snake_not_a_formation(self):
        c,s,sent=self.controller();c.state='to_grid';c.due=1.
        c.handle('three',.1);c.update(1.1)
        self.assertEqual(sent,[dict(action='start',direction=1,limit=5)])
        self.assertEqual(s.allcfs.events,[])

    def test_unsupported_formation_and_premature_collection_are_ignored(self):
        c,s,sent=self.controller();c.state='ready'
        c.handle('moon');c.handle('ok')
        self.assertEqual(c.state,'ready')
        self.assertEqual(s.allcfs.events,[])
        self.assertEqual(sent,[])
