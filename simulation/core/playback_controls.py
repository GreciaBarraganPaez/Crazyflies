"""Simulation-clock demo scheduling, separate from flight and ROS code."""
from simulation.core.formation_registry import FORMATIONS, GESTURES_BY_SHAPE


class DemoSequence:
    def __init__(self):
        self.active=False
        self.shape=None
        self.due=None

    def stop(self):
        self.active=False
        self.shape=self.due=None

    def start(self):
        self.stop()
        self.active=True

    def poll(self, state, shape, running, now, period):
        """Return one normal gesture; never arm, take off or land on its own."""
        if not self.active:return None
        if state in ('grounded','landing','to_grid'):
            self.stop()
            return None
        order=tuple(FORMATIONS)
        if state=='ready':return GESTURES_BY_SHAPE[order[0]]
        if state!='showing' or not running:return None
        if shape!=self.shape or self.due is None:
            self.shape=shape
            self.due=now+max(12.,2*period)
        if now<self.due:return None
        self.due=None
        return GESTURES_BY_SHAPE[order[(order.index(shape)+1)%len(order)]]
