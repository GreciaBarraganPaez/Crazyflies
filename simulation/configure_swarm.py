#!/usr/bin/env python3
"""Generate a SEVEN-drone Crazyswarm2 simulation config from ROS Jazzy defaults.

This never changes the ROS installation. Example radio URIs are placeholders,
NOT verified physical drone addresses. Run with backend:=sim ONLY.
"""
from pathlib import Path
import copy
import yaml
from formations import DRONES, positions

SOURCE = Path('/opt/ros/jazzy/share/crazyflie/config/crazyflies.yaml')
DEST = Path(__file__).resolve().parent / 'config' / 'crazyflies.yaml'
BASE_URI = int('E7E7E7E7E7', 16)


def main():
    if not SOURCE.exists():
        raise SystemExit(f'Missing installed Crazyswarm2 config: {SOURCE}')
    with SOURCE.open(encoding='utf-8') as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict) or 'robot_types' not in config:
        raise SystemExit('Unexpected installed crazyflies.yaml structure.')
    original = config.get('robots', {})
    if not original:
        raise SystemExit('Missing robot template in the installed configuration.')
    template = copy.deepcopy(original.get('cf231') or next(iter(original.values())))
    config['robots'] = {}
    starting = positions('line')
    for i, drone in enumerate(DRONES):
        robot = copy.deepcopy(template)
        robot['enabled'] = True
        robot['uri'] = f'radio://0/80/2M/{BASE_URI + i:010X}'
        robot['initial_position'] = [starting[drone][0], 0.0, 0.0]
        robot['type'] = 'cf21'
        config['robots'][drone] = robot
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with DEST.open('w', encoding='utf-8') as stream:
        yaml.safe_dump(config, stream, sort_keys=False)
    print(f'Created {DEST} with {len(DRONES)} drones: {", ".join(DRONES)}')
    for name, robot in config['robots'].items():
        print(f'  {name}: initial_position={robot["initial_position"]}')
    print('SIMULATION ONLY. Placeholder radio addresses must not be used with hardware.')


if __name__ == '__main__':
    main()
