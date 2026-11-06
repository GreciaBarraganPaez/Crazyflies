#!/usr/bin/env python3
"""SwarmGesture: static 19-drone FRONT-VIEW shapes over UDP; SIMULATION ONLY.

Gestures: one=takeoff, peace=heart, three=sine, ok=spiral,
          fist=return to grid, palm=grid then controlled landing.

Shape targets share y=0, but have different z coordinates (front X-Z plane).
Switches and landing go via the centered 6/7/6 XY grid.
Planned geometry is checked; fresh TF grid positions gate landing and shape switches.
"""
from __future__ import annotations
import argparse
import math
import select
import socket
import sys
import time
from simulation.core.formation_registry import SHAPE_GESTURES

from simulation.core.static_shapes import (
    DRONES, HOME, FLIGHT_HEIGHT, MIN_PLANNED_SEPARATION,
    targets, planned_segment_distance, validate_geometry,
    minimum_distance,
)

PORT = 5055
TAKEOFF_SEC = 3.0
SHAPE_MOVE_SEC = 4.8
GRID_MOVE_SEC = 4.8
LAND_SEC = 3.2
MARGIN_SEC = 0.55
GESTURES = {'one', 'palm', 'fist'} | set(SHAPE_GESTURES)
ACTIONS = {
    'one': 'take off from grid',
    **{gesture:f'static {shape}' for gesture,shape in SHAPE_GESTURES.items()},
    'fist': 'return to grid',
    'palm': 'return to grid and land',
}


def set_fast_test_timing(enabled):
    """Faster timed moves for simulation experiments only (not real hardware)."""
    global TAKEOFF_SEC, SHAPE_MOVE_SEC, GRID_MOVE_SEC, LAND_SEC, MARGIN_SEC
    if enabled:
        TAKEOFF_SEC = 2.3
        SHAPE_MOVE_SEC = 3.0
        GRID_MOVE_SEC = 3.0
        LAND_SEC = 2.5
        MARGIN_SEC = 0.35
    else:
        TAKEOFF_SEC = 3.0
        SHAPE_MOVE_SEC = 4.8
        GRID_MOVE_SEC = 4.8
        LAND_SEC = 3.2
        MARGIN_SEC = 0.55



def parse_gesture(data, gestures=GESTURES):
    if len(data) > 32:
        return None
    try:
        label = data.decode('ascii', errors='strict').strip().lower()
    except UnicodeDecodeError:
        return None
    return label if label in gestures else None


class SimulationController:
    """Timed, manually-armed controller. Never use for real hardware."""

    DRONE_NAMES = DRONES
    HOME_POINTS = HOME

    def __init__(self, swarm, grid_arrived=None):
        self.drone_names = self.DRONE_NAMES
        self.home = self.HOME_POINTS
        self.swarm = swarm
        self.clock = swarm.timeHelper.time if hasattr(swarm, "timeHelper") else time.monotonic
        self.grid_arrived = grid_arrived
        self.waiting_for_grid = False
        self.by_name = swarm.allcfs.crazyfliesByName
        if set(self.by_name) != set(self.drone_names):
            raise RuntimeError(f'Expected {len(self.drone_names)} drones {self.drone_names[0]}..{self.drone_names[-1]}; '
                               f'got {sorted(self.by_name)}. Generate YAML and restart ROS.')
        self.state = 'grounded'
        self.armed = False
        self.shape = None
        self.current_goals = self.home  # planned targets, not measured positions
        self.next_shape = None
        self.land_after_grid = False
        self.queued_gesture = None
        self.due = 0.0

    def _move(self, points, seconds):
        gap = planned_segment_distance(self.current_goals, points)
        required_gap = 0.0 if points == targets('clock') else MIN_PLANNED_SEPARATION
        if gap < required_gap:
            print(f'REJECTED path: ideal straight-line separation {gap:.2f} m.', flush=True)
            return False
        for name, point in zip(self.drone_names, points):
            self.by_name[name].goTo(list(point), yaw=0.0, duration=seconds)
        self.current_goals = points
        return True

    def arm(self, now=None):
        now = self.clock() if now is None else now
        self.update(now)
        if self.state != 'grounded':
            print('Cannot arm: land first.', flush=True)
            return
        self.armed = True
        print('ARMED: show one finger to take off from the starting grid.', flush=True)

    def _start_shape(self, shape, now):
        if self.current_goals != self.home or self.state != 'ready':
            raise RuntimeError('Internal error: must be ready at grid before new shape')
        points = targets(shape)
        if not self._move(points, SHAPE_MOVE_SEC):
            print('Shape move rejected: staying at grid.', flush=True)
            return
        self.shape = shape
        self.state = 'to_shape'
        self.due = now + SHAPE_MOVE_SEC + MARGIN_SEC
        plane='in 3D' if shape=='helix' else 'in vertical X-Z plane (y=0)'
        print(f'FORMING STATIC {shape.upper()} {plane}, {SHAPE_MOVE_SEC:.1f}s.', flush=True)

    def _start_grid(self, now, next_shape=None, land=False):
        self.waiting_for_grid = False
        self.next_shape = next_shape
        self.land_after_grid = land
        self.shape = None
        already_home = self.current_goals == self.home
        if not already_home and not self._move(self.home, GRID_MOVE_SEC):
            self.state = 'showing'  # remain in previous commanded position
            self.next_shape = None
            self.land_after_grid = False
            print('Return path rejected. Inspect RViz and land manually if required.', flush=True)
            return
        self.state = 'to_grid'
        self.due = now + (0.3 if already_home else GRID_MOVE_SEC + MARGIN_SEC)
        print(('Already at grid' if already_home else f'GRID RETURN COMMANDED ({GRID_MOVE_SEC:.1f}s, wait before landing)') +
              (f' -> {next_shape}' if next_shape else ' -> land' if land else ''), flush=True)

    def _issue_land(self, now):
        if self.current_goals != self.home or self.state not in ('ready', 'to_grid'):
            raise RuntimeError('Refusing to land: grid-return stage not completed')
        self.swarm.allcfs.land(targetHeight=0.04, duration=LAND_SEC)
        self.state = 'landing'
        self.due = now + LAND_SEC + MARGIN_SEC
        self.armed = False
        print('GRID RETURN INTERVAL FINISHED -> now requesting vertical landing at grid XY points.', flush=True)
        print('Landing from verified grid positions.' if self.grid_arrived else
              'No position feedback: timing-only test controller.', flush=True)

    def land(self, reason='Land', now=None):
        now = self.clock() if now is None else now
        self.update(now)
        self.armed = False
        if self.state in ('grounded', 'landing'):
            print(f'{reason}: already grounded/landing.', flush=True)
            return
        if self.state in ('taking_off', 'to_shape'):
            self.queued_gesture = 'palm'
            print(f'{reason}: queued landing after current move.', flush=True)
            return
        if self.state == 'to_grid':
            self.land_after_grid = True
            self.next_shape = None
            print(f'{reason}: will land after reaching grid.', flush=True)
            return
        self._start_grid(now, land=True)

    def handle(self, label, now=None):
        now = self.clock() if now is None else now
        self.update(now)
        if label == 'palm':
            self.land('Open palm', now)
            return
        if self.state == 'landing':
            return
        if label == 'one':
            if self.state != 'grounded' or not self.armed:
                print('Takeoff ignored: controller not grounded and armed.', flush=True)
                return
            self.armed = False
            self.swarm.allcfs.takeoff(targetHeight=FLIGHT_HEIGHT, duration=TAKEOFF_SEC)
            self.state = 'taking_off'
            self.due = now + TAKEOFF_SEC + MARGIN_SEC
            print(f'Taking off {len(self.drone_names)} drones from ground grid to z={FLIGHT_HEIGHT:.2f}m ({TAKEOFF_SEC:.1f}s).', flush=True)
            return
        if label not in SHAPE_GESTURES and label != 'fist':
            return
        if self.state == 'grounded':
            print('Take off first.', flush=True)
            return
        if self.state in ('taking_off', 'to_shape'):
            self.queued_gesture = label
            print(f'Queued {label} until current movement finishes.', flush=True)
            return
        shape = SHAPE_GESTURES.get(label)
        if self.state == 'to_grid':
            if not self.land_after_grid:
                self.next_shape = shape  # fist means remain at grid
                print(f'Queued after grid: {shape or "grid"}.', flush=True)
            return
        if shape and self.state == 'showing' and self.shape == shape:
            print(f'Already displaying {shape}.', flush=True)
            return
        if self.state in ('ready', 'showing'):
            if self.current_goals == self.home:
                if shape:
                    self._start_shape(shape, now)
                else:
                    print('Already at grid.', flush=True)
            else:
                self._start_grid(now, next_shape=shape)

    def update(self, now=None):
        now = self.clock() if now is None else now
        if now < self.due:
            return
        if self.state == 'taking_off':
            self.state = 'ready'
            print('Takeoff interval finished: airborne grid ready.', flush=True)
        elif self.state == 'to_shape':
            self.state = 'showing'
            print(f'STATIC {self.shape.upper()} displayed. Drones should hover.', flush=True)
        elif self.state == 'to_grid':
            if self.grid_arrived is not None and not self.grid_arrived():
                if not self.waiting_for_grid:
                    print('Waiting for fresh TF positions: all drones must reach the airborne grid.', flush=True)
                    self.waiting_for_grid = True
                return
            self.state = 'ready'
            print('Grid return completed' + (' (TF positions verified).' if self.grid_arrived else ' (timing only).'), flush=True)
            if self.land_after_grid:
                self.land_after_grid = False
                self._issue_land(now)
                return
            if self.next_shape:
                shape = self.next_shape
                self.next_shape = None
                self._start_shape(shape, now)
                return
        elif self.state == 'landing':
            self.state = 'grounded'
            self.current_goals = self.home
            self.shape = None
            self.next_shape = None
            self.land_after_grid = False
            self.queued_gesture = None
            print('Landing interval finished (simulated timing). Press a + Enter to arm again.', flush=True)
        if self.state in ('ready', 'showing') and self.queued_gesture:
            label = self.queued_gesture
            self.queued_gesture = None
            self.handle(label, now)


def arrival_metrics(measured, goals, tolerance):
    error = max(math.dist(a, b) for a, b in zip(measured, goals))
    clearance = minimum_distance(measured)
    return error <= tolerance and clearance >= MIN_PLANNED_SEPARATION, error, clearance


class GridArrivalMonitor:
    """Require recent world-frame TF positions near every assigned grid point."""

    def __init__(self, node, drone_names=DRONES, home=HOME):
        self.drone_names, self.home = drone_names, home
        from tf2_ros import Buffer, TransformListener
        self.node = node
        self.buffer = Buffer(node=node)
        self.listener = TransformListener(self.buffer, node)
        self.last_status = 'No feedback yet'

    def __call__(self):
        return self.at(self.home)

    def at(self, points, tolerance=0.20):
        if len(points) != len(self.drone_names) or any(not all(math.isfinite(v) for v in p) for p in points):
            return False
        measured = self.snapshot()
        if measured is None:
            return False
        arrived, worst_error, clearance = arrival_metrics(measured, points, tolerance)
        self.last_status = f'max error={worst_error:.3f}m (limit {tolerance:.2f}m), measured spacing={clearance:.3f}m'
        return arrived

    def snapshot(self):
        """Return one fresh complete world-frame position snapshot, or None."""
        from rclpy.time import Time
        from tf2_ros import TransformException
        now = self.node.get_clock().now().nanoseconds / 1e9
        measured = []
        for name in self.drone_names:
            try:
                transform = self.buffer.lookup_transform('world', name, Time())
            except TransformException:
                self.last_status = f'Missing TF: {name}'
                return None
            stamp = transform.header.stamp
            age = now - (stamp.sec + stamp.nanosec / 1e9)
            p = transform.transform.translation
            if not all(math.isfinite(v) for v in (p.x, p.y, p.z)):
                self.last_status = f'Invalid coordinates: {name}'
                return None
            if not -0.1 <= age <= 1.0:
                self.last_status = f'Stale TF: {name}, age={age:.2f}s'
                return None
            measured.append((p.x, p.y, p.z))
        return tuple(measured)


def main(controller_type=SimulationController):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true', help='UDP check only; does not start ROS')
    group.add_argument('--run-sim', action='store_true', help='SIMULATION ONLY')
    parser.add_argument('--fast-test', action='store_true',
                        help='Simulation-only faster move durations; use only with --run-sim')
    parser.add_argument('--bind', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=PORT)
    parser.add_argument('--allowed-ip', help='Optional Windows sender IPv4 allowed to send')
    args, extra = parser.parse_known_args()
    if extra and extra[0] != '--ros-args':
        parser.error(f'Unexpected arguments: {extra}')
    if not 1024 <= args.port <= 65535:
        parser.error('Port must be in 1024..65535')
    if args.fast_test and not args.run_sim:
        parser.error('--fast-test requires --run-sim')
    set_fast_test_timing(args.fast_test)
    if args.fast_test:
        print('FAST TEST (SIM ONLY): takeoff 2.3s, movements 3.0s, landing 2.5s; '
              'path geometry is checked but actual trajectories are not verified.', flush=True)
    actions = {**ACTIONS, **getattr(controller_type, "INPUT_ACTIONS", {})}
    ctrl = None
    if args.run_sim:
        checks = getattr(controller_type, "geometry_checks", validate_geometry)()
        print('Geometric preflight (not collision avoidance):', checks, flush=True)
        from crazyflie_py import Crazyswarm
        print('SIMULATION ONLY: launch Crazyswarm2 with backend:=sim.', flush=True)
        import rclpy
        swarm = Crazyswarm()
        ctrl = controller_type(swarm, grid_arrived=GridArrivalMonitor(
            swarm.allcfs, controller_type.DRONE_NAMES, controller_type.HOME_POINTS))
        if hasattr(ctrl, 'configure_backend'):
            from rclpy.parameter_client import AsyncParameterClient
            parameters = AsyncParameterClient(swarm.allcfs, 'crazyflie_server')
            backend = 'unknown'
            if parameters.wait_for_services(timeout_sec=2.0):
                future = parameters.get_parameters(['sim.backend'])
                rclpy.spin_until_future_complete(swarm.allcfs, future, timeout_sec=2.0)
                if future.done() and future.exception() is None:
                    backend = future.result().values[0].string_value
            configured=ctrl.configure_backend(backend)
            if configured is not None:ctrl=configured

    def pump_ros():
        if ctrl:
            # Service replies, /clock and TF need an executor even while UDP is idle.
            for _ in range(32):
                rclpy.spin_once(swarm.allcfs, timeout_sec=0)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind((args.bind, args.port))
        server.settimeout(0.12)
        print(f'Listening on UDP {args.bind}:{args.port} | mode={"SIM" if ctrl else "DRY RUN"}', flush=True)
        if ctrl:
            print('Keyboard: a + Enter = arm; x + Enter = grid then land; q + Enter = quit.', flush=True)
            if hasattr(ctrl,'keyboard_command'):ctrl.keyboard_command('help')
        try:
            while True:
                if ctrl:
                    pump_ros()
                    ctrl.update()
                if sys.stdin.isatty() and select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.readline().strip().lower()
                    if key == 'q':
                        break
                    if ctrl and key == 'a':
                        ctrl.arm()
                    elif ctrl and key in ('x', 'land'):
                        ctrl.land('Keyboard')
                    elif ctrl and hasattr(ctrl,'keyboard_command'):
                        ctrl.keyboard_command(key)
                try:
                    data, peer = server.recvfrom(1024)
                except socket.timeout:
                    continue
                if args.allowed_ip and peer[0] != args.allowed_ip:
                    continue
                label = parse_gesture(data, set(actions))
                if label is None:
                    print('Ignored unknown UDP payload.', flush=True)
                elif ctrl:
                    print(f'Received {label} -> {actions[label]}', flush=True)
                    ctrl.handle(label)
                else:
                    print(f'DRY RUN {peer[0]}: {label} -> {actions[label]}', flush=True)
        except KeyboardInterrupt:
            print('\nInterrupted.', flush=True)
        finally:
            if ctrl and ctrl.state != 'grounded':
                pump_ros()
                ctrl.land('Shutdown')
                report_due = time.monotonic() + 10
                try:
                    # A slow simulator must not outlive a wall-clock shutdown timeout.
                    while ctrl.state != 'grounded':
                        pump_ros()
                        ctrl.update()
                        if time.monotonic() >= report_due:
                            print(f'Waiting for controlled shutdown: {ctrl.state}. '
                                  'Keep ROS running. A second Ctrl+C exits without confirmed landing.', flush=True)
                            report_due = time.monotonic() + 10
                        time.sleep(0.05)
                except KeyboardInterrupt:
                    print('Forced bridge exit: landing NOT confirmed. Inspect the simulator.', flush=True)
            print('Bridge stopped.', flush=True)


if __name__ == '__main__':
    main()
