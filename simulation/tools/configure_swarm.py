#!/usr/bin/env python3
"""Generate 19 simulated Crazyflies in a centered 6/7/6 starting grid; no real radios."""
import copy
from pathlib import Path
from simulation.core.paths import CONFIG_DIR
import yaml
from simulation.core.static_shapes import DRONES, HOME

SOURCE = Path('/opt/ros/jazzy/share/crazyflie/config/crazyflies.yaml')
DEST = CONFIG_DIR / 'crazyflies.yaml'
BASE_URI = int('E7E7E7E7E7', 16)


def main():
    if not SOURCE.exists():
        raise SystemExit(f'Missing ROS configuration template: {SOURCE}')
    with SOURCE.open(encoding='utf-8') as fh:
        config = yaml.safe_load(fh)
    if not isinstance(config, dict) or 'robot_types' not in config or not config.get('robots'):
        raise SystemExit('Unexpected Crazyswarm2 configuration template')
    template = copy.deepcopy(config['robots'].get('cf231') or next(iter(config['robots'].values())))
    config['robots'] = {}
    for i, (name, (x, y, _)) in enumerate(zip(DRONES, HOME)):
        robot = copy.deepcopy(template)
        robot.update(enabled=True, type='cf21',
                     uri=f'radio://0/80/2M/{BASE_URI + i:010X}',
                     initial_position=[float(x), float(y), 0.0])
        config['robots'][name] = robot
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with DEST.open('w', encoding='utf-8') as fh:
        yaml.safe_dump(config, fh, sort_keys=False)
    print(f'Created {DEST} with {len(DRONES)} simulated drones: {DRONES[0]} ... {DRONES[-1]}')
    print('Starting positions: 6/7/6 symmetric ground grid (XY).')
    print('Airborne shapes: upright X-Z silhouettes at y=0, viewed from the front.')
    print('SIMULATION ONLY. Generated radio URIs are placeholders, NOT real drone addresses.')


if __name__ == '__main__':
    main()
