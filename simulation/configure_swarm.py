#!/usr/bin/env python3
"""Create a local three-Crazyflie config based on the installed Jazzy config.

This does not modify /opt/ros or the system's default Crazyflie config.
"""
from pathlib import Path
import copy
import yaml

SOURCE = Path('/opt/ros/jazzy/share/crazyflie/config/crazyflies.yaml')
DEST = Path(__file__).resolve().parent / 'config' / 'crazyflies.yaml'

# 0.8 metre spacing provides clear separation for the demonstration.
DRONES = {
    'cf231': ('radio://0/80/2M/E7E7E7E7E7', [-0.8, 0.0, 0.0]),
    'cf232': ('radio://0/80/2M/E7E7E7E7E8', [ 0.0, 0.0, 0.0]),
    'cf233': ('radio://0/80/2M/E7E7E7E7E9', [ 0.8, 0.0, 0.0]),
}


def main():
    if not SOURCE.exists():
        raise SystemExit(f'Missing installed Crazyswarm2 config: {SOURCE}')
    with SOURCE.open(encoding='utf-8') as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict) or 'robot_types' not in config:
        raise SystemExit('Unexpected ROS config structure; inspect the installed crazyflies.yaml')
    previous_robots = config.get('robots', {})
    if not previous_robots:
        raise SystemExit('The installed Crazyswarm2 config contains no example robots.')
    # Preserve the other ROS settings (robot_types, all, broadcasts, etc.).
    template = copy.deepcopy(previous_robots.get('cf231') or next(iter(previous_robots.values())))
    config['robots'] = {}
    for name, (uri, position) in DRONES.items():
        robot = copy.deepcopy(template)
        robot['enabled'] = True
        robot['uri'] = uri
        robot['initial_position'] = position
        robot['type'] = 'cf21'
        config['robots'][name] = robot
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with DEST.open('w', encoding='utf-8') as stream:
        yaml.safe_dump(config, stream, sort_keys=False)
    print(f'Created {DEST}')
    for name, (uri, position) in DRONES.items():
        print(f'  {name}: initial_position={position}, URI={uri}')
    print('This config is for simulation only. Do not use its sample URIs for real drones.')


if __name__ == '__main__':
    main()
