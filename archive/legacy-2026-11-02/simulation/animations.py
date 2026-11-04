"""18-drone Phase 1 animated targets. SIMULATION ONLY; no collision avoidance.

Shapes are displayed on the X-Z plane, with small permanent Y offsets to provide
some depth separation for overlapping points in the front projection.
Targets are in Crazyswarm2 world coordinates (metres).
"""
from __future__ import annotations
import math
from itertools import combinations

DRONES = tuple(f"cf{i}" for i in range(231, 249))
COUNT = len(DRONES)
HOME_HEIGHT = 2.75
X_SPACING = 0.68
# Preflight-selected shallow depth lanes: -0.85, 0, +0.85 metres.
# These are fixed per drone; depth separation aids clearance in dense silhouettes.
LANES = (-1, 1, -1, 1, 0, -1, -1, 1, -1, 1, 0, 0, 1, 0, 1, 1, -1, 1)
Y_OFFSET = 0.85
MIN_PLANNED_SEPARATION = 0.55
ANIMATIONS = ("heart", "wave", "wind_spiral")

HOME = tuple(
    ((i - (COUNT - 1) / 2) * X_SPACING, LANES[i] * Y_OFFSET, HOME_HEIGHT)
    for i in range(COUNT)
)


def _heart_outline():
    # Standard parametric heart contour, sorted left-to-right for fixed drone IDs.
    points = []
    for i in range(COUNT):
        a = 2 * math.pi * i / COUNT
        x = 16 * math.sin(a) ** 3 * 0.27
        z = 2.95 + (13 * math.cos(a) - 5 * math.cos(2 * a)
                    - 2 * math.cos(3 * a) - math.cos(4 * a)) * 0.13
        points.append((x, z))
    return tuple(sorted(points))


def _spiral_outline():
    # Ascending, two-dimensional spiral on X-Z plane (visible from the front).
    points = []
    for i in range(COUNT):
        radius = 0.75 + 0.17 * i
        angle = 1.22 * i
        points.append((radius * math.cos(angle), 4.35 + radius * math.sin(angle)))
    return tuple(sorted(points))


HEART_OUTLINE = _heart_outline()
SPIRAL_OUTLINE = _spiral_outline()


def heart(t):
    """Repeat a slow heartbeat every ~5.5 s."""
    size = 1 + 0.07 * math.sin(2 * math.pi * t / 5.5)
    return tuple((x * size, HOME[i][1], 2.95 + (z - 2.95) * size)
                 for i, (x, z) in enumerate(HEART_OUTLINE))


def wave(t):
    """A traveling sine wave with fixed horizontal drone positions."""
    return tuple((HOME[i][0], HOME[i][1], HOME_HEIGHT + 0.78 *
                  math.sin(2 * math.pi * i / 8 - 2 * math.pi * t / 6.5))
                 for i in range(COUNT))


def spiral(t):
    """A softly breathing spiral."""
    size = 1 + 0.05 * math.sin(2 * math.pi * t / 6)
    return tuple((x * size, HOME[i][1], 4.35 + (z - 4.35) * size)
                 for i, (x, z) in enumerate(SPIRAL_OUTLINE))


def _ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def interpolate(a, b, amount):
    return tuple(tuple(x * (1 - amount) + y * amount for x, y in zip(left, right))
                 for left, right in zip(a, b))


def wind_spiral(t):
    """Traveling wind wave -> spiral -> wave; continuously repeats every 19 s."""
    phase = t % 19
    if phase < 4:
        return wave(t)
    if phase < 9:
        return interpolate(wave(t), spiral(t), _ease((phase - 4) / 5))
    if phase < 14:
        return spiral(t)
    return interpolate(spiral(t), wave(t), _ease((phase - 14) / 5))


FUNCTIONS = {"heart": heart, "wave": wave, "wind_spiral": wind_spiral}


def positions(name, elapsed):
    if name not in FUNCTIONS:
        raise ValueError(f"Unknown animation: {name}")
    return FUNCTIONS[name](elapsed)


def minimum_distance(points):
    return min(math.dist(a, b) for a, b in combinations(points, 2))


def planned_segment_distance(a, b, samples=20):
    """Checks STRAIGHT interpolations of target positions; not actual flight paths."""
    return min(minimum_distance(interpolate(a, b, i / samples))
               for i in range(samples + 1))


def validate_geometry():
    """Preflight sample test. Actual Crazyflie trajectories are not guaranteed safe."""
    if len(HOME) != COUNT or len(LANES) != COUNT:
        raise AssertionError("Drone count/lane mismatch")
    worst = (float('inf'), '')
    for name, fn in FUNCTIONS.items():
        period = 19 if name == 'wind_spiral' else 12
        last = HOME
        for frame in range(period * 5 + 1):
            t = frame / 5
            next_points = fn(t)
            for label, d in (
                ('animation', planned_segment_distance(last, next_points, 5)),
                ('home', planned_segment_distance(HOME, next_points, 5)),
            ):
                if d < worst[0]:
                    worst = (d, f'{name} {label} at t={t:.1f}s')
                if d < MIN_PLANNED_SEPARATION:
                    raise AssertionError(f'Planned clearance too small: {d:.3f}m; {name} {label} t={t:.1f}s')
            last = next_points
    return worst
