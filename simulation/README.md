# SwarmGesture — Three-drone simulation

This example runs **only in Crazyswarm2's simulated backend**, not on real Crazyflies. It uses ROS 2 Jazzy in `SwarmGesture-Ubuntu` (WSL2).

## Setup (once)

1. Copy this `simulation/` folder into your SwarmGesture project. Open WSL Ubuntu 24.04 with `wsl -d SwarmGesture-Ubuntu`.
2. Switch to the `simulation/` folder in WSL. If you're using the Windows project clone, its path is under `/mnt/c/Users/Marco/...`; use `pwd` to check.
3. Create a three-drone configuration **without modifying any installed ROS files**:

```bash
python3 configure_swarm.py
python3 formation_demo.py --dry-run
```

The generated `config/crazyflies.yaml` preserves the system's existing `robot_types`, `all`, and other settings, but enables three drones: `cf231`, `cf232`, `cf233`, initially 0.8 m apart.

## Run (every time)

**Terminal 1 — launch simulator and RViz**

```bash
# From the simulation/ folder
ros2 launch crazyflie launch.py \
  backend:=sim rviz:=True teleop:=False mocap:=False \
  crazyflies_yaml_file:="$(realpath config/crazyflies.yaml)"
```

In RViz, set **Global Options → Fixed Frame** to `world` and enable RobotModel/TF, if necessary.

**Terminal 2 — run the demo**

```bash
# New Ubuntu terminal, from the same simulation/ folder
ros2 service list | grep /go_to
python3 formation_demo.py --run-sim --ros-args -p use_sim_time:=true
```

Watch the three Crazyflies take off to 1 m, move through **line → V → circle → line**, and land. For three drones, the "circle" is necessarily a triangular arrangement of three points on a circle.

## Safety and limitations

- **Simulation only.** These example URIs are not verified hardware addresses.
- Movement uses high-level `goTo` commands with 6-second durations; there is **no active collision avoidance, feedback validation, or dynamic formation assignment** yet.
- Geometry tests verify **planned** separation ≥0.3 m for idealized straight-line moves, not actual simulator trajectories; visually inspect and test the resulting motion before claiming the milestone is met.
- Stop the terminal demo with `Ctrl+C`. For an abnormal event in simulation, stop the launch with `Ctrl+C`; an independent emergency stop is still to be designed before real flights.
- **Do not launch this demo with `backend:=cpp` or `backend:=cflib`.**

## How it fits into the project

- W06 — multiple simulated drones: first demonstration.
- W07 — first fixed formations, without Hungarian assignment or collision-aware planning.
- Next: make a gesture command controller and bridge the Windows classifier to ROS 2.

References: https://imrclab.github.io/crazyswarm2/usage.html and https://github.com/IMRCLab/crazyswarm2
