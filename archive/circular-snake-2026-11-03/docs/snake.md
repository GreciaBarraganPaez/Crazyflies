# Snake prototype — optional simulation mode

The existing formation launcher and its default mode are preserved. Use
`Start-SwarmGesture.cmd` for heart, sine, the constant-size rotating spiral and
moon phases. Use **Start-SwarmGesture-Snake.cmd** for the separate Snake scene.
Only one simulator/bridge/marker session may run at a time.

## Start and controls

1. Land in the current session. Stop bridge, webcam and markers, then ROS last.
2. Double-click `Start-SwarmGesture-Snake.cmd`. It opens the same four-terminal
   arrangement, using the Snake server/controller/markers and a separate RViz view.
3. Wait for Listening on UDP. Enter `a` in the bridge terminal and press Enter.
4. Click the webcam and press E to enable sending. Show one finger to take off.
5. Show peace to start clockwise travel, or three fingers for counterclockwise.
6. Show OK to stage the next available drone for collection.

| Input | Snake behavior |
| --- | --- |
| `a` + Enter | Arm one takeoff; required again after landing |
| One finger | Take off to the existing airborne grid |
| Peace / `cw` + Enter | Start or change to clockwise travel |
| Three fingers / `ccw` + Enter | Start or change to counterclockwise travel |
| OK / `collect` + Enter | Stage the next waiting drone; it joins when the head reaches its pickup zone |
| Fist / `grid` + Enter | Return to the airborne grid and hover |
| Palm / `x` + Enter | Return to the verified grid, then land |
| `snake` + Enter | Start clockwise travel from the airborne grid |
| `count 3..19` | Set the maximum chain size while grounded; for example `count 19`; disarms takeoff |
| `status` | Show state, chain size, configured limit and arming |
| `q` + Enter | Quit through the controlled landing sequence |

Default: three moving chain drones, two collectible drones and fourteen dim
parked drones. The unchanged fleet configuration still contains all nineteen;
all take off together and return/land together. `count 3` disables collection;
`count 19` makes all remaining drones collectible. Count resets to five when
the bridge restarts. Select count before arming.

The head follows a predefined 24-second circular path in the front X-Z plane.
Followers run the same path with a time delay, giving about 0.90 m adjacent
center spacing on the circle. Direction changes use checked depth-lane morphs;
they do not reverse velocity abruptly or send the fleet back through the grid.
This first prototype provides direction selection, not freehand steering or
a grid-based Snake board.

## Collection and visual roles

Gold = head; teal = body; purple = available waiting drones; green = the staged
pickup; dim blue = parked drones outside this scene's configured limit. The
track, noncontact pickup zone, chain length and score appear in RViz. All drone
spheres/halos remain frame-locked to their TF frames.

Press OK once to move a waiting drone to the pickup zone. The chain keeps
moving. The head passes within 1.16 m of that drone (the nearest head-to-pickup
center distance is 1.10 m), then the new drone takes a checked path through depth
and joins behind the tail. The score increases only after joining finishes.
Collection is proximity-based; the drones do not touch. A pickup may wait up
to one circuit for the head. Press OK again after joining to collect another.

Requests to change direction or collect during another scene move are rejected
with a message; wait until it finishes. Palm can interrupt entry, collection,
or a direction change. It supersedes pending scene work with a checked route
to HOME. A later fist or collection request cannot cancel a pending landing.
On a rejected return route, the old motion remains active and the terminal
reports the failure; inspect it and request landing again.

## Preserving and switching back

The default launcher, gesture classifier, formation motion models and saved
formation RViz view are retained. New code lives in `simulation/scenes/`,
`runtime/snake_scene.py`, and the three Snake entry scripts. The optional mode
is selected by launch arguments; it is not added to the formation registry or
to the existing formation demo sequence.

To switch back, land and stop Snake's four programs, then use
`Start-SwarmGesture.cmd`. For a Snake controller-only restart after landing
and stopping it, use `Restart-SwarmGesture-Snake-Bridge.cmd`.

`archive/formation-baseline-2026-11-03/` preserves 48 source/configuration files
for the existing formation mode with SHA-256 checksums. This is a source snapshot,
not a full asset/runtime backup. Existing data and trained models were unchanged.

## Architecture and validation

- `scenes/snake.py`: immutable scene snapshots, actor roles, analytic head/body
  path, pickup proximity rules and collection/turn/return plans.
- `scenes/trajectories.py`: shared time-aligned quintics, 3D detours and full-curve
  conservative separation/height certificates for all nineteen actors.
- `runtime/snake_scene.py`: asynchronous scheduled planning, native firmware
  state forecasting, commitment checks, program chaining and scene events.
- `snake_preview_server.py`: ROS adapter for the scene. Formation-controller
  capability is disabled here to prevent attaching the wrong controller.
- `snake_controller.py`: gesture/keyboard intent and shared manual arming,
  takeoff, fresh-pose grid gate and landing lifecycle.
- `snake_markers.py`: role colors, track, pickup zone and score overlay.

Plans must certify >=0.52 m center separation and altitude >0.6 m over their
complete polynomial curves, including parked/waiting actors. Uncertain plans
are rejected while current motion continues. The runtime schedules joins 0.60
simulation seconds ahead, checks installed-firmware p/v/a before commitment,
and uploads finite high-level trajectories. It does not stream flight commands
per frame. Native buffers are reused for the three-piece and 96-piece programs.

Run offline checks from the project root:

```powershell
python -m unittest discover -s simulation -p "test_*.py" -v
```

In a configured WSL shell, from simulation/:

```bash
ROS_DOMAIN_ID=89 python3 check_snake_preview.py --limit 5 --report ../reports/simulation/snake-5.json
ROS_DOMAIN_ID=89 python3 check_snake_preview.py --limit 19 --report ../reports/simulation/snake-19.json
```

Run these sequentially on the isolated domain. They create their own server and
invoke its callbacks; they do not command the user's live simulator. Both checks
cover following, collection, direction change, fist return, restart from grid,
and palm landing during active pickup. The nineteen-drone run performs all
sixteen collections. The existing four-formation integration also passes.
Reports live in `reports/simulation/`.

This is ideal-motion simulation validation. It does not establish physical
rotor/body clearance or tolerance for real tracking errors. Snake is disabled
for the physics/hardware profiles in this prototype.
