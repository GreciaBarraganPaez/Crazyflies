# aiproject-ws26-swarmgesture

Gesture-controlled Crazyflie swarm. A webcam tracks the hand, our own gesture
classifier recognizes signs, and gestures or hand shapes become swarm
formations, flown in simulation (ROS 2 + Gazebo) and on real Crazyflies.

AI Project, Master AIR2, Hof University, Winter Semester 2026/27.

## Team

| Name | Focus |
|---|---|
| TODO | Gesture detection (Stage 1) |
| TODO | ROS 2 / Gazebo (Stage 2) |
| TODO | Hardware / evaluation (Stage 3) |

## Stages

1. **Hand and sign detection:** MediaPipe Hand Landmarker plus our own classifier.
2. **ROS 2 and Gazebo:** formation planning and simulated swarm.
3. **Real hardware:** the same pipeline on Crazyflies.

## Setup (Stage 1, Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install mediapipe opencv-python numpy

Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -OutFile "hand_landmarker.task"

python hand_tracker.py
```

Press Esc to quit. The model file is not committed (see `.gitignore`).

## Repository structure

```
.
├── README.md
├── .gitignore
├── hand_tracker.py        # live hand tracking demo
├── docs/
│   ├── project.md         # project plan -> final report
│   └── learning-journal.md
├── data/                  # labeled gesture CSV files
└── notebooks/             # Jupyter: training and evaluation
```

## Documentation

- Project plan, requirements and decisions: `docs/project.md`
- Biweekly progress and AI tool use: `docs/learning-journal.md`


TEST Grecia 