#!/usr/bin/env bash
set -eo pipefail
if pgrep -f '^python3 (drone_markers|snake_markers|play_snake_markers)\.py( |$)' >/dev/null; then
    echo 'A marker publisher is already running; stop it before switching modes.' >&2
    exit 2
fi
source /opt/ros/jazzy/setup.bash
cd "$(dirname "${BASH_SOURCE[0]}")"
exec python3 play_snake_markers.py --ros-args -p use_sim_time:=true
