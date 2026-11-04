# SwarmGesture

Hand gestures control **19 simulated Crazyflies** (`cf231`â€“`cf249`). Windows
runs MediaPipe hand tracking and a trained SVM; UDP sends stable gesture labels
to ROS 2 Jazzy/Crazyswarm2 in the `SwarmGesture-Ubuntu` WSL distribution.

The current demo uses RViz with smooth colored markers and an ideal-motion
preview: a continuous pulsing heart, travelling sine wave and constant-size rotating spiral, plus a full-to-half moon outline and a moving 3D helix.
Colors follow the actual formation: a deep-to-bright red heart glow, a traveling rainbow wave, calm cyan grid and a traveling gold-purple spiral gradient. Physical flight has
not been validated.

## Start

Double-click **Start-SwarmGesture.cmd** in this folder. It opens the four demo
terminals. Wait for **Listening on UDP** in the bridge, enter **a + Enter** to
arm, then click the webcam window and press **E** to enable gesture sending.

| Gesture | Action |
| --- | --- |
| One finger | Take off |
| Peace | Continuous pulsing heart |
| Three fingers | Travelling sine wave |
| OK | Spiral rotates back and forth at constant size (8-second cycle) |
| Fist | Return to airborne grid |
| Open palm | Verified grid return, then landing |

Fast-preview shape changes join the outgoing motion through checked depth
lanes into the next animation, without a separate brake or alignment pause.
Landing keeps the grid-first sequence. Preview runs at 50 Hz;
at 1x: heart period is 3.2 seconds, wave 6 seconds, spiral 8 seconds and moon 10 seconds.

In the bridge terminal, enter `speed 0.75` or `speed 1.25` while grounded
(range 0.5-1.25; resets to 1x on restart). Arm again afterward. After takeoff,
enter `demo` to cycle heart -> sine -> spiral -> moon -> helix, `demo off` to keep the current
formation, or `status`. Any gesture or landing request cancels demo mode.

See [launcher and restart instructions](docs/launching.md) for the physics
fallback, keyboard controls, diagnostics and recovery.

## Project layout

| Location | Purpose |
| --- | --- |
| **`Start-SwarmGesture.cmd`** | Normal formation startup; use this every day |
| **`SwarmGesture-Tools.cmd`** | Optional games, physics, bridge restarts and WSL recovery menu |
| `app/` | Windows webcam recognition, feature extraction, gesture filtering and hand steering |
| `simulation/` | ROS controllers, formations, trajectories, simulation configuration and checks |
| `tools/gestures/` | Record data, train models, preview predictions and inspect hand landmarks |
| `tools/launch/` | Shared PowerShell launcher and optional mode/recovery shortcuts |
| `models/` | Trained classifiers and the required `hand_landmarker.task` MediaPipe asset |
| `data/`, `reports/` | Collected landmarks and evaluation/validation evidence |
| `docs/` | Controls, launching, architecture and the historical learning journal |
| `archive/` | Preserved earlier experiments and source snapshots |

Only the normal start shortcut is needed for the formation demo. The tools menu
collects the optional launchers that previously filled this folder. For an
explanation of every moved Python/CMD file, see [the file guide](docs/project-map.md).

The mirrored classifier `models/gesture_svm_mirrored.joblib` and
`models/hand_landmarker.task` are required local assets. Existing datasets and
models are preserved. `requirements.txt` lists Windows Python dependencies;
the working ROS/Crazyswarm2 runtime remains in WSL.

## Validate

From the project root, offline tests require no ROS or webcam:

```powershell
python -m unittest discover -s simulation/tests -t . -p "test_*.py" -v
```

Installed-firmware and live-preview checks are documented in
[simulation/README.md](simulation/README.md). Separation tests cover planned
point trajectories and measured ideal-preview runs; they do not establish
collision avoidance for physical drones or physics tracking errors.

## Documentation

- [Architecture and extension guide](docs/architecture.md)
- [End goal and roadmap](docs/roadmap.md)
- [Gesture controls](docs/gesture-control.md)
- [Project plan (historical)](docs/project.md)
- [Learning journal](docs/learning-journal.md)
- [Archived experiments](archive/README.md)

AI Project, Master AIR2, Hof University, winter semester 2026/27.


Moon phases: after manual takeoff, enter `moon` + Enter in the preview bridge.
The outline changes smoothly between full and half moon over a 10-second cycle
at 1x. It is also included in `demo`. Existing hand gestures are unchanged;
no new webcam gesture has been trained. `heart`, `sine` and `spiral` also work
as keyboard formation commands. This update requires a full restart after landing:
stop bridge, markers and webcam, then ROS last; run Start-SwarmGesture.cmd again.


## Moving 3D helix

The formation preview now also includes a **moving 3D helix**. After takeoff,
type `helix` + Enter in the bridge terminal. In RViz, select the saved **3D Helix**
view to see the depth. See [Helix controls](docs/helix.md).

## Optional autonomous Snake

For the separate **eight-drone hand-controlled game**, use
**tools/launch/Start-SwarmGesture-Snake-Player.cmd**. Point one finger and move your hand
left/right/up/down to steer a single snake. See [Hand Snake](docs/snake-player.md).

**tools/launch/Start-SwarmGesture-Snake.cmd** starts continuous Snake with three initial body
drones, twelve visible red apples and four cyan border drones. Each eaten drone
becomes its group's new head; the body follows it without stopping at corners or
collections. Seeded winding routes replace the row sweep. At nine drones, the
chain splits into two snakes that collect apples in separate board regions,
growing to fifteen drones combined while the four border drones stay fixed.
The red pickup pulse has been removed; each group keeps fixed role colors.
After all apples are eaten, the fleet automatically returns to the airborne
grid, ready for another game or palm landing.

After manual takeoff, show peace, three or OK once to start. Fist returns to the
grid; palm lands. This update requires restarting all four Snake programs and
loads the fresh `snake-smooth.rviz` view with MarkerArray enabled automatically.
The normal launcher still selects the existing formations. See
[Snake controls and architecture](docs/snake.md).
