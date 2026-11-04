"""Seven-drone vertical formations (X-Z plane, metres), simulation ONLY.

The drone IDs are mapped to targets from left to right. This preserves their
horizontal order during straight-line interpolations between the formations.
No active collision avoidance or feedback-based trajectory checking is provided.
"""
from itertools import combinations
from math import cos, dist, pi, sin

DRONES = tuple(f'cf{i}' for i in range(231, 238))
FLIGHT_HEIGHT = 1.7
MIN_PLANNED_SEPARATION = 0.3
LINE_SPACING = 0.8
CIRCLE_RADIUS = 1.6
CIRCLE_CENTER_HEIGHT = 2.2
FORMATION_NAMES = ('line', 'v', 'circle')


def positions(name, z=FLIGHT_HEIGHT):
    """Get {drone_name: (x,y,z)} in the world frame; z sets line height."""
    if name not in FORMATION_NAMES:
        raise ValueError(f'Unknown formation {name!r}. Choose from {FORMATION_NAMES}')

    count = len(DRONES)
    xs = [(i - (count - 1) / 2) * LINE_SPACING for i in range(count)]
    if name == 'line':
        xz = [(x, z) for x in xs]
    elif name == 'v':
        xz = [(x, 0.85 + 0.48 * abs(x)) for x in xs]
    else:
        # Seven equally spaced points on the circumference of a VERTICAL circle.
        # Sort by X so drones retain left-to-right order across formations.
        xz = sorted(
            (CIRCLE_RADIUS * cos(pi / 2 + 2 * pi * i / count),
             CIRCLE_CENTER_HEIGHT + CIRCLE_RADIUS * sin(pi / 2 + 2 * pi * i / count))
            for i in range(count)
        )

    result = {drone: (float(x), 0.0, float(height)) for drone, (x, height) in zip(DRONES, xz)}
    if any(height < 0.5 for _, _, height in result.values()):
        raise ValueError('A drone would be too close to the ground (<0.5 m).')
    return result


def min_separation(targets):
    return min(dist(a, b) for a, b in combinations(targets.values(), 2))


def min_horizontal_separation(targets):
    """Horizontal clearance remains relevant even when all drones land."""
    return min(abs(a[0] - b[0]) for a, b in combinations(targets.values(), 2))


def check_geometry():
    """Check static and interpolated targets, not actual drone trajectories."""
    sequence = ('line', 'v', 'circle', 'line')
    results = []
    for name in FORMATION_NAMES:
        points = positions(name)
        separation = min_separation(points)
        assert separation >= MIN_PLANNED_SEPARATION, (name, separation)
        assert min_horizontal_separation(points) >= MIN_PLANNED_SEPARATION, name
        results.append((name, separation))
    for before, after in zip(sequence, sequence[1:]):
        a, b = positions(before), positions(after)
        for step in range(101):
            t = step / 100
            intermediate = {
                drone: tuple((1-t)*u+t*v for u,v in zip(a[drone], b[drone]))
                for drone in DRONES
            }
            assert min_separation(intermediate) >= MIN_PLANNED_SEPARATION, (before, after, t)
            assert min_horizontal_separation(intermediate) >= MIN_PLANNED_SEPARATION, (before, after, t)
    return results
