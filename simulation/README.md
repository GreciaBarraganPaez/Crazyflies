# SwarmGesture — 7-drone quickstart

**Simulation only.** Open three terminals. Run everything from your existing GitLab project.

## Once after replacing the scripts

In Windows PowerShell:

```powershell
wsl -d SwarmGesture-Ubuntu
```

In Ubuntu:

```bash
cd "/mnt/c/Users/Marco/SynologyDrive/Hof/STUDIUM/Semester II/AI Project/MediaPipe Hand Landmarker/simulation"
python3 configure_swarm.py
python3 formation_demo.py --dry-run
python3 -m unittest test_gesture_bridge.py -v
```

## Terminal 1 — ROS 2 + RViz (Ubuntu)

```powershell
wsl -d SwarmGesture-Ubuntu
```

```bash
cd "/mnt/c/Users/Marco/SynologyDrive/Hof/STUDIUM/Semester II/AI Project/MediaPipe Hand Landmarker/simulation"
ros2 launch crazyflie launch.py \
  backend:=sim rviz:=True teleop:=False mocap:=False \
  crazyflies_yaml_file:="$(realpath config/crazyflies.yaml)"
```

## Terminal 2 — Gesture bridge (Ubuntu)

```powershell
wsl -d SwarmGesture-Ubuntu
```

```bash
cd "/mnt/c/Users/Marco/SynologyDrive/Hof/STUDIUM/Semester II/AI Project/MediaPipe Hand Landmarker/simulation"
python3 gesture_bridge.py --run-sim --ros-args -p use_sim_time:=true
```

Type **`a` + Enter** to arm takeoff, **`x` + Enter** to land, or **`q` + Enter** to quit.

## Terminal 3 — Webcam (Windows PowerShell)

```powershell
cd "C:\Users\Marco\SynologyDrive\Hof\STUDIUM\Semester II\AI Project\MediaPipe Hand Landmarker"
$WSL_IP = ((wsl -d SwarmGesture-Ubuntu -- hostname -I) -split '\s+')[0]
python .\gesture_sender.py --model models/gesture_svm_mirrored.joblib --send --host $WSL_IP
```

Click the camera window and press **E** to enable gesture sending.

| Gesture | Action |
|---|---|
| One finger | Takeoff (arm first) |
| Peace | V formation |
| Three fingers | Line |
| OK | Vertical circle (7 points) |
| Open palm | Land |
| Fist | No new movement |

**Camera keys:** `E` = toggle sending; `X` = request landing; `Q` = quit.

## Optional — automatic formation demo (no webcam)

Stop the gesture bridge first; keep Terminal 1 (ROS + RViz) running. In Terminal 2:

```bash
python3 formation_demo.py --run-sim --ros-args -p use_sim_time:=true
```

**Important:** Stop the old ROS server and gesture bridge before starting the new seven-drone configuration. Use `backend:=sim` only. The planner has no active collision avoidance or verified hardware emergency stop.
