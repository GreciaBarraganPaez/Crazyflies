# Winding Snake with automatic splitting

Use **tools/launch/Start-SwarmGesture-Snake.cmd** for this game. The normal
**Start-SwarmGesture.cmd** still runs the existing heart, sine, constant-size
spiral and moon formations.

## Start and controls

This update changes the Snake server, controller and marker publisher.
Land, stop bridge/webcam/markers, then ROS last, and restart with the Snake
launcher. A bridge-only restart cannot load these changes.

1. Wait for Listening on UDP. Enter `a` + Enter to arm.
2. Enable webcam sending with E, then show one finger to take off.
3. Show peace, three or OK once, or enter `snake`, to start automatic play.

No steering or collect commands are needed. Fist or `grid` returns to the airborne
grid. Palm or `x` returns to the verified grid and lands. `q` quits through that
landing sequence. After landing, `a` is required before the next takeoff.

`count 3..15` and `seed INTEGER` may be set while grounded; they disarm takeoff.
Default count is 15 and seed is 31. `status` shows current game state. Restarting
the bridge resets these choices. Four drones are always reserved for the border.

## Visible layout

The scene uses the unchanged nineteen-drone fleet:

- Three drones initially form the snake: one gold head and two teal body drones.
- Twelve red drones are already visible as apples on the board.
- Four cyan drones hover at the actual board corners. They are not food.

The 12-column, 8-row board has 1.5 m cell spacing and an 18 m by 12 m border.
Its lower corner drones hover at z=1.15 m. The saved camera includes the full
board and caption. `count 8` gives five apples; lower counts leave unused game
drones parked outside the board. The maximum combined snake length is fifteen because
four of the nineteen drones remain border markers.

## Continuous motion and head identity

The route winds around a seeded maze instead of sweeping entire rows. A random
tree connects small grid loops into one continuous course with varied left and
right turns. The default full-board course has 36 turns. Set `seed INTEGER`
while grounded to choose a different reproducible layout.
Logical turns remain 90 degrees; physical direction
changes are rounded because exact sharp corners require zero speed. Shared
quintic route curves join in position, velocity and acceleration. Existing snake
actors never stop at cell or program boundaries during normal play.

The autonomous traversal covers the board and collects the visible apples in
route order. There are no manual collect commands. Apple positions are seeded
and separated to leave a checked handoff corridor before the next apple.

When the snake approaches an apple, that drone accelerates forward along the
same route. The existing snake closes the gap behind it without touching it.
The handoff waits until the previous head reaches the apple's original cell.
The apple then takes its group's head color and becomes the **new head**, with the previous head
as its first follower. Drone identities are retained; the apple is not sent to
the tail or swapped with another drone. A frame-locked HEAD label follows the
actual leading drone. Once all apples are eaten, the fleet automatically joins
the precertified return path and holds at the airborne grid. It does not land.
Show peace, three or OK to start another game from that grid, or palm to land.

Colors stay fixed by role: gold head and teal body for the first snake, purple
head and blue body for the second, red apples and cyan borders.
The experimental red pickup pulse has been removed.

## Automatic split at nine drones

At length nine, if apples remain, the original chain splits into groups of five and four. The
original tail group gains its own head; no drone is duplicated or removed.
A certified transition moves the groups into the left and right four-column
regions, redistributing the remaining apples between them. A wide central gap
separates their independent winding routes. All four border drones stay fixed
throughout the split. Position, velocity and acceleration join continuously at
both ends of the transition.

Each snake collects and grows independently, with the eaten drone becoming that
snake's head. With the default twelve apples, they finish at lengths eight and
seven. HEAD 1 and HEAD 2 labels and separate colors identify them. Counts up to
nine finish as one snake. The split occurs only once per game.

All body drones follow the same route curve with ordered offsets. The apple
starts moving when the head is one cell away, creating room for the handoff.
Existing actors maintain their normal speed through growth while the new head
continues forward. Their route speed stays positive; the collectible may start at rest,
but the existing body does not pause for it. Whole-fleet polynomial certificates
check the body, moving apple, remaining stationary apples and border drones.

## MarkerArray and saved RViz view

Snake now publishes a reliable **transient-local** MarkerArray snapshot at 20 Hz
and retains authoritative role/status snapshots. A late RViz subscriber receives
the last full marker set immediately. Sphere and halo positions remain attached
to each drone's TF frame with frame_locked=True.

The launcher loads **simulation/config/snake-smooth.rviz**, with MarkerArray
already enabled on `/swarmgesture/markers`, world as the fixed frame, explicit
scene/head namespaces, matching durability, and TF axes disabled. It is a fresh
view file so saving an older open snake.rviz window cannot overwrite it.
The normal formation RViz configuration and marker publisher are unchanged.

## Flight lifecycle and planning

Manual arming, takeoff and measured grid-first landing are shared with the
existing controller. A return request joins a pre-certified exit at the end of
the current program, preserving motion into the grid route. The next game
program is prepared ahead of time and starts at the exact previous time origin;
there is no rest tick between game programs. If planning cannot provide the next
certified path, a precomputed exit returns the fleet to the airborne grid rather
than freezing moving drones at an endpoint.

The runtime uses uploaded finite native trajectories, not per-frame flight
commands. Every full curve must certify center spacing >=0.52 m and altitude
>0.6 m. This is ideal preview only; physical rotor/body clearance and tracking
error are not established by these checks.

## Validation and preserved work

From the project root:

```powershell
python -m unittest discover -s simulation/tests -t . -p "test_*.py" -v
```

From the project root in a configured WSL shell, sequentially:

```bash
ROS_DOMAIN_ID=89 python3 -m simulation.checks.check_snake_preview --limit 8 --report reports/simulation/snake-winding-8.json
ROS_DOMAIN_ID=89 python3 -m simulation.checks.check_snake_preview --limit 15 --report reports/simulation/snake-split-15.json
ROS_DOMAIN_ID=89 python3 -m simulation.checks.check_snake_preview --limit 15 --seed 1 --return-during-split --report reports/simulation/snake-split-seed1.json
ROS_DOMAIN_ID=89 python3 -m simulation.checks.check_snake_markers
```

These create their own isolated server/controller and do not command the live
project. They check positive native body speed through corners and collections,
actual head-ID changes, all four corner positions, separation, no missed program
joins, grid return/restart, landing during growth, and manual rearming. The marker
check creates a genuine late subscriber and verifies the retained snapshot,
apple/border colors and the HEAD label after an identity change.

Formation mode, trained models and data remain preserved. Earlier Snake source
is archived under `archive/circular-snake-2026-11-03/` and
`archive/grid-snake-tail-growth-2026-11-03/`. The formation source/configuration
snapshot remains under `archive/formation-baseline-2026-11-03/`.
