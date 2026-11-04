# SwarmGesture — animation crash fix (19 drones)

This is a **simulation-only** fix for `ValueError: goTo from low-level modes not yet supported` in the Crazyswarm2 `backend:=sim` implementation. Replaces the low-level `cmdFullState` animation stream with repeated high-level `goTo` targets, so subsequent grid moves and landing remain possible. This is a tradeoff: movement may be less fluid, but avoids the unsupported mode transition. **Not for real drones.**

## Replace files

Extract this ZIP **into your repository root** so these files replace the existing versions:

- `simulation/animated_shapes.py` — same original shape coordinates at t=0; heart pulses visibly (±20% width), spiral expands/contracts more
- `simulation/gesture_bridge.py` — high-level-only animation controller
- `simulation/test_animated_shapes.py` — revised tests for the new controller (replaces tests for low-level streaming)

**Do not replace** `static_shapes.py`, `configure_swarm.py`, `drone_markers.py` or `gesture_sender.py`.

## Check offline

From your `simulation/` directory in Ubuntu:

```bash
python3 animated_shapes.py
python3 -m unittest test_static_shapes.py test_animated_shapes.py -v
```

## Launch (same four terminals)

1. Ubuntu 1, from `simulation/`:

```bash
ros2 launch crazyflie launch.py \
  backend:=sim rviz:=True teleop:=False mocap:=False \
  crazyflies_yaml_file:="$(realpath config/crazyflies.yaml)"
```

2. Ubuntu 2, from `simulation/`:

```bash
python3 gesture_bridge.py --run-sim --fast-test \
  --step-sec 1.0 --lookahead-sec 1.35 --speed 1.0 \
  --ros-args -p use_sim_time:=true
```

Type `a` then Enter to arm.

3. Ubuntu 3, from `simulation/`: colored markers (unchanged):

```bash
python3 drone_markers.py --palette rainbow --ros-args -p use_sim_time:=true
```

4. Windows PowerShell, from the project root:

```powershell
$WSL_IP = ((wsl -d SwarmGesture-Ubuntu -- hostname -I) -split '\s+')[0]
python .\gesture_sender.py --model models/gesture_svm_mirrored.joblib --send --host $WSL_IP
```

Click the camera window and press `E` to enable transmission.

Gestures: one=takeoff, peace=heart, three=sine, OK=spiral, fist=grid, palm=grid then landing.

If you still use your old command with `--rate 20`, this version accepts that argument but ignores it. It no longer sends `cmdFullState` at 20 Hz. To trade motion smoothness for fewer ROS requests, change `--step-sec` (default 1.0; allowed 0.8–3.0), and keep `--lookahead-sec` between 1.0× and 1.7× the step value. Repeat `goTo` commands are *not guaranteed* to be perfectly smooth in the simulator.

For safety, no collision avoidance or measured-position verification is implemented. GoTo-based motion is a **compatibility workaround**, not the final trajectory architecture.
