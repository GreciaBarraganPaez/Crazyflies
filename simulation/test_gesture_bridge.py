"""Tests for the pure command parser, timing gate, and safe simulated state logic."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from gesture_bridge import parse_gesture, SimulationController
from formations import DRONES, FLIGHT_HEIGHT, positions, min_horizontal_separation, check_geometry
from gesture_gate import StableGestureGate


class FakeCF:
    def __init__(self): self.targets = []
    def goTo(self, goal, yaw, duration): self.targets.append((goal, yaw, duration))


class FakeAll:
    def __init__(self):
        self.crazyfliesByName = {name: FakeCF() for name in DRONES}
        self.events = []
    def takeoff(self, targetHeight, duration): self.events.append(('takeoff', targetHeight))
    def land(self, targetHeight, duration): self.events.append(('land', targetHeight))


class FakeSwarm:
    def __init__(self): self.allcfs = FakeAll()


class TestProtocol(unittest.TestCase):
    def test_parser(self):
        self.assertEqual(parse_gesture(b'PEACE\n'), 'peace')
        self.assertEqual(parse_gesture(b'palm'), 'palm')
        self.assertIsNone(parse_gesture(b'execute'))
        self.assertIsNone(parse_gesture(b'\xff'))
        self.assertIsNone(parse_gesture(b'p' * 33))

    def test_gate(self):
        gate = StableGestureGate(min_hold=0.7, cooldown=1.5)
        self.assertIsNone(gate.accept('peace', 1.0))
        self.assertIsNone(gate.accept('peace', 1.6))
        self.assertEqual(gate.accept('peace', 1.8), 'peace')
        self.assertIsNone(gate.accept('peace', 3.0))
        self.assertIsNone(gate.accept('no hand', 3.1))
        self.assertIsNone(gate.accept('peace', 3.2))
        self.assertEqual(gate.accept('peace', 3.95), 'peace')

    def test_seven_drone_geometry(self):
        self.assertEqual(len(DRONES), 7)
        self.assertEqual(len(positions("circle")), 7)
        self.assertGreaterEqual(min_horizontal_separation(positions("circle")), 0.3)
        check_geometry()

    def test_arm_required_and_land_disarms(self):
        swarm = FakeSwarm()
        controller = SimulationController(swarm)
        controller.handle('one')
        self.assertEqual(swarm.allcfs.events, [])
        controller.arm()
        controller.handle('one')
        self.assertEqual(swarm.allcfs.events[0], ('takeoff', FLIGHT_HEIGHT))
        controller.state = 'airborne'  # simulate elapsed takeoff interval
        controller.busy_until = 0
        controller.handle('peace')
        self.assertEqual(len(swarm.allcfs.crazyfliesByName['cf231'].targets), 1)
        controller.handle('palm')
        self.assertEqual(swarm.allcfs.events[-1][0], 'land')
        self.assertFalse(controller.armed)


if __name__ == '__main__':
    unittest.main()
