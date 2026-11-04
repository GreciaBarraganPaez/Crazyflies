"""Shared preview formation metadata. Models are pure functions of phase.

Keep IDs stable: the installed firmware and preview protocol use these values.
Assigned resting geometry remains in static_shapes for the physics fallback.
"""
from dataclasses import dataclass
from typing import Callable
import math
from simulation.formations import heart, sine, spiral, moon, helix


@dataclass(frozen=True)
class Formation:
    name: str
    gesture: str
    period: float
    entry_id: int
    loop_id: int
    blend_id: int
    pieces: int
    evaluate: Callable


FORMATIONS = {f.name:f for f in (
    Formation('heart','peace',3.2,70,71,80,32,heart.evaluate),
    Formation('sine','three',6.0,72,73,82,32,sine.evaluate),
    Formation('spiral','ok',8.0,74,75,84,64,spiral.evaluate),
    Formation('moon','moon',10.0,76,77,86,32,moon.evaluate),
    Formation('helix','helix',6.0,78,79,88,32,helix.evaluate),
)}
PERIODS = {name:f.period for name,f in FORMATIONS.items()}
TRAJECTORY_IDS = {name:(f.entry_id,f.loop_id) for name,f in FORMATIONS.items()}
BLEND_REQUESTS = {f.blend_id:name for name,f in FORMATIONS.items()}
SHAPE_GESTURES = {f.gesture:name for name,f in FORMATIONS.items()}
GESTURES_BY_SHAPE = {name:f.gesture for name,f in FORMATIONS.items()}


def validate_speed(value):
    value=float(value)
    if not math.isfinite(value) or not .5<=value<=1.25:
        raise ValueError('Animation speed must be between 0.5 and 1.25')
    return value
