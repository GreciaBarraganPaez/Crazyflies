# Active simulation

Use `../Start-SwarmGesture.cmd` for the normal four-terminal fast preview.
See [launcher and restart instructions](../docs/launching.md).

## Manual WSL startup

From this folder, in separate WSL terminals:

```bash
bash start_ros.sh preview
bash start_bridge.sh animations
bash start_markers.sh
```

The commands above belong in three separate terminals. Windows webcam commands
remain in the project root; the one-click launcher resolves the WSL IP for you.
Use `bash start_ros.sh physics` for the packaged NumPy physics backend, which
runs substantially slower on this machine. Never start two simulator servers or
bridges at once. The scripts reject duplicates and use Linux line endings.

The default bridge is `smooth_animation_bridge.py`. It requires the current
`preview_server.py`, uploads C2-continuous trajectories before Listening, and
plays them at 50 Hz. At 1x: heart 3.2-second period; sine 6 seconds; spiral 8 seconds; moon 10 seconds. The stepped
controllers remain active dependencies and the physics fallback.

## Checks

From the project root:

```bash
python -m unittest discover -s simulation -p "test_*.py" -v
```

From simulation/ in a ROS-configured WSL shell:

```bash
python3 check_continuous_backend.py
python3 check_heart_backend.py
```

These create isolated firmware planner objects without commanding the live fleet.
For the live **ideal preview only**, stop the interactive bridge first:

```bash
python3 check_live_preview.py --ros-args -p use_sim_time:=true
```

That check reserves UDP 5055, verifies the ideal backend, deliberately arms and
moves the simulated fleet through heart/wave transitions, and lands via grid.
It refuses to run alongside an interactive bridge. Measured separation from
one run does not guarantee physical body/rotor clearance or collision avoidance.

Archived 7/18-drone experiments are outside this folder and excluded from tests.


The saved `config/swarmgesture.rviz` loads the colored MarkerArray automatically
in preview and physics modes. The marker publisher still needs to be running.


Joined shape changes are planned by `blended_transitions.py` and scheduled by
`preview_server.py`, continuing position/velocity/acceleration into the next
loop without a separate braking/aligning waypoint. Restart ROS and bridge after
this server update. Isolated server integration check (no live fleet commands):

```bash
ROS_DOMAIN_ID=88 python3 check_blended_preview.py
```


## Playback controls and adding formations

In the bridge terminal: `speed 0.5..1.25` while grounded (for example
`speed 0.75`), then arm again. After manual takeoff, `demo` cycles the registered
formations; `demo off` keeps the current motion, and `status` prints current
settings. Any gesture or landing cancels the demo. Settings reset on restart.

`formation_registry.py` holds common metadata. Pure animation models live in
`formations/`, separate from ROS and flight lifecycle. See the
[extension guide and architecture review](../docs/architecture.md) and the
[product roadmap](../docs/roadmap.md) before adding more silhouettes or games.

Longer isolated checks, from this folder in the configured WSL shell:

```bash
ROS_DOMAIN_ID=88 python3 check_blended_preview.py --demo-rounds 2 --speed 1.25 --report ../reports/simulation/demo-1.25x.json
ROS_DOMAIN_ID=88 python3 check_blended_preview.py --demo-rounds 1 --speed 0.5 --report ../reports/simulation/demo-0.5x.json
ROS_DOMAIN_ID=88 python3 check_blended_preview.py --switches 30 --speed 1.25 --seed 20261102 --report ../reports/simulation/random-1.25x.json
```

Run these checks sequentially; they all reserve the isolated ROS domain 88.
Reports contain simulation duration, completed targets, speed and measured
minimum center spacing/airborne height. Each check also asserts grid landing,
no intermediate goTo during formation changes and no rejected transitions.
`check_continuous_backend.py` now checks 0.5x, 1x and 1.25x for 3 and 19 drones.


Moon phases: after manual takeoff, enter `moon` + Enter in the preview bridge.
The outline changes smoothly between full and half moon over a 10-second cycle
at 1x. It is also included in `demo`. Existing hand gestures are unchanged;
no new webcam gesture has been trained. `heart`, `sine` and `spiral` also work
as keyboard formation commands. This update requires a full restart after landing:
stop bridge, markers and webcam, then ROS last; run Start-SwarmGesture.cmd again.


## Optional Snake scene

The separate eight-drone **hand-controlled game** uses
`tools/launch/Start-SwarmGesture-Snake-Player.cmd`, or these three WSL programs with the
Windows sender started using `--snake-player`:

```bash
bash start_ros.sh preview True snake-player
bash start_bridge.sh snake-player
bash start_play_snake_markers.sh
```

Its fleet YAML, RViz view, player scene, input topic and steering runtime are
separate from the existing nineteen-drone modes. See [Hand Snake](../docs/snake-player.md).

Normal startup still selects formations. `tools/launch/Start-SwarmGesture-Snake.cmd` selects
an independent scene server/controller/marker view after stopping the current
session. Manual startup in separate WSL terminals:

```bash
bash start_ros.sh preview True snake
bash start_bridge.sh snake
bash start_snake_markers.sh
```

The Windows webcam sender stays unchanged. See [Snake controls](../docs/snake.md)
for winding routes, automatic two-snake splitting, new-head growth, multiple
apples, static borders and isolated checks.
