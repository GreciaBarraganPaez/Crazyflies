"""Run offline: python3 -m unittest test_phase1.py -v"""
import unittest
from animations import (DRONES, HOME, ANIMATIONS, MIN_PLANNED_SEPARATION,
                        positions, planned_segment_distance, validate_geometry)
from gesture_bridge import SimulationController, parse_gesture


class FakeDrone:
    def __init__(self):
        self.commands = []
    def goTo(self, goal, yaw, duration):
        self.commands.append((goal, yaw, duration))


class FakeFleet:
    def __init__(self):
        self.crazyfliesByName = {d: FakeDrone() for d in DRONES}
        self.events = []
    def takeoff(self, targetHeight, duration):
        self.events.append(('takeoff', targetHeight, duration))
    def land(self, targetHeight, duration):
        self.events.append(('land', targetHeight, duration))


class FakeSwarm:
    def __init__(self):
        self.allcfs = FakeFleet()


class Phase1Tests(unittest.TestCase):
    def test_fleet_and_preflight(self):
        self.assertEqual(len(DRONES), 18)
        min_gap, _ = validate_geometry()
        self.assertGreaterEqual(min_gap, MIN_PLANNED_SEPARATION)

    def test_modes_move_and_loop(self):
        for name in ANIMATIONS:
            self.assertEqual(len(positions(name, 0)), 18)
            self.assertEqual(len(positions(name, 3.2)), 18)
            self.assertNotEqual(positions(name, 0), positions(name, 3.2))

    def test_parser(self):
        self.assertEqual(parse_gesture(b'PEACE\n'), 'peace')
        self.assertIsNone(parse_gesture(b'launch'))
        self.assertIsNone(parse_gesture(b'\xff'))

    def test_arm_takeoff_animation_switch_pause_land(self):
        swarm = FakeSwarm()
        ctrl = SimulationController(swarm)
        ctrl.handle('one', 100)
        self.assertFalse(swarm.allcfs.events)
        ctrl.arm(100)
        ctrl.handle('one', 100)
        self.assertEqual(swarm.allcfs.events[0][0], 'takeoff')
        ctrl.update(106)
        self.assertEqual(ctrl.state, 'ready')
        ctrl.handle('peace', 106)
        ctrl.update(106.3)
        self.assertEqual(ctrl.mode, 'heart')
        self.assertEqual(ctrl.state, 'animating')
        self.assertGreater(sum(len(c.commands) for c in swarm.allcfs.crazyfliesByName.values()), 0)
        ctrl.handle('three', 108)
        self.assertEqual(ctrl.state, 'staging')
        ctrl.update(119)
        self.assertEqual(ctrl.mode, 'wave')
        ctrl.handle('fist', 120)
        self.assertEqual(ctrl.state, 'ready')
        ctrl.handle('palm', 121)
        self.assertEqual(ctrl.state, 'staging')
        ctrl.update(131)
        self.assertEqual(ctrl.state, 'landing')
        self.assertEqual(swarm.allcfs.events[-1][0], 'land')
        ctrl.update(138)
        self.assertEqual(ctrl.state, 'grounded')
        self.assertFalse(ctrl.armed)

    def test_repeated_mode_does_not_restage(self):
        swarm = FakeSwarm()
        ctrl = SimulationController(swarm)
        ctrl.arm(100); ctrl.handle('one', 100)
        ctrl.update(106); ctrl.handle('ok', 106); ctrl.update(106.3)
        before = sum(len(c.commands) for c in swarm.allcfs.crazyfliesByName.values())
        ctrl.handle('ok', 107)
        after = sum(len(c.commands) for c in swarm.allcfs.crazyfliesByName.values())
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
