# Autonomous grid Snake

This replaces the circular Snake prototype. The formation mode remains separate:
`Start-SwarmGesture.cmd` still starts heart, sine, the constant-size rotating
spiral and moon phases. `Start-SwarmGesture-Snake.cmd` starts autonomous Snake.

## Start

1. Land and stop the current bridge, webcam and markers, then ROS last.
2. Run **Start-SwarmGesture-Snake.cmd**. A full restart is required for this
   update; the new controller checks the server's grid-Snake capability.
3. Wait for Listening on UDP, then enter `a` + Enter in the bridge terminal.
4. Enable webcam sending with E, then show one finger to take off.
5. Show peace, three fingers or OK once (or enter `snake`) to start the game.

The game chooses its route and eats food automatically. No steering or collection
commands are needed. Fist returns to the airborne grid; palm or `x` + Enter
returns to the verified grid and lands. After landing, enter `a` again before
using one finger. `q` exits through the landing sequence.

| Keyboard command | Meaning |
| --- | --- |
| `snake` | Start autonomous play from the airborne grid |
| `grid` | Return to the airborne grid and reset the board |
| `count 3..19` | Set maximum chain size while grounded; default 19 |
| `seed INTEGER` | Choose a reproducible food layout while grounded; default 31 |
| `status` | Show state, length, move count, arming and configured limit |
| `a` / `x` / `q` | Arm / grid-first landing / controlled quit |

Count and seed changes disarm takeoff and reset on bridge restart. Existing
six trained gesture labels are unchanged. Peace, three and OK all start the
same autonomous game; during play they do not steer or request food.

## Classic movement

The board has 8 columns and 6 rows in the front X-Z plane, with 1.2 m cell
spacing. Three drones initially form the snake. The head moves forward, turns
left 90 degrees or turns right 90 degrees. It never moves diagonally or reverses
into its neck. Every body drone occupies the head's previous cell/path history.

The autonomous policy uses a Hamiltonian board ordering with safe forward
shortcuts toward food. Moves must remain within the board, avoid the body, and
preserve ordering before the tail. New food is selected from reachable free
cells ahead of the head. A seeded choice varies the food layout reproducibly.
When all available drones are collected, the snake keeps moving around the board.

Ordinary body motion is strictly axis-aligned. Grid nodes are C2 rest states,
so drones slow for exact corners instead of instantly changing velocity.
Straight runs of up to three cells are combined when no body drone would cut a
corner, skip food or change role. A single 50 Hz rest tick resolves native
firmware endpoint precision before the next program starts. No circular track
or rounded corner shortcut remains in the game.

The classic mechanics are informed by [Snake rules](https://www.coolmathgames.com/0-snake):
food grows the body, walls/body are avoided, and turning replaces reversal.
Our version chooses the moves automatically and adapts collection for drones.

## Food and growth without contact

Gold is the head, teal is the body, red is food, and dim blue is parked. The
board, highlighted food cell, chain length and score appear in RViz. There is
one food drone at a time; other drones wait outside the board.

When the head advances into a food cell, the food drone first leaves the board
plane. It travels through depth and joins at the vacated tail position while
existing body drones advance one cell. If more drones remain, the next parked
drone simultaneously moves to a new free food cell on a separate depth route.
The complete nineteen-drone program, including both transfers and all parked
drones, must pass the separation certificate. No two drones need to touch or
occupy the same 3D position. Food transfers may use 3D paths; ordinary snake
head/body motion always follows straight board edges.

The score increments only after the physical growth program completes. A landing
request waits for the current checked step/collection to finish, then returns
all drones to HOME. Later start gestures cannot replace landing. Failed planning
holds the board safely and prints the reason; palm can still request landing.
This is a controlled landing request, not an emergency motor cutoff.

## Implementation

- `scenes/snake.py`: immutable body/food state, legal moves, autonomous policy,
  seeded food selection, role assignment and physical step/entry/return plans.
- `scenes/trajectories.py`: aligned quintic paths, 3D transfer detours and
  conservative whole-curve center-separation/height validation.
- `runtime/snake_scene.py`: one-step-ahead worker planning, finite native
  trajectory programs, firmware-state checks and automatic game progression.
- `snake_controller.py`: manual arming, start/return/landing input and status.
- `snake_markers.py`: frame-locked role markers, rectangular grid and food cell.
- `snake_preview_server.py`: scene ROS adapter; it refuses the formation controller.

Source-state checks use the installed firmware representation. Programs must
certify >=0.52 m center separation and height >0.6 m over the complete polynomial
curves. Unresolved paths are rejected. The game uses uploaded native programs,
not a per-frame stream of flight commands. It is limited to ideal preview;
physical body/rotor clearance and real tracking errors are not validated here.

## Validation

Run offline tests from the project root:

```powershell
python -m unittest discover -s simulation -p "test_*.py" -v
```

The policy is tested through full growth across 40 seeds, checking no reversal,
wall/body collision, diagonal step or incorrect history/growth. Path checks cover
right-angle movement, straight-run merging and physical food/tail transfer.

In a configured WSL shell, from simulation/ (run sequentially):

```bash
ROS_DOMAIN_ID=89 python3 check_snake_preview.py --limit 5 --report ../reports/simulation/snake-5.json
ROS_DOMAIN_ID=89 python3 check_snake_preview.py --limit 19 --report ../reports/simulation/snake-19.json
ROS_DOMAIN_ID=89 python3 check_snake_preview.py --limit 19 --seed 1 --report ../reports/simulation/snake-grid-seed1.json
ROS_DOMAIN_ID=89 python3 check_snake_markers.py
```

These checks use isolated server/controller/firmware objects and do not command
the user's live project. They validate actual axis-aligned body motion, automatic
collection, grid return/restart, landing during growth, and mandatory rearming.

## Preserved work

The normal formation launcher, models/data, geometry, animation models, colors
and saved formation view are retained. Stop Snake and use the normal launcher
to switch back. `Restart-SwarmGesture-Snake-Bridge.cmd` remains the controller-only
restart button for Snake after landing and stopping that bridge.

The retired circle prototype, its tests/view and earlier reports are preserved
with checksums under `archive/circular-snake-2026-11-03/`. The earlier formation
source snapshot remains under `archive/formation-baseline-2026-11-03/`.
