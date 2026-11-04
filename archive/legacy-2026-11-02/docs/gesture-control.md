# SwarmGesture — Webcam to simulated swarm

This demo connects our **Windows gesture classifier** to the **three simulated Crazyflies in Ubuntu WSL2**. It does not control real drones.

## Files

Copy the files from the ZIP into the **existing GitLab project** (keep your working `simulation/formations.py` and `simulation/config/crazyflies.yaml`):

```text
SwarmGesture/
├── gesture_sender.py                   # Windows webcam predictions -> UDP
├── gesture_gate.py                     # Stable prediction filter
├── simulation/
│   ├── gesture_bridge.py               # Ubuntu UDP -> Crazyswarm2
│   ├── send_test_gesture.py             # Network test without webcam
│   ├── test_gesture_bridge.py           # Unit tests
│   ├── formations.py                   # KEEP your working vertical formations
│   └── config/crazyflies.yaml          # KEEP your existing generated config
└── docs/gesture-control.md
```

## Gesture mapping

| Gesture | Simulation action |
|---|---|
| One index finger (`one`) | Take off, **only after manual arming** |
| Peace (`peace`) | Vertical V |
| Three fingers (`three`) | Vertical line |
| OK (`ok`) | Three points on a vertical circle |
| Open palm (`palm`) | Controlled landing and disarm |
| Fist (`fist`) | No new move; does **not** cancel a movement in progress |

Unknown/uncertain/no-hand predictions send nothing. A label must remain stable for 0.7 seconds and confidence must exceed the selected threshold. A gesture triggers once until you change or remove your hand, with an additional cooldown.

## Step A — Test Windows -> WSL networking (no ROS required)

1. In **PowerShell**, start Ubuntu:

   ```powershell
   wsl -d SwarmGesture-Ubuntu
   ```

2. In **Ubuntu**, change to the `simulation` directory **inside your existing SwarmGesture repository**. You can use the path you used for the working three-drone demo. Start the receiver:

   ```bash
   python3 gesture_bridge.py --dry-run
   ```

3. In **another PowerShell window**, get Ubuntu's IPv4 address:

   ```powershell
   wsl -d SwarmGesture-Ubuntu -- hostname -I
   ```

   Use the **WSL IPv4 address** (usually begins with `172.`), not your GitLab URL. In another PowerShell terminal inside your Windows project, send a packet (replace `WSL_IP`):

   ```powershell
   python simulation/send_test_gesture.py --host WSL_IP --gesture peace
   ```

   Ubuntu should print `DRY RUN ... peace -> v`. UDP does not confirm delivery: seeing `Sent` on Windows alone is **not** enough.

   If nothing arrives, confirm both scripts are running, the IP belongs to `SwarmGesture-Ubuntu`, and the port is 5055. WSL network mode and Windows Firewall may affect UDP between Windows and Ubuntu. See [Microsoft WSL networking](https://learn.microsoft.com/windows/wsl/networking).

4. Stop dry-run receiver with `Ctrl+C`.

## Step B — Run the simulated swarm

Open **three terminals**:

**Ubuntu terminal 1 — server and RViz** (from the existing repository's `simulation/` folder):

```bash
ros2 launch crazyflie launch.py \
  backend:=sim rviz:=True teleop:=False mocap:=False \
  crazyflies_yaml_file:="$(realpath config/crazyflies.yaml)"
```

**Ubuntu terminal 2 — gesture bridge** (same `simulation/` folder):

```bash
python3 gesture_bridge.py --run-sim --ros-args -p use_sim_time:=true
```

In this second terminal, type `a` and press **Enter** to arm ONE simulated takeoff. Type `x` + **Enter** at any time to request a controlled landing and disarm. Type `q` + **Enter** to exit (it will request landing first).

**Windows terminal 3 — test commands manually** (from project root; substitute `WSL_IP`):

```powershell
python simulation/send_test_gesture.py --host WSL_IP --gesture one
```

Wait about **5 seconds** for takeoff. Then send, **one by one**, waiting about **8 seconds** between formation commands:

```powershell
python simulation/send_test_gesture.py --host WSL_IP --gesture peace
python simulation/send_test_gesture.py --host WSL_IP --gesture three
python simulation/send_test_gesture.py --host WSL_IP --gesture ok
python simulation/send_test_gesture.py --host WSL_IP --gesture palm
```

The drones should take off, form a V, a line, a vertical circle (triangle with three drones), and land. If the bridge says `ignored while moving`, wait for the last movement to finish and resend the gesture.

## Step C — Use the webcam

Use your **existing mirrored model** and MediaPipe model. From Windows PowerShell in your project root:

```powershell
python gesture_sender.py --model models/gesture_svm_mirrored.joblib --send --host WSL_IP
```

In the webcam window:

- **E**: enable / disable gesture transmission (starts disabled even with `--send`).
- **X**: request **controlled landing** and disable transmission.
- **Q**: quit (also sends a best-effort landing request).

In the Ubuntu bridge terminal, press `a` + Enter **before showing the takeoff gesture**. Show `one` for ~1 second, wait for takeoff, then show `peace`, `three`, or `ok`, one at a time. If you prefer to preview predictions without any UDP communication, omit `--send` and `--host`.

## Known limitations and safety

- **Simulation only:** Do **not** run this bridge with `backend:=cpp`, `backend:=cflib`, or physical Crazyflies. Hardware flight needs independent hardware safety controls and validation.
- The keyboard and palm action request a **controlled landing**, **not** a guaranteed emergency motor cut. The fist does not stop a trajectory already underway. UDP delivery is not guaranteed.
- The server currently accepts UDP from any reachable sender on port `5055`. Use on a trusted local development setup only. Optionally specify `--allowed-ip WINDOWS_IP` to restrict incoming senders.
- Only fixed formation positions are commanded; **no active collision avoidance** or physical position verification is implemented.
- A `confidence` displayed by the model is an estimate, not proof of command safety. Keep collecting participant-held-out data for evaluation.
- The first goal is to demonstrate an end-to-end prototype, not to claim it is safe for real flight.

## Tests

From your project root (Windows or Ubuntu, with normal Python):

```bash
python -m unittest discover -s simulation -p "test_gesture_bridge.py" -v
```

The unit tests do not need ROS. They check packet parsing, stable prediction filtering, and manual arming/landing logic.
