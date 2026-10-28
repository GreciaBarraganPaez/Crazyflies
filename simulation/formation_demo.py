#!/usr/bin/env python3
"""Run seven simulated Crazyflies: line -> V -> circle -> line -> land."""
import argparse
from formations import DRONES, FLIGHT_HEIGHT, check_geometry, positions

MOVE_DURATION = 6.0
TAKEOFF_DURATION = 3.0
LAND_DURATION = 3.0


def dry_run():
    print(f'{len(DRONES)} simulated drones; target coordinates (x, y, z in metres):')
    for name in ('line', 'v', 'circle'):
        print(f'  {name.upper()}')
        for drone, point in positions(name).items():
            print(f'    {drone}: {tuple(round(v, 3) for v in point)}')
    for name, minimum in sorted(check_geometry()):
        print(f'  {name} minimum target separation: {minimum:.3f} m')
    print('Geometric interpolation checked; no active collision avoidance.')


def run():
    from crazyflie_py import Crazyswarm
    swarm = Crazyswarm()
    by_name = swarm.allcfs.crazyfliesByName
    if set(by_name) != set(DRONES):
        raise RuntimeError(
            f'Expected {list(DRONES)}, got {sorted(by_name)}. '
            'Regenerate crazyflies.yaml and restart the simulator.')
    clock = swarm.timeHelper
    print(f'{len(DRONES)} simulated drones connected. Taking off...')
    airborne = False
    try:
        swarm.allcfs.takeoff(targetHeight=FLIGHT_HEIGHT, duration=TAKEOFF_DURATION)
        airborne = True
        clock.sleep(TAKEOFF_DURATION + 1)
        for name in ('line', 'v', 'circle', 'line'):
            print(f'Formation: {name}')
            for drone, goal in positions(name).items():
                by_name[drone].goTo(list(goal), yaw=0.0, duration=MOVE_DURATION)
            clock.sleep(MOVE_DURATION + 1)
        print('Formation cycle complete.')
    finally:
        if airborne:
            print('Sending landing command...')
            swarm.allcfs.land(targetHeight=0.04, duration=LAND_DURATION)
            clock.sleep(LAND_DURATION + 1)
    print('Demo finished.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--run-sim', action='store_true')
    args, extra = parser.parse_known_args()
    if extra and extra[0] != '--ros-args':
        parser.error(f'Unexpected arguments: {extra}')
    dry_run()
    if args.run_sim:
        run()


if __name__ == '__main__':
    main()
