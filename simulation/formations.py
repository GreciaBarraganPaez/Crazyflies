"""Three-drone formations visible from the front (X-Z plane, metres).

X is left/right; Z is height; Y stays at zero so observers looking along
Y can see the shape. Simulation demonstration ONLY: no active collision avoidance.
"""
from itertools import combinations
from math import dist, sqrt

DRONES = ('cf231', 'cf232', 'cf233')
FLIGHT_HEIGHT = 1.2  # common centre altitude (m)
MIN_PLANNED_SEPARATION = 0.3


def positions(name, z=FLIGHT_HEIGHT):
    """Return drone targets (x, y, z); preserve the original function API.

    This keeps each drone in its left/centre/right lane whenever possible.
    Three drones on a circle form a triangle, not a visually smooth ring.
    """
    circle_radius = 0.8
    x_circle = (sqrt(3) / 2) * circle_radius
    xz = {
        'line': [(-0.8, z), (0.0, z), (0.8, z)],
        'v': [(-0.8, z + 0.5), (0.0, z - 0.5), (0.8, z + 0.5)],
        # Three points on a vertical circle (equilateral triangle).
        'circle': [(-x_circle, z - circle_radius / 2),
                   (0.0, z + circle_radius),
                   (x_circle, z - circle_radius / 2)],
    }
    if name not in xz:
        raise ValueError(f'Unknown formation: {name}. Choose from {tuple(xz)}')
    targets = {drone: (x, 0.0, height) for drone, (x, height) in zip(DRONES, xz[name])}
    if any(height < 0.3 for _, _, height in targets.values()):
        raise ValueError('Formation puts a drone below 0.3 m above the ground.')
    return targets


def min_separation(targets):
    return min(dist(a, b) for a, b in combinations(targets.values(), 2))


def check_geometry():
    """Check target distances and ideal straight-line interpolations only.

    Passing this check is NOT a proof that real drone trajectories are safe.
    """
    names = ('line', 'v', 'circle', 'line')
    results = []
    for name in ('line', 'v', 'circle'):
        minimum = min_separation(positions(name))
        assert minimum >= MIN_PLANNED_SEPARATION, (name, minimum)
        results.append((name, minimum))
    for before, after in zip(names, names[1:]):
        a, b = positions(before), positions(after)
        for step in range(101):
            t = step / 100
            midway = {
                drone: tuple((1 - t) * aa + t * bb for aa, bb in zip(a[drone], b[drone]))
                for drone in DRONES
            }
            assert min_separation(midway) >= MIN_PLANNED_SEPARATION, (before, after, t)
    return results
