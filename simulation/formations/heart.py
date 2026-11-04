"""Heart position, velocity and acceleration for one assigned drone."""
import math


def evaluate(point, phase, velocity, acceleration):
    x,y,z=point
    scale = 1 + .2*math.sin(phase)
    ds = .2*math.cos(phase)*velocity
    dds = .2*(-math.sin(phase)*velocity**2 + math.cos(phase)*acceleration)
    delta = (x, 0., z-2.7)
    position = (x*scale, y, 2.7+(z-2.7)*scale)
    vel = tuple(d*ds for d in delta)
    acc = tuple(d*dds for d in delta)
    return position,vel,acc
