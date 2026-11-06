"""Analog clock formation showing the local time at startup."""
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import math

CENTER_Z = 6.7
RADIUS = 5.5

def _point(angle, radius, depth=0.0):
    return (radius * math.sin(angle), depth, CENTER_Z + radius * math.cos(angle))

def geometry(now=None):
    if now is None:
        timezone_name = os.environ.get('SWARMGESTURE_TIMEZONE', 'Europe/Berlin')
        now = datetime.now(ZoneInfo(timezone_name))
    minute = now.minute + now.second / 60.0
    hour = (now.hour % 12) + minute / 60.0
    minute_angle = 2 * math.pi * minute / 60.0
    hour_angle = 2 * math.pi * hour / 12.0
    points = [_point(2 * math.pi * i / 12.0, RADIUS) for i in range(12)]
    points += [_point(hour_angle, radius, 0.45) for radius in (0.9, 2.3, 3.7)]
    points += [_point(minute_angle, radius, -0.45) for radius in (1.5, 2.8, 4.1, 5.0)]
    return tuple(points)

def evaluate(point, phase, velocity, acceleration):
    return point, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
