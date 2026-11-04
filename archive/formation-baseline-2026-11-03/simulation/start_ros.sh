#!/usr/bin/env bash
# ROS 2 setup.bash expects some variables to be unset; do not enable `set -u` here.
set -eo pipefail
if pgrep -f '^(/usr/bin/python3 /opt/ros/jazzy/lib/crazyflie_sim/crazyflie_server|/usr/bin/python3 .*/(preview_server|snake_preview_server)\.py)( |$)' >/dev/null; then
    echo 'The ROS simulator is already running. Reuse it for a bridge-only restart, or stop terminal 1 before changing profiles.' >&2
    exit 2
fi
source /opt/ros/jazzy/setup.bash
export PYTHONPATH="$HOME/.local/share/swarmgesture/python:$HOME/crazyflie-firmware/build:${PYTHONPATH:-}"
cd "$(dirname "${BASH_SOURCE[0]}")"

# WSLg provides the Windows display for Linux GUI applications (RViz).
# DISPLAY should be :0 on a normal WSLg installation.
export DISPLAY="${DISPLAY:-:0}"
printf 'WSLg display: DISPLAY=%s\n' "$DISPLAY"
if [[ ! -S /tmp/.X11-unix/X0 ]]; then
    echo 'ERROR: WSLg X11 socket /tmp/.X11-unix/X0 was not found.'
    echo 'Close the launcher windows and run Start-SwarmGesture-Clean.cmd.'
    echo 'This resets WSL (also stops other WSL applications, including Docker).'
    exit 2
fi
# Prefer RViz's X11 backend on WSLg rather than native Wayland.
export QT_QPA_PLATFORM=xcb

if [[ ! -f config/crazyflies.yaml ]]; then
    echo 'Missing config/crazyflies.yaml. Generate it with: python3 configure_swarm.py'
    exit 1
fi
if [[ ! -f config/swarmgesture.rviz ]]; then
    echo 'Missing project RViz configuration: config/swarmgesture.rviz' >&2
    exit 1
fi
profile="${1:-preview}"
rviz="${2:-True}"
scene="${3:-formations}"
case "$scene" in formations|snake) ;; *) echo "Unknown scene: $scene" >&2; exit 2 ;; esac
if [[ "$scene" == snake && "$profile" != preview ]]; then echo "Snake requires preview" >&2; exit 2; fi
case "$rviz" in True|False) ;; *) echo "rviz must be True or False" >&2; exit 2 ;; esac
if [[ "$profile" == preview ]]; then
    echo 'CHOREOGRAPHY PREVIEW: ideal motion, paced at ~real time; no physics simulation.'
    rviz_config="$(realpath config/swarmgesture.rviz)"
    if [[ "$scene" == snake ]]; then rviz_config="$(realpath config/snake.rviz)"; fi
    exec ros2 launch ./choreography_preview.launch.py "rviz:=$rviz" "scene:=$scene" "rviz_config_file:=$rviz_config"
elif [[ "$profile" != physics ]]; then
    echo "Unknown simulation profile: $profile" >&2
    exit 2
fi
exec ros2 launch crazyflie launch.py \
    backend:=sim "rviz:=$rviz" teleop:=False mocap:=False \
    "crazyflies_yaml_file:=$(realpath config/crazyflies.yaml)" \
    "rviz_config_file:=$(realpath config/swarmgesture.rviz)"
