#!/usr/bin/env bash
# ROS 2 setup.bash expects some variables to be unset; do not enable `set -u` here.
set -eo pipefail
if pgrep -f '^python3 (gesture_bridge|heart_animation_bridge|formation_animation_bridge|smooth_animation_bridge|snake_controller)\.py( |$)' >/dev/null; then
    echo 'A bridge is already running. Land, stop that bridge with Ctrl+C, then restart only terminal 2.' >&2
    exit 2
fi
source /opt/ros/jazzy/setup.bash
export PYTHONPATH="$HOME/.local/share/swarmgesture/python:$HOME/crazyflie-firmware/build:${PYTHONPATH:-}"
cd "$(dirname "${BASH_SOURCE[0]}")"
mode="${1:-animations}"
case "$mode" in
    animations) controller=smooth_animation_bridge.py ;;
    heart) controller=heart_animation_bridge.py ;;
    static) controller=gesture_bridge.py ;;
    snake) controller=snake_controller.py ;;
    *) echo "Unknown formation mode: $mode (expected animations, heart, static or snake)" >&2; exit 2 ;;
esac
echo "SwarmGesture bridge: mode=$mode; controller=$controller"
exec python3 "$controller" --run-sim --fast-test \
    --ros-args -p use_sim_time:=true
