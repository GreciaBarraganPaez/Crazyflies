# Hand-controlled Snake

Run **tools/launch/Start-SwarmGesture-Snake-Player.cmd** for the separate playable mode.
It uses **eight actual simulated drones**: three snake members and five visible
red apples. There is always one snake; it never splits. The board is a saved
10-by-8 grid with a static outline, so no drones are reserved as border markers.

The existing **tools/launch/Start-SwarmGesture-Snake.cmd** remains the nineteen-drone automatic
animation, including winding routes, two-snake splitting and automatic completion
return. Heart, sine, spiral and moon remain on **Start-SwarmGesture.cmd**.

## Starting and steering

Land and stop the four programs before switching modes. Start the new player
launcher and wait for Listening on UDP in the bridge terminal.

1. Enter `a` + Enter in the bridge terminal to arm.
2. Click the webcam window and press **E** to enable sending.
3. Show **one finger** to take off to the eight-drone airborne grid.
4. Show **peace** to start the game. Three or OK also starts it.
5. Point **one finger** and move your hand toward **LEFT**, **RIGHT**, **UP** or
   **DOWN** in the webcam view. These are absolute board directions. The playable
   view is mirrored so its hand movement matches the displayed direction.

The center rectangle means continue straight. A direction needs about 0.15 s of
stable hand position; repeated packets tolerate UDP loss. Neutral position,
tracking loss and gestures other than one finger send no new steering direction.
The snake continues its committed motion until a new valid turn or grid return.

Steer early: each cell takes 2.4 s, and rounded turns are planned ahead. A turn
updates the future path; it does not abruptly redirect a drone halfway through
a committed corner. Immediate 180-degree reversals and turns into the body are
ignored. If the requested turn is blocked, the snake continues straight when
that is clear. If no clear forward path can be certified, the game returns to
the airborne grid instead of moving into a wall, body or apple.

**Fist** returns to the airborne grid. **Palm** or keyboard **X** requests the
verified grid-first landing sequence; X also disables webcam sending. **Q** quits
the webcam with the existing best-effort landing request. Keyboard `x` + Enter
in the bridge lands; `q` + Enter performs controlled shutdown.

## Apples and completion

The eaten apple drone accelerates ahead and becomes the new gold head when the
previous head reaches its original cell. Existing body drones stay teal and
follow the same rounded path without stopping. Apples remain red until the
handoff. There is no traveling color pulse.

Collect all five apples to reach eight snake members. The fleet then returns
automatically to its airborne grid. Show peace to restart, or palm to land.
After any landing, manual arming with `a` is required again.

## Implementation and validation

- `simulation/scenes/play_snake.py`: independent eight-drone layout, trail,
  future turns, apple/head identity and certified trajectories.
- `simulation/runtime/play_snake.py`: prepares future turns without replacing
  current motion; uses the shared finite native-trajectory scheduler.
- `app/hand_steering.py`: pure four-zone hand-position gate. The sender enables it
  only with `--snake-player`; the six trained gesture labels are unchanged.
- `simulation/controllers/play_snake_controller.py`, `simulation/servers/play_snake_server.py`, `simulation/visualization/play_snake_markers.py`:
  separate input, scene and view; topics under `/swarmgesture/snake_player/`.
- `config/snake-player.yaml` and `config/snake-player.rviz`: separate fleet and
  saved view. The default nineteen-drone YAML is preserved.

Run the offline suite from the project root:

```powershell
python -m unittest discover -s simulation/tests -t . -p "test_*.py" -q
```

From the project root in a configured WSL shell:

```bash
ROS_DOMAIN_ID=89 python3 -m simulation.checks.check_play_snake
ROS_DOMAIN_ID=89 python3 -m simulation.checks.check_play_snake_markers
```

The native game test uses scripted directional input through the same controller
entry point as webcam UDP. It checks all four directions, all five pickups,
growth, one snake only, actual eight-drone count, positive body speed, full
collection return/restart, blocked-path return, palm during growth and manual
rearming. The marker test checks a genuinely retained snapshot, eight TF-bound
drones, five apples and the actual new head label. Human hand recognition still
depends on camera visibility and the existing SVM confidence threshold.

This remains ideal simulation. Whole-fleet trajectories must certify >=0.52 m
center separation and altitude >0.6 m; those checks do not establish physical
rotor clearance or real tracking performance.
