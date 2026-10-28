#!/usr/bin/env python3
"""Run the line -> V -> circle formation demo in the Crazyswarm2 sim.

Dry-run is safe without ROS. A real command run requires --run-sim.
"""
import argparse
from formations import DRONES, check_geometry, positions

MOVE_DURATION = 6.0
TAKEOFF_DURATION = 3.0
LAND_DURATION = 3.0


def dry_run():
    print('Target positions (x, y, z in metres):')
    for formation in ('line', 'v', 'circle'):
        print(f'  {formation.upper()}')
        for drone, pos in positions(formation).items():
            print(f'    {drone}: {pos}')
    for name, minimum in sorted(check_geometry()):
        print(f'  {name} minimum target separation: {minimum:.3f} m')
    print('Straight-line transition check passed (geometric check, not collision avoidance).')


def run():
    from crazyflie_py import Crazyswarm

    # The Crazyswarm constructor waits until the ROS server is available.
    swarm = Crazyswarm()
    by_name = swarm.allcfs.crazyfliesByName
    available = set(by_name)
    expected = set(DRONES)
    if available != expected:
        raise RuntimeError(
            f'Expected exactly {sorted(expected)}, found {sorted(available)}. '
            'Stop the server and relaunch with the generated crazyflies.yaml.'
        )
    clock = swarm.timeHelper
    print('Three drones connected to ROS services. Taking off...')
    airborne = False
    try:
        swarm.allcfs.takeoff(targetHeight=1.0, duration=TAKEOFF_DURATION)
        airborne = True
        clock.sleep(TAKEOFF_DURATION + 1.0)

        for name in ('line', 'v', 'circle', 'line'):
            print(f'Formation: {name}')
            for drone, target in positions(name).items():
                by_name[drone].goTo(list(target), yaw=0.0, duration=MOVE_DURATION)
            clock.sleep(MOVE_DURATION + 1.0)
        print('Formation cycle complete.')
    finally:
        if airborne:
            print('Sending landing command...')
            swarm.allcfs.land(targetHeight=0.04, duration=LAND_DURATION)
            clock.sleep(LAND_DURATION + 1.0)
    print('Demo finished.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--dry-run', action='store_true', help='Check coordinates, do not connect to ROS')
    choice.add_argument('--run-sim', action='store_true', help='Run the flight demo (simulation ONLY)')
    args, unknown = parser.parse_known_args()  # allows ROS's --ros-args to pass through
    if unknown and not (unknown[0] == '--ros-args' or unknown[0].startswith('__')):
        parser.error(f'Unexpected arguments: {unknown}')
    dry_run()
    if args.run_sim:
        run()


if __name__ == '__main__':
    main()
