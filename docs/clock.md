# Analog clock formation

The clock is a simulation-only formation selected by the two-hand wrist-pointing gesture:

- one hand is closed;
- the index finger of the other hand points at that wrist;
- the gesture must remain stable long enough for the gesture gate.

## Implementation

| Component | Role |
| --- | --- |
| `app/clock_gesture.py` | Rule-based two-hand detector used by the live sender |
| `app/clock_features.py` | 126-column paired-hand normalization for model work |
| `simulation/formations/clock.py` | Clock-face geometry and local-time hand positions |
| `simulation/core/formation_registry.py` | Registers `clock` as a formation and gesture |
| `tools/gestures/record_gestures.py` | Records `clock_positive` and `clock_negative` paired samples |
| `tools/gestures/train_clock_model.py` | Trains and evaluates the separate clock SVM |
| `models/clock_pair_svm.joblib` | Trained paired-hand model |
| `reports/clock/` | Evaluation text and confusion matrix |

## Data collection

Run from the project root:

```powershell
.\.venv\Scripts\python.exe tools\gestures\record_gestures.py --label clock_positive --person p01 --session wrist-clock-03
.\.venv\Scripts\python.exe tools\gestures\record_gestures.py --label clock_negative --person p01 --session wrist-clock-03
```

Use `R` to start/pause recording and `Q` or `Esc` to exit. Positive and negative examples should be recorded in each session. The paired data is stored in `data/landmarks/<person>/clock_pairs.csv`.

## Training and evaluation

Random evaluation:

```powershell
.\.venv\Scripts\python.exe tools\gestures\train_clock_model.py --mode random
```

Session-held-out evaluation:

```powershell
.\.venv\Scripts\python.exe tools\gestures\train_clock_model.py --mode session
```

The current session evaluation is recorded in `reports/clock/evaluation.txt`. It reports train/test accuracy, the generalization gap, precision, recall, F1-score and a confusion matrix.

## Current limitations

The clock uses the local `Europe/Berlin` timezone by default and calculates the hands when the formation starts. The hand geometry is checked for resting separation, but its entry path is time-dependent and is not certified for physical flight. Keep the clock in simulation until time-varying entry and transition routes receive a full safety check.
