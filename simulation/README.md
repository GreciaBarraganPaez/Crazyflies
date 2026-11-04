# Simulation folder guide

For normal use, start **Start-SwarmGesture.cmd** in the project root.
Use **SwarmGesture-Tools.cmd** for games, physics and bridge restarts.
You do not need to run the Python files individually.

## What each folder contains

| Folder | Purpose | When to look here |
| --- | --- | --- |
| `formations/` | Heart, sine, spiral, moon and helix motion models | Adding/changing a formation |
| `controllers/` | Gesture/keyboard controls and takeoff/grid/landing behavior | Changing controls or flight stages |
| `servers/` | The ROS simulator entry points | Simulator/backend work |
| `core/` | Shared geometry, trajectory building, transition checks and formation registry | Motion planning work |
| `runtime/` | Runs prepared animations and scene trajectories over simulation time | Playback/scheduling work |
| `visualization/` | Drone colors, labels and RViz MarkerArray publishers | Visual changes |
| `scenes/` | Automatic Snake and playable Snake state/movement rules | Game changes |
| `config/` | Fleet YAML files and saved RViz views | Drone counts or camera/display setup |
| `launch/` | Bash startup scripts and the ROS launch description | Startup problems |
| `tools/` | Fleet configuration generator and manual UDP sender | Deliberate setup/diagnostic tasks |
| `tests/` | Fifteen focused offline test files plus shared fake-fleet helpers | Development checks; not normal startup |
| `checks/` | ROS/firmware integration and marker checks | Deeper validation; not normal startup |

The root `__init__.py` only identifies this as a Python package. Generated
`__pycache__/` folders are ignored caches, not additional source files.

## The scripts that actually run

| Mode | Controller | Server | Marker publisher |
| --- | --- | --- | --- |
| Normal formations | `controllers/smooth_animation_bridge.py` | `servers/preview_server.py` | `visualization/drone_markers.py` |
| Automatic Snake animation | `controllers/snake_controller.py` | `servers/snake_preview_server.py` | `visualization/snake_markers.py` |
| Hand-controlled Snake | `controllers/play_snake_controller.py` | `servers/play_snake_server.py` | `visualization/play_snake_markers.py` |

`controllers/gesture_bridge.py` supplies the shared flight lifecycle and UDP
loop. `heart_animation_bridge.py` and `formation_animation_bridge.py` retain the
stepped heart/wave behavior used by the physics fallback. They are still active
dependencies, not unused copies. Their tests remain for that reason.

Normal formations use nineteen drones. The playable Snake has its separate
eight-drone configuration. Modes keep their existing controls and startup menu.

## Why there are fifteen test files

Each file checks a different responsibility rather than mixing every behavior
into one long script. Together they contain **108 tests**: motion/derivatives,
complete-path spacing, controller transitions, gesture filtering, colors, demo
controls and both games. Keeping them helps catch regressions when adding a
formation or moving code. They are not loaded by the running simulation.

Run all offline checks from the **project root**:

```powershell
python -m unittest discover -s simulation/tests -t . -p "test_*.py" -q
```

See [the test guide](tests/README.md) for the file-by-file map and
[the integration check guide](checks/README.md) for checks that need WSL/ROS.

## Manual WSL startup

Normally use the root CMD files. If starting manually, run these from the
**project root** in three separate WSL terminals:

```bash
bash simulation/launch/start_ros.sh preview
bash simulation/launch/start_bridge.sh animations
bash simulation/launch/start_markers.sh
```

Use `physics` instead of `preview` for the slower physics profile. Use scene
`snake` or `snake-player` as the third ROS argument and corresponding bridge
mode/marker script when deliberately starting those modes. Do not run two modes
at once; startup guards recognize both the previous script paths and new modules.

Source code is imported through the `simulation` package. Developer commands
therefore use modules, for example `python3 -m simulation.checks.check_blended_preview`,
from the project root rather than executing moved files by their old paths.

## Formation controls

After manual takeoff: `heart`, `sine`, `spiral`, `moon`, `helix`, `demo`,
`demo off` and `status` work in the bridge terminal. Grounded `speed 0.5..1.25`
changes animation speed and disarms takeoff. Existing webcam gestures are
unchanged. Palm still returns to the measured grid before landing.

See [launching](../docs/launching.md), [architecture](../docs/architecture.md),
[3D helix](../docs/helix.md), [automatic Snake](../docs/snake.md) and
[hand-controlled Snake](../docs/snake-player.md).
