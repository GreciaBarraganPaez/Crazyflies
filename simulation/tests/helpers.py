"""Shared fake fleets and deterministic scenarios; no test cases or ROS calls."""
from simulation.core.static_shapes import DRONES

class FakeDrone:
    def __init__(self, name, events):
        self.name, self.commands, self.events = name, [], events
    def goTo(self, goal, yaw, duration):
        self.commands.append((tuple(goal),duration))
        self.events.append(('goTo',self.name,tuple(goal)))

class FakeFleet:
    def __init__(self):
        self.events=[]
        self.crazyfliesByName={name:FakeDrone(name,self.events) for name in DRONES}
    def takeoff(self,targetHeight,duration):
        self.events.append(('takeoff',targetHeight,duration))
    def land(self,targetHeight,duration):
        self.events.append(('land',targetHeight,duration))

class FakeSwarm:
    def __init__(self): self.allcfs=FakeFleet()
