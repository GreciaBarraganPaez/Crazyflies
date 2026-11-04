#!/usr/bin/env bash
# ROS 2 setup.bash expects some variables to be unset; do not enable `set -u` here.
set -eo pipefail
if pgrep -f '^(/usr/bin/python3 /opt/ros/jazzy/lib/crazyflie_sim/crazyflie_server|/usr/bin/python3 .*/(preview_server|snake_preview_server|play_snake_server)\.py|(/usr/bin/python3|python3) -m simulation\.servers\.(preview_server|snake_preview_server|play_snake_server))( |$)' >/dev/null; then
    echo 'The ROS simulator is already running. Reuse it for a bridge-only restart, or stop terminal 1 before changing profiles.' >&2
    exit 2
fi
source /opt/ros/jazzy/setup.bash
export PYTHONPATH="$HOME/.local/share/swarmgesture/python:$HOME/crazyflie-firmware/build:${PYTHONPATH:-}"
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

# WSLg provides the Windows display for Linux GUI applications (RViz).
# DISPLAY should be :0 on a normal WSLg installation.
export DISPLAY="${DISPLAY:-:0}"
printf 'WSLg display: DISPLAY=%s\n' "$DISPLAY"
if [[ ! -S /tmp/.X11-unix/X0 ]]; then
    echo 'ERROR: WSLg X11 socket /tmp/.X11-unix/X0 was not found.'
    echo 'Close the launcher windows and use WSL recovery in SwarmGesture-Tools.cmd.'
    echo 'This resets WSL (also stops other WSL applications, including Docker).'
    exit 2
fi
# Prefer RViz's X11 backend on WSLg rather than native Wayland.
export QT_QPA_PLATFORM=xcb

if [[ ! -f simulation/config/crazyflies.yaml ]]; then
    echo 'Missing simulation/config/crazyflies.yaml. Generate it with: python3 -m simulation.tools.configure_swarm'
    exit 1
fi
if [[ ! -f simulation/config/swarmgesture.rviz ]]; then
    echo 'Missing project RViz configuration: simulation/config/swarmgesture.rviz' >&2
    exit 1
fi
profile="${1:-preview}"
rviz="${2:-True}"
scene="${3:-formations}"
case "$scene" in formations|snake|snake-player) ;; *) echo "Unknown scene: $scene" >&2; exit 2 ;; esac
if [[ "$scene" != formations && "$profile" != preview ]]; then echo "Snake requires preview" >&2; exit 2; fi
case "$rviz" in True|False) ;; *) echo "rviz must be True or False" >&2; exit 2 ;; esac
if [[ "$profile" == preview ]]; then
    echo 'CHOREOGRAPHY PREVIEW: ideal motion, paced at ~real time; no physics simulation.'
    rviz_config="$(realpath simulation/config/swarmgesture.rviz)"
    if [[ "$scene" == snake ]]; then rviz_config="$(realpath simulation/config/snake-smooth.rviz)"; fi
    if [[ "$scene" == snake-player ]]; then rviz_config="$(realpath simulation/config/snake-player.rviz)"; fi
    exec ros2 launch ./simulation/launch/choreography_preview.launch.py "rviz:=$rviz" "scene:=$scene" "rviz_config_file:=$rviz_config"
elif [[ "$profile" != physics ]]; then
    echo "Unknown simulation profile: $profile" >&2
    exit 2
fi
exec ros2 launch crazyflie launch.py \
    backend:=sim "rviz:=$rviz" teleop:=False mocap:=False \
    "crazyflies_yaml_file:=$(realpath simulation/config/crazyflies.yaml)" \
    "rviz_config_file:=$(realpath simulation/config/swarmgesture.rviz)"
