"""C2 continuous high-level preview trajectories; no streaming flight commands."""
import math
from dataclasses import dataclass
from static_shapes import targets, COUNT

from formation_registry import FORMATIONS, PERIODS, TRAJECTORY_IDS, validate_speed
# Re-export existing constants for callers; definitions live with the spiral.
from formations.spiral import SPIRAL_CENTER_Z, SPIRAL_TURN_AMPLITUDE
LOOP_IDS = {entry: loop for entry, loop in TRAJECTORY_IDS.values()}
LOOP_IDS.update({loop: loop for _, loop in TRAJECTORY_IDS.values()})


def motion(shape, elapsed, entry=False, speed=1.0):
    period = PERIODS[shape]/validate_speed(speed)
    omega = 2 * math.pi / period
    if entry:
        u = max(0.0, min(1.0, elapsed / period))
        phase = 2*math.pi*(6*u**3 - 8*u**4 + 3*u**5)
        velocity = omega*(18*u**2 - 32*u**3 + 15*u**4)
        acceleration = omega/period*(36*u - 96*u**2 + 60*u**3)
    else:
        phase, velocity, acceleration = omega*elapsed, omega, 0.0
    evaluate=FORMATIONS[shape].evaluate
    return tuple(evaluate(point,phase,velocity,acceleration) for point in targets(shape))



def hermite(p0, v0, a0, p1, v1, a1, duration):
    c0, c1, c2 = p0, v0*duration, a0*duration**2/2
    r0 = p1-c0-c1-c2
    r1 = v1*duration-c1-2*c2
    r2 = a1*duration**2-2*c2
    normalized = (c0,c1,c2,10*r0-4*r1+r2/2,-15*r0+7*r1-r2,6*r0-3*r1+r2/2)
    return tuple(c/duration**i for i,c in enumerate(normalized)) + (0.,0.)


@dataclass(frozen=True)
class Piece:
    duration: float
    axes: tuple

    def evaluate(self, t, derivative=0):
        result = []
        for axis in self.axes:
            coefficients = axis
            for _ in range(derivative):
                coefficients = tuple(i*c for i,c in enumerate(coefficients) if i)
            result.append(sum(c*t**i for i,c in enumerate(coefficients)))
        return tuple(result)


def compile_trajectories(shape, entry=False, pieces=None, speed=1.0):
    if pieces is None:pieces=FORMATIONS[shape].pieces
    duration = PERIODS[shape]/validate_speed(speed)/pieces
    trajectories = [[] for _ in range(COUNT)]
    for step in range(pieces):
        a = motion(shape, step*duration, entry, speed)
        b = motion(shape, (step+1)*duration, entry, speed)
        for i in range(COUNT):
            axes = tuple(hermite(a[i][0][axis],a[i][1][axis],a[i][2][axis],
                                 b[i][0][axis],b[i][1][axis],b[i][2][axis],duration)
                         for axis in range(3))
            trajectories[i].append(Piece(duration, axes))
    return tuple(tuple(pieces) for pieces in trajectories)


def as_ros_trajectory(pieces):
    import numpy as np
    from crazyflie_py.uav_trajectory import Polynomial4D, Trajectory
    trajectory = Trajectory()
    trajectory.polynomials = [Polynomial4D(p.duration, *(np.array(a) for a in p.axes), np.zeros(8))
                              for p in pieces]
    trajectory.duration = sum(p.duration for p in pieces)
    return trajectory
