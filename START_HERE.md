# SwarmGesture — Stage 1: collect normalized hand landmarks

Copy `gesture_features.py` and `record_gestures.py` into the ROOT of your **new local Git clone**, beside `hand_tracker.py`. Do not copy them to your old Synology Drive folder.

This is a first-stage recording tool, **not a trained classifier yet**. It builds on your working MediaPipe hand tracking and does not change `hand_tracker.py`.

## 1. Prerequisites

Open PowerShell inside your local `aiproject-ws26-swarmgesture` clone:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install mediapipe opencv-python numpy
```

If you already have an activated venv with the dependencies installed, skip setup.

The project root must contain `hand_landmarker.task`. If it doesn't, download it using the command in your repository README:

```powershell
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -OutFile "hand_landmarker.task"
```

The `.task` model is correctly ignored by Git.

## 2. Collect the first labeled samples

Start with an open palm:

```powershell
python record_gestures.py --label palm --person p01 --session s01
```

- Press **R** to start recording. Press **R** again to pause.
- Show the requested gesture and vary hand angle, distance, lighting and position slightly.
- Record about **30–50 samples per class for an initial smoke test** (this is not enough for the final evaluation).
- Press **Q** or **Esc** to close.
- Keep only **one hand** in the camera view.

Then run for the other classes:

```powershell
python record_gestures.py --label fist --person p01 --session s01
python record_gestures.py --label one --person p01 --session s01
python record_gestures.py --label peace --person p01 --session s01
python record_gestures.py --label three --person p01 --session s01
python record_gestures.py --label ok --person p01 --session s01
python record_gestures.py --label unknown --person p01 --session s01
```

Use `unknown` for **visible hands making other, non-command poses**, not empty frames. If no hand is detected, that must be handled as a separate safe state at inference time.

The program writes CSV files to `data/landmarks/p01/<label>.csv` with metadata (person/session/handedness/time), a gesture label, and 63 features per example. It saves **no photographs or video**.

## 3. Good data collection practice

- Use anonymous participant IDs `p01`, `p02`, ...; ask permission when recording other people.
- Keep each participant's data together for evaluation. Never randomly split adjacent frames between training and test; that gives an unrealistically easy score.
- Add more participants and fresh sessions after the first smoke test.
- Record a clear gesture definition: e.g. which fingers are raised for `three`.
- The coordinate transform centers at landmark 0 (wrist), then divides by wrist-to-landmark-9 scale. Use the **same transform** for public image data, training and live inference.
- Do not change the preprocessing partway through collecting data unless you reprocess everything.

## 4. Next implementation tasks

1. Build an importer for a *small verified subset* of HaGRID images using MediaPipe's `IMAGE` mode. Save compatible CSV files, keep original split/participant IDs where available, and record extraction failures.
2. Train a rule-based baseline and scikit-learn SVM (with scaling) on normalized features.
3. Evaluate held-out subjects, gesture-wise recall, confusion matrix and inference latency.
4. Add live gesture display and an `unknown` rejection threshold.
5. Add stabilization, an independent emergency stop, and only then simulator commands.

Until validated, this recorder and the future classifier are **not appropriate to control real drones**.
