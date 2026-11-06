"""Simple time-based filter shared by the gesture sender and tests."""

KNOWN = {'one', 'peace', 'three', 'ok', 'palm', 'fist', 'clock'}


class StableGestureGate:
    """Send once per sustained label; require a different/neutral label before retrigger."""

    def __init__(self, min_hold=0.7, cooldown=1.5):
        self.min_hold = min_hold
        self.cooldown = cooldown
        self.candidate = None
        self.start = None
        self.latched = None
        self.last_sent = -float('inf')

    def accept(self, label, now):
        if label not in KNOWN:
            self.candidate = None
            self.start = None
            self.latched = None
            return None
        if label != self.candidate:
            self.candidate = label
            self.start = now
        if self.latched == label:
            return None
        if now - self.start < self.min_hold or now - self.last_sent < self.cooldown:
            return None
        self.latched = label
        self.last_sent = now
        return label
