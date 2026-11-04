"""Keep the sender gate/protocol coverage from the retired seven-drone tests."""
import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from gesture_gate import StableGestureGate
from gesture_bridge import parse_gesture


class GestureGateTests(unittest.TestCase):
    def test_hold_latch_and_release(self):
        gate=StableGestureGate(min_hold=.7,cooldown=1.5)
        self.assertIsNone(gate.accept('peace',1.0))
        self.assertIsNone(gate.accept('peace',1.6))
        self.assertEqual(gate.accept('peace',1.8),'peace')
        self.assertIsNone(gate.accept('peace',3.0))
        self.assertIsNone(gate.accept('no hand',3.1))
        self.assertIsNone(gate.accept('peace',3.2))
        self.assertEqual(gate.accept('peace',3.95),'peace')

    def test_cooldown_survives_label_change(self):
        gate=StableGestureGate(min_hold=.1,cooldown=1.5)
        gate.accept('peace',0)
        self.assertEqual(gate.accept('peace',.2),'peace')
        gate.accept('three',.3)
        self.assertIsNone(gate.accept('three',.6))
        self.assertEqual(gate.accept('three',1.8),'three')

    def test_invalid_udp_payloads_are_rejected(self):
        self.assertEqual(parse_gesture(b'PEACE\n'),'peace')
        for payload in (b'execute', b'\xff', b'p'*33):
            self.assertIsNone(parse_gesture(payload))


if __name__ == '__main__':unittest.main()
