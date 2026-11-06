# Where things live

The main folder is for starting the project and finding its documentation.
Implementation files and optional utilities are grouped by purpose.

## Main folder

| File/folder | What it does | Needed for everyday use? |
| --- | --- | --- |
| `Start-SwarmGesture.cmd` | Starts the normal nineteen-drone formation preview | Yes |
| `SwarmGesture-Tools.cmd` | Menu for games, physics, bridge restarts and WSL recovery | Optional |
| `README.md` | Starting instructions and folder overview | Reference |
| `requirements.txt` | Windows Python dependencies | Setup/maintenance |
| `pytest.ini` | Test discovery settings | Development |
| `.gitignore`, `.gitattributes` | Version-control exclusions and Bash line endings | Keep |
| `.venv/` | Existing local Python environment | Keep; do not move |
| `app/`, `simulation/` | Working Windows input app and ROS simulation | Yes |
| `tools/`, `docs/` | Optional utilities and documentation | Keep |
| `models/`, `data/`, `reports/`, `archive/` | Assets, data and project evidence | Keep |

The clock extension adds paired-hand recognition without replacing the original
one-hand pipeline:

| Location | Purpose |
| --- | --- |
| `app/clock_gesture.py` | Live rule-based detector for a closed wrist plus pointing index |
| `app/clock_features.py` | Normalizes two hands into 126 paired features |
| `simulation/formations/clock.py` | Analog clock geometry and local-time hands |
| `tools/gestures/train_clock_model.py` | Separate clock SVM training and evaluation |
| `models/clock_pair_svm.joblib` | Clock-only trained model |
| `reports/clock/` | Clock evaluation report and confusion matrix |
| `docs/clock.md` | Clock controls, data collection and limitations |

Python creates `__pycache__/` folders inside code folders. They are generated
cache files, ignored by Git, and contain no source code or training samples.

## Why there were seven CMD files

Only the main start shortcut is necessary. The others were small convenience
wrappers around one shared PowerShell launcher; they were not seven independent
implementations. They now live together in `tools/launch/`, and the tools menu
provides their actions without requiring you to find the correct file.

| Optional shortcut in `tools/launch/` | Purpose |
| --- | --- |
| `Start-SwarmGesture-Snake.cmd` | Automatic nineteen-drone Snake animation |
| `Start-SwarmGesture-Snake-Player.cmd` | Eight-drone hand-controlled game |
| `Start-SwarmGesture-Physics.cmd` | Slower physics profile |
| `Restart-SwarmGesture-Bridge.cmd` | Restart the stopped formation bridge after landing |
| `Restart-SwarmGesture-Snake-Bridge.cmd` | Restart the stopped automatic Snake bridge |
| `Start-SwarmGesture-Clean.cmd` | Confirmed WSL shutdown and recovery; not routine startup |

`tools/launch/Start-SwarmGesture.ps1` is the shared implementation. It finds the
project root, checks required files/WSLg, opens the four terminals and selects
the requested mode. The tools menu can restart the hand-game bridge too.

Land and stop the existing programs before switching modes. WSL recovery retains
its confirmation because it stops every WSL application, including Docker.

## What the eight Python files do

| New location | Purpose | Used by |
| --- | --- | --- |
| `app/gesture_sender.py` | Webcam, MediaPipe, classifier, display and UDP sender | Every launch |
| `app/gesture_features.py` | Converts 21 landmarks into the same normalized 63 features used in training | Sender, recorder, trainer, prediction preview |
| `app/gesture_gate.py` | Requires a stable gesture and suppresses repeated triggers | Sender |
| `app/hand_steering.py` | Hand-position zones and debounce | Hand-game sender mode |
| `tools/gestures/record_gestures.py` | Records labeled landmark CSV samples | Dataset collection |
| `tools/gestures/train_model.py` | Trains/evaluates the SVM and writes reports/models | Model development |
| `tools/gestures/predict_live.py` | Shows classifier predictions without sending drone commands | Recognition diagnostics |
| `tools/gestures/hand_tracker.py` | Original landmark-only webcam demo | Tracking diagnostics |

`record_gestures.py` detects two hands for all recordings. Normal gesture labels
continue to write the original 63-feature format; `clock_positive` and
`clock_negative` write paired 126-feature rows to `clock_pairs.csv`.

The last four tools are not needed to run formations. They remain useful for
the AI project's training and evaluation work, so they were moved, not deleted.
Feature extraction, filtering, steering logic and the trained models retain
their behavior.

For manual sender startup, run `python -m app.gesture_sender --help` from the
project root. Developer tools can be run directly, for example
`python tools/gestures/train_model.py --help`. Their default asset/data paths
resolve from the project location rather than the terminal's working directory.

The MediaPipe file moved from the main folder to
`models/hand_landmarker.task`. It is required by tracking/recognition. The
launcher and all four webcam/developer tools use its new location.

The simulation code is now grouped by responsibility too. See the
[simulation folder guide](../simulation/README.md) and its separate tests/checks
guides. Historical archives remain preserved.

## Team additions on 4 November 2026

The team's work this week added the shared continuous formation runtime and moving
3D helix, the automatic nineteen-drone Snake scene, the separate eight-drone
hand-controlled Snake scene, and validated snapshots under `archive/`. These
are active capabilities in the root project; the archived folders are copies.
