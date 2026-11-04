# Offline tests: fifteen files, 108 checks

These tests use fake fleets and motion maths. They do not open the webcam,
start a ROS server or send flight commands. They do not run during startup.

From the project root:

```powershell
python -m unittest discover -s simulation/tests -t . -p "test_*.py" -q
```

For one area, for example:

```powershell
python -m unittest simulation.tests.test_helix -q
```

| File | What it protects |
| --- | --- |
| `test_static_shapes.py` | Formation geometry, grid layout and basic flight controls |
| `test_continuous_trajectories.py` | Smooth piece/loop joins, spacing, height and speed scaling |
| `test_blended_transitions.py` | Full-curve separation and continuous formation changes |
| `test_transitions.py` | Checked resting/depth-lane transitions and feedback waits |
| `test_helix.py` | Actual 3D motion, derivatives, radius, colors and helix selection |
| `test_smooth_controller.py` | Continuous playback and stopping/landing behavior |
| `test_blended_controller.py` | Queued gestures and formation changes without a brake waypoint |
| `test_heart_animation.py` | Stepped heart controller used by the fallback |
| `test_formation_animation.py` | Stepped wave/controller fallback |
| `test_formation_colors.py` | Colors matching the actual formation pose/phase |
| `test_playback_controls.py` | Registry consistency, demo order, speed and command rules |
| `test_gesture_gate.py` | Stable gestures, cooldown and UDP input validation |
| `test_snake_scene.py` | Automatic Snake identities, winding routes, split and spacing |
| `test_snake_controller.py` | Automatic Snake controls and grid/landing priority |
| `test_play_snake.py` | Hand-position steering, eight-drone game, pickups and safe exits |

`helpers.py` contains the shared fake fleet and deterministic game-input
scenario. It contains no test cases and makes no ROS calls. Native checks reuse
those fixtures without importing whole unit-test modules.

Several files are needed because a geometry test cannot tell whether a queued
palm request was lost, and a controller test cannot prove an entire moving curve
keeps its separation. They cover complementary responsibilities.
