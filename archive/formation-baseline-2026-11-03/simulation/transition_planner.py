"""Simulation-only routes between resting X-Z formations, preserving drone IDs.

Color conflicting straight X-Z paths into separate Y lanes. Spread in Y, morph
in X-Z, then flatten Y. Each synchronized, rest-to-rest stage is checked with
the exact pairwise straight-segment lower bound. No physics/avoidance guarantee.
"""
import math
from static_shapes import (COUNT, MIN_PLANNED_SEPARATION, minimum_distance,
                           planned_segment_distance, _pair_path_distance)

LANE_SPACING = 0.85
DIRECT_CLEARANCE = 0.75


def plan_transition(start, end):
    if len(start) != COUNT or len(end) != COUNT:
        raise ValueError('Transition requires the complete fleet')
    if any(len(p) != 3 or not all(math.isfinite(v) for v in p) for p in (*start, *end)):
        raise ValueError('Transition points must be finite 3D coordinates')
    if any(abs(p[1]) > 1e-8 for p in (*start, *end)):
        raise ValueError('Transition endpoints must be resting front-plane shapes')
    if min(minimum_distance(start), minimum_distance(end)) < MIN_PLANNED_SEPARATION:
        raise ValueError('Formation endpoint separation is insufficient')
    if planned_segment_distance(start, end) >= DIRECT_CLEARANCE:
        return (end,)
    neighbors = [set() for _ in start]
    for i in range(COUNT):
        for j in range(i):
            if _pair_path_distance(start[i], end[i], start[j], end[j]) < DIRECT_CLEARANCE:
                neighbors[i].add(j)
                neighbors[j].add(i)
    colors = {}
    for i in sorted(range(COUNT), key=lambda k: (-len(neighbors[k]), k)):
        occupied = {colors[j] for j in neighbors[i] if j in colors}
        colors[i] = next(c for c in range(COUNT) if c not in occupied)
    center = max(colors.values()) / 2
    lanes = [(colors[i] - center) * LANE_SPACING for i in range(COUNT)]
    spread = tuple((x, lanes[i], z) for i, (x, _, z) in enumerate(start))
    morph = tuple((x, lanes[i], z) for i, (x, _, z) in enumerate(end))
    stages = (spread, morph, end)
    previous = start
    for stage in stages:
        if planned_segment_distance(previous, stage) < MIN_PLANNED_SEPARATION:
            raise ValueError('Transition stage failed separation preflight')
        previous = stage
    return stages
