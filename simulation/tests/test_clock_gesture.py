import unittest
from types import SimpleNamespace

from app.clock_gesture import detects_wrist_point

def hand(wrist, index_tip, other_tips):
    points = [SimpleNamespace(x=wrist[0], y=wrist[1]) for _ in range(21)]
    points[0] = SimpleNamespace(x=wrist[0], y=wrist[1])
    points[9] = SimpleNamespace(x=wrist[0], y=wrist[1] + .1)
    points[8] = SimpleNamespace(x=index_tip[0], y=index_tip[1])
    for idx, point in zip((12, 16, 20), other_tips):
        points[idx] = SimpleNamespace(x=point[0], y=point[1])
    return points

class ClockGestureTests(unittest.TestCase):
    def test_requires_two_hands(self):
        self.assertFalse(detects_wrist_point([]))

    def test_detects_index_pointing_at_closed_wrist(self):
        target = hand((.5, .5), (.5, .5), [(.52, .52)] * 3)
        pointer = hand((.2, .5), (.5, .5), [(.2, .51)] * 3)
        self.assertTrue(detects_wrist_point([target, pointer]))

    def test_does_not_trigger_for_two_closed_hands(self):
        a = hand((.5, .5), (.55, .5), [(.52, .52)] * 3)
        b = hand((.2, .5), (.25, .5), [(.22, .52)] * 3)
        self.assertFalse(detects_wrist_point([a, b]))
