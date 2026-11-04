# SwarmGesture — static formations (19 drones)

Simulation only. Open **4 terminals**. Use the `simulation/` folder for Ubuntu commands and the project root for Windows commands.

## 1. Ubuntu — ROS + RViz

Open Ubuntu from PowerShell: `wsl -d SwarmGesture-Ubuntu`

```bash
cd "/mnt/c/Users/Marco/SynologyDrive/Hof/STUDIUM/Semester II/AI Project/MediaPipe Hand Landmarker/simulation"
ros2 launch crazyflie launch.py \
  backend:=sim rviz:=True teleop:=False mocap:=False \
  crazyflies_yaml_file:="$(realpath config/crazyflies.yaml)"
```

## 2. Ubuntu — static formation bridge

```bash
cd "/mnt/c/Users/Marco/SynologyDrive/Hof/STUDIUM/Semester II/AI Project/MediaPipe Hand Landmarker/simulation"
python3 gesture_bridge.py --run-sim --fast-test \
  --ros-args -p use_sim_time:=true
```

When it says `Listening`, press **a** + Enter to arm; **x** + Enter to return to grid and land.

## 3. Ubuntu — smooth colored drone markers

```bash
cd "/mnt/c/Users/Marco/SynologyDrive/Hof/STUDIUM/Semester II/AI Project/MediaPipe Hand Landmarker/simulation"
python3 drone_markers.py --palette rainbow \
  --ros-args -p use_sim_time:=true
```

RViz: Fixed Frame = `world`; enable `/swarmgesture/markers` (MarkerArray); hide **TF**; view along Y-axis.

## 4. Windows PowerShell — webcam

```powershell
cd "C:\Users\Marco\SynologyDrive\Hof\STUDIUM\Semester II\AI Project\MediaPipe Hand Landmarker"
$WSL_IP = ((wsl -d SwarmGesture-Ubuntu -- hostname -I) -split '\s+')[0]
python .\gesture_sender.py --model models/gesture_svm_mirrored.joblib --send --host $WSL_IP
```

Click the webcam window and press **E** to send gestures.

**Gestures:** One = takeoff · Peace = static heart · Three = static sine · OK = static spiral · Fist = return to grid · Palm = grid then land.

## Offline check (Ubuntu)

```bash
python3 -m unittest test_static_shapes.py -v
```

Movement waits use the ROS simulation clock. Before landing or starting the next shape after a grid return, the bridge requires fresh world-frame TF for all 19 drones within 0.20 m of their airborne grid targets. If feedback is missing or a drone has not arrived, it stays in the grid-return stage and prints a waiting message.

Only simulation: path checks use planned positions and do not guarantee collision-free trajectories. Restart the bridge after code changes; an already running Python process keeps its old code.


## Experimental pulsing heart

Once grounded, stop the existing bridge and replace only terminal 2's command:

```bash
python3 heart_animation_bridge.py --run-sim --fast-test \
  --ros-args -p use_sim_time:=true
```

Arm with **a + Enter**, show **one** to take off, then **peace**. The original
heart forms first, then repeatedly grows to 120%, shrinks to 80%, and returns
to its original size. Three and OK still select static sine and spiral.

Palm, fist, shape switches, and keyboard landing finish the current pulse leg
(up to about 3 simulation seconds), restore the original heart at rest, then
return to the grid. Palm lands only after the existing fresh-TF grid check.
This prototype uses completed high-level `goTo` moves, with a short settling
pause between legs; it never streams low-level setpoints. The static command
`python3 gesture_bridge.py ...` continues to select the static controller.

Checks from `simulation/`:

```bash
python3 -m unittest test_static_shapes.py test_heart_animation.py -v
python3 check_heart_backend.py
```

The backend check creates isolated planner objects for 3, then 19 drones; it
sends no ROS commands and assumes ideal tracking. Live RViz pulse / stop /
landing still needs visual acceptance testing.


## Travelling sine wave

The quickstart now selects `formation_animation_bridge.py`: peace pulses the heart,
three sends a wave toward +X, and OK keeps the static spiral. Each sine drone
retains its X/Y assignment and moves up/down in Z. Palm and shape switches finish
the current leg, restore the original silhouette, then return to the TF-verified grid.

Manual bridge command: `python3 formation_animation_bridge.py --run-sim --fast-test --ros-args -p use_sim_time:=true`.

For the optional faster ideal-motion preview (without physics), see
`../LAUNCHER_README.md`. It requires restarting the ROS simulation as well as the bridge.


Formation switches in `formation_animation_bridge.py` now use checked direct or
Y-lane routes rather than HOME. Each route stage waits for fresh TF arrival.
Grid return remains for fist and palm/landing. See `../LAUNCHER_README.md` for
restart buttons and the limits of planned separation checks.


## Continuous preview playback (current default)

The launcher now selects `smooth_animation_bridge.py`. It requires the updated
`preview_server.py` and plays uploaded high-level trajectories continuously:
heart period 3.2s, sine period 6s, 50 Hz ideal-motion updates. It never switches
to low-level streaming. The middle-size heart waypoint and sampled-wave dwell
pauses are removed; preview transitions run faster while retaining arrival checks.
Restart both ROS and bridge when updating the preview server. See the current
`../LAUNCHER_README.md` for startup, restart, and validation commands.
