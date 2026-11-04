"""Nineteen-drone static X-Z silhouettes (front view), simulation only.

At rest, drones are on a centered 6/7/6 ground grid in X-Y.
After takeoff the grid is at z=2.7 m. Silhouettes use y=0 with different z
heights; the helix extends into depth and is best viewed at an angle.

Assigned target points are statically optimized for the grid-to-shape
straight-line paths. This is not real trajectory or collision avoidance.
"""
from __future__ import annotations
import bisect
import math
from simulation.formations.moon import geometry as moon_geometry
from simulation.formations.helix import geometry as helix_geometry
from itertools import combinations

DRONES = tuple(f'cf{i}' for i in range(231, 250))
COUNT = len(DRONES)
GRID_X_SPACING = 1.10
GRID_Y_SPACING = 1.30
FLIGHT_HEIGHT = 2.70
MIN_PLANNED_SEPARATION = 0.52

# Three centered rows: 6 + 7 + 6 = 19 (symmetrical about x=0 and y=0).
_ROW_X = (
    (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5),
    (-3., -2., -1., 0., 1., 2., 3.),
    (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5),
)
HOME = tuple(
    (round(x * GRID_X_SPACING, 6), (row - 1) * GRID_Y_SPACING, FLIGHT_HEIGHT)
    for row, xs in enumerate(_ROW_X) for x in xs
)


def _heart():
    """Symmetric heart outline in X-Z. Center drone marks the bottom tip."""
    def curve(theta):
        return (0.18 * 16 * math.sin(theta)**3,
                3.70 + 0.16 * (13*math.cos(theta) - 5*math.cos(2*theta)
                               - 2*math.cos(3*theta) - math.cos(4*theta)))

    n = 10000
    samples = [curve(math.pi + 2*math.pi*i/n) for i in range(n+1)]
    lengths = [0.]
    for a, b in zip(samples, samples[1:]):
        lengths.append(lengths[-1] + math.dist(a, b))
    pts = []
    for i in range(COUNT):
        distance = lengths[-1]*i/COUNT
        j = max(1, bisect.bisect_left(lengths, distance))
        length = lengths[j]-lengths[j-1]
        frac = (distance-lengths[j-1]) / length if length else 0
        a, b = samples[j-1], samples[j]
        pts.append((a[0]+frac*(b[0]-a[0]), 0., a[1]+frac*(b[1]-a[1])))
    # Both near the top notch were only 0.31m apart; open the notch.
    x,z = pts[9][0],pts[9][2]
    pts[9] = (-0.45, 0., z)
    pts[10] = (0.45, 0., z)
    return tuple(pts)


def _sine():
    """Wide, two-wave sine curve on a standing vertical X-Z plane."""
    return tuple(
        (-5.4 + i*10.8/(COUNT-1), 0.,
         2.90 + 1.40*math.sin(2*math.pi*(-5.4 + i*10.8/(COUNT-1))/5.4))
        for i in range(COUNT)
    )


def _spiral():
    """One-and-a-half turns of a visible, spaced-out vertical spiral."""
    return tuple(
        ((1.4 + i*2.2/(COUNT-1))*math.cos(i*3*math.pi/(COUNT-1)),
         0.,
         3.8 + (1.4 + i*2.2/(COUNT-1))*math.sin(i*3*math.pi/(COUNT-1)))
        for i in range(COUNT)
    )


# Precomputed mapping from each grid drone to a shape point to reduce
# simultaneous straight-line path crossings. Not real collision avoidance.
_ASSIGNMENT = {
    'heart': (5, 7, 10, 18, 11, 13, 4, 3, 2, 0, 17, 16, 15, 6, 8, 1, 9, 12, 14),
    'sine': (1, 4, 8, 10, 15, 16, 0, 5, 6, 9, 12, 14, 17, 2, 3, 11, 7, 13, 18),
    'spiral': (17, 5, 3, 2, 14, 0, 18, 7, 8, 9, 10, 11, 12, 6, 16, 4, 1, 15, 13),
    'moon': (16, 13, 18, 2, 5, 9, 14, 11, 0, 10, 3, 8, 6, 12, 15, 17, 1, 7, 4),
    'helix': (5, 3, 6, 16, 11, 14, 1, 10, 8, 4, 7, 17, 18, 2, 0, 15, 13, 9, 12),
}
_RAW = {'heart': _heart(), 'sine': _sine(), 'spiral': _spiral(), 'moon': moon_geometry(), 'helix': helix_geometry()}
SHAPES = {name: tuple(raw[j] for j in _ASSIGNMENT[name]) for name, raw in _RAW.items()}


def targets(name):
    return HOME if name == 'grid' else SHAPES[name]


def ground_positions():
    return tuple((x, y, 0.) for x, y, z in HOME)


def minimum_distance(points):
    return min(math.dist(a,b) for a,b in combinations(points,2))


def _pair_path_distance(a0, a1, b0, b1):
    """Exact distance lower bound for *linear, synchronized* trajectories."""
    d0 = tuple(a-b for a,b in zip(a0,b0))
    d1 = tuple(a-b-d for a,b,d in zip(a1,b1,d0))
    norm2 = sum(d*d for d in d1)
    t = max(0.,min(1., -sum(a*b for a,b in zip(d0,d1))/norm2)) if norm2 > 1e-12 else 0.
    return math.sqrt(sum((a+t*b)**2 for a,b in zip(d0,d1)))


def planned_segment_distance(start,end):
    if len(start)!=COUNT or len(end)!=COUNT:
        raise ValueError(f'Expected {COUNT} drones')
    return min(_pair_path_distance(start[i],end[i],start[j],end[j])
               for i in range(COUNT) for j in range(i+1,COUNT))


def validate_geometry():
    assert COUNT == 19 and len(HOME) == COUNT
    assert sum(len(r) for r in _ROW_X) == COUNT
    assert all(x == 0. or (-x in [p[0] for p in HOME]) for x,_,_ in HOME)
    assert all(z == FLIGHT_HEIGHT for x,y,z in HOME)
    results = {}
    for name, points in [('grid', HOME), *SHAPES.items()]:
        assert len(points) == COUNT and len(set(points)) == COUNT
        if name != 'grid':
            if name!='helix':assert all(abs(y) < 1e-9 for _,y,_ in points), name
            assert all(z > 0.6 for _,_,z in points), name
        gap=minimum_distance(points)
        transit=planned_segment_distance(HOME,points)
        assert gap >= MIN_PLANNED_SEPARATION, (name, 'shape spacing',gap)
        assert transit >= MIN_PLANNED_SEPARATION, (name,'ideal line paths',transit)
        results[name]=(round(gap,3), round(transit,3))
    # Home is a 19-drone grid; the vertical landing from it keeps XY positions.
    assert all(abs(a[0]-b[0]) < 1e-9 and abs(a[1]-b[1]) < 1e-9
               for a,b in zip(HOME,ground_positions()))
    return results

if __name__ == '__main__':
    for name, (gap, transit) in validate_geometry().items():
        print(f'{name:6s}: shape separation {gap:.2f}m, ideal grid transition {transit:.2f}m')
    print('Silhouettes use vertical X-Z; helix uses Y depth. Select an angled view for 3D.')
