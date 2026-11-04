#!/usr/bin/env bash
# ROS 2 setup.bash expects some variables to be unset; do not enable `set -u` here.
set -eo pipefail
if pgrep -f '^python3 (drone_markers|snake_markers|play_snake_markers)\.py( |$)' >/dev/null; then
    echo 'Drone markers are already running. Stop that marker terminal before restarting it.' >&2
    exit 2
fi
source /opt/ros/jazzy/setup.bash
export PYTHONPATH="$HOME/.local/share/swarmgesture/python:$HOME/crazyflie-firmware/build:${PYTHONPATH:-}"
cd "$(dirname "${BASH_SOURCE[0]}")"
exec python3 drone_markers.py --palette auto \
    --ros-args -p use_sim_time:=true
