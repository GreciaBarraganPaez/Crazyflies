"""Offline tests: python -m unittest simulation.tests.test_static_shapes -v"""
import math
import unittest
from simulation.core.static_shapes import (COUNT, DRONES, HOME, SHAPES, FLIGHT_HEIGHT,
                           MIN_PLANNED_SEPARATION, ground_positions,
                           minimum_distance, planned_segment_distance,
                           validate_geometry)
from simulation.controllers.gesture_bridge import (SimulationController, parse_gesture,
                            GRID_MOVE_SEC, SHAPE_MOVE_SEC, MARGIN_SEC,
                            TAKEOFF_SEC, LAND_SEC)

from simulation.tests.helpers import FakeSwarm

class Tests(unittest.TestCase):
    def test_symmetric_odd_grid(self):
        self.assertEqual(COUNT, 19)
        self.assertEqual(len(HOME), 19)
        rows={y:sorted(x for x,yy,z in HOME if y==yy) for y in {p[1] for p in HOME}}
        self.assertEqual(sorted(map(len,rows.values())),[6,6,7])
        for xs in rows.values():
            self.assertEqual(xs,[-x for x in xs[::-1]])
        self.assertEqual(sum(x==0 and y==0 for x,y,z in HOME),1)

    def test_front_plane_shapes(self):
        self.assertEqual(set(validate_geometry()),{'grid','heart','sine','spiral','moon','helix','clock'})
        for name,t in SHAPES.items():
            with self.subTest(name=name):
                self.assertEqual(len(t),COUNT)
                if name!='helix':self.assertTrue(all(y==0 for x,y,z in t))
                else:self.assertGreater(max(y for x,y,z in t)-min(y for x,y,z in t),2.)
                self.assertGreater(max(z for x,y,z in t)-min(z for x,y,z in t),2.0)
                self.assertGreaterEqual(minimum_distance(t), MIN_PLANNED_SEPARATION)
                self.assertGreaterEqual(planned_segment_distance(HOME,t),MIN_PLANNED_SEPARATION)
                self.assertGreaterEqual(planned_segment_distance(t,HOME),MIN_PLANNED_SEPARATION)

    def test_heart_bilateral_symmetry(self):
        shape=sorted((round(x,4),round(z,4)) for x,y,z in SHAPES['heart'])
        for x,z in shape:
            self.assertIn((-x,z),shape)

    def test_grid_lands_vertically(self):
        for h,g in zip(HOME,ground_positions()):
            self.assertEqual((h[0],h[1]),(g[0],g[1]))
            self.assertEqual(g[2],0.)

    def test_parse(self):
        self.assertEqual(parse_gesture(b'PEACE'),'peace')
        self.assertIsNone(parse_gesture(b'other'))

    def _airborne_heart(self):
        fleet=FakeSwarm(); ctrl=SimulationController(fleet)
        ctrl.arm(0)
        ctrl.handle('one',0)
        ctrl.update(TAKEOFF_SEC+MARGIN_SEC+.01)
        ctrl.handle('peace',TAKEOFF_SEC+MARGIN_SEC+.02)
        t=TAKEOFF_SEC+MARGIN_SEC+.02+SHAPE_MOVE_SEC+MARGIN_SEC+.02
        ctrl.update(t)
        self.assertEqual(ctrl.state,'showing')
        return ctrl,fleet,t

    def test_landing_first_returns_to_grid(self):
        ctrl,fleet,t=self._airborne_heart()
        ctrl.handle('palm',t+.01)
        self.assertEqual(ctrl.state,'to_grid')
        self.assertFalse(any(event[0]=='land' for event in fleet.allcfs.events))
        for name,drone in ctrl.by_name.items():
            self.assertEqual(drone.commands[-1][0],HOME[DRONES.index(name)])
        ctrl.update(t+.01+GRID_MOVE_SEC+MARGIN_SEC-.01)
        self.assertFalse(any(event[0]=='land' for event in fleet.allcfs.events))
        ctrl.update(t+.01+GRID_MOVE_SEC+MARGIN_SEC+.02)
        self.assertEqual(ctrl.state,'landing')
        self.assertEqual(fleet.allcfs.events[-1][0],'land')
        self.assertEqual(sum(e[0]=='goTo' for e in fleet.allcfs.events),COUNT*2)

    def test_switch_returns_to_grid_before_next_shape(self):
        ctrl,fleet,t=self._airborne_heart()
        ctrl.handle('three',t+.01)
        self.assertEqual(ctrl.state,'to_grid')
        ctrl.update(t+.01+GRID_MOVE_SEC+MARGIN_SEC+.02)
        self.assertEqual(ctrl.state,'to_shape')
        self.assertEqual(ctrl.current_goals,SHAPES['sine'])

    def test_queued_landing_during_takeoff(self):
        ctrl=SimulationController(FakeSwarm())
        ctrl.arm(0);ctrl.handle('one',0)
        ctrl.handle('palm',1)
        self.assertEqual(ctrl.queued_gesture,'palm')
        ctrl.update(TAKEOFF_SEC+MARGIN_SEC+.01)
        self.assertEqual(ctrl.state,'to_grid')
        ctrl.update(TAKEOFF_SEC+MARGIN_SEC+.4)
        self.assertEqual(ctrl.state,'landing')

class LandingFeedbackTests(unittest.TestCase):
    _airborne_heart = Tests._airborne_heart
    def test_landing_waits_for_measured_grid_arrival(self):
        ctrl, fleet, t = self._airborne_heart()
        arrived = [False]
        ctrl.grid_arrived = lambda: arrived[0]
        ctrl.handle('palm', t + .01)
        ctrl.update(t + GRID_MOVE_SEC + MARGIN_SEC + 10)
        self.assertEqual(ctrl.state, 'to_grid')
        self.assertFalse(any(e[0] == 'land' for e in fleet.allcfs.events))
        ctrl.handle('three', t + GRID_MOVE_SEC + MARGIN_SEC + 11)
        arrived[0] = True
        ctrl.update(t + GRID_MOVE_SEC + MARGIN_SEC + 12)
        self.assertEqual(ctrl.state, 'landing')
        self.assertEqual(fleet.allcfs.events[-1][0], 'land')

    def test_uses_simulation_clock_when_wall_time_runs_ahead(self):
        swarm = FakeSwarm()
        class Clock:
            now = 0.0
            def time(self): return self.now
        swarm.timeHelper = Clock()
        ctrl = SimulationController(swarm)
        ctrl.arm()
        ctrl.handle('one')
        ctrl.update()
        self.assertEqual(ctrl.state, 'taking_off')
        swarm.timeHelper.now = TAKEOFF_SEC + MARGIN_SEC + .01
        ctrl.update()
        self.assertEqual(ctrl.state, 'ready')

if __name__ == '__main__': unittest.main()
