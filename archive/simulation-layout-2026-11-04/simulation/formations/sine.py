"""Sine position, velocity and acceleration for one assigned drone."""
import math


def evaluate(point, phase, velocity, acceleration):
    x,y,z=point
    angle = 2*math.pi*x/5.4 - phase
    position = (x, y, 2.9+1.4*math.sin(angle))
    vel = (0., 0., -1.4*math.cos(angle)*velocity)
    acc = (0., 0., -1.4*math.sin(angle)*velocity**2-1.4*math.cos(angle)*acceleration)
    return position,vel,acc
