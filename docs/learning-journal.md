# SwarmGesture — Learning Journal

## Weeks 1–2 | 14–27 October 2026

### Progress
- Started the project and wrote the first plan, requirements and work packages (**MS1–MS2**).
- Installed and tested **MediaPipe**. Our `hand_tracker.py` shows 21 hand landmarks live through the webcam (**W01 — done**).
- Visited the drone lab with the professor and **3D printed propeller protectors** for the Crazyflies (**W11 — preparation**).
- Started a tool to record labeled hand-landmark data. We collected about **108 open-palm samples** in `palm.csv` (**W02/W04 — in progress**).

### What we learned / challenges
- MediaPipe finds the hand joints, but we still need our **own model** to recognize gestures.
- We need examples of each gesture from different people and angles. Samples from one recording are not enough to test accuracy reliably.

### Decisions
- Train a gesture classifier using **21 landmarks (63 coordinates)** instead of raw camera images. Start with our own recordings and consider a public dataset such as HaGRID later.
- Test in simulation before trying the real drones.

### Next steps
- Record the other five gestures and collect samples from more people (**W02/W04**).
- Build a simple rule-based baseline and train a first classifier (**W03/W04**).
- Check the printed protectors and begin setting up the drone simulation (**W06/W11**).

## Week 4 | 4–6 November 2026

### Team updates | 4 November 2026

- **Continuous formations and 3D helix (`f2ac933`):** introduced the shared
  formation registry/runtime, continuous heart/sine/spiral playback, joined
  transitions, pose-synchronized colors and the moving 3D helix.
- **Automatic Snake (`eb9f60c`):** added the nineteen-drone Snake scene with
  growth, apple collection, grid return, seeded winding routes and splitting
  into two snakes.
- **Hand-controlled Snake (`ea7b775`):** added the separate eight-drone game
  with hand-position steering, its own scene/runtime, RViz configuration and
  validation checks.
- **Layout and snapshots (`8ba03cb`):** documented the project map and
  preserved validated development snapshots under `archive/`, including Snake,
  formation and simulation-layout versions.

### Progress
- Stabilized the Windows environment in the existing `.venv` and verified the offline simulation tests.
- Installed the ROS 2 Jazzy/Crazyswarm2 prerequisites in Ubuntu 24.04, including the Crazyflie packages and Python firmware bindings.
- Added the analog `clock` formation. Nineteen drones form a clock face with hour and minute hands based on the local `Europe/Berlin` time at formation startup.
- Added a separate two-hand detector: one closed hand is identified as the wrist target while the index finger of the other hand points to it. Existing one-hand gestures remain unchanged.
- Updated the recorder to visualize two hands and preserve the `R` record/pause and `Q`/`Esc` exit controls.
- Added paired-hand recording with 126 normalized landmark features and positive/negative clock labels.
- Trained a separate clock SVM and generated `reports/clock/evaluation.txt` plus `reports/clock/confusion_matrix.png`.

### Evaluation
- Random split: 100.0% train accuracy, 99.13% test accuracy, 0.87 percentage-point gap.
- Session split: 99.74% train accuracy, 99.11% test accuracy, 0.63 percentage-point gap.
- The session confusion matrix contained 39 true negatives, 1 false positive, 75 true positives and 0 false negatives.
- These results are promising, but more participants and independent sessions are still needed before treating the model as robust.

### What we learned / challenges
- The original SVM stores one hand as 63 normalized features. The clock needs both hands, so it uses a separate 126-feature data path and model.
- A time-dependent clock geometry cannot use one fixed grid-entry clearance certificate for every minute. The clock remains simulation-only until time-varying routes are certified.
- WSL commands (`make`, `source`, `ros2`) must run inside Ubuntu; the Windows launcher coordinates the webcam and ROS processes.

### Decisions
- Keep the existing gesture classifier and mappings unchanged.
- Keep the clock model separate as `models/clock_pair_svm.joblib`.
- Keep archived clock documentation and evidence separate from the active root project; the active project remains the runnable source of truth.

### Next steps
- Evaluate the clock with more independent sessions and participants.
- Integrate the validated paired SVM into live recognition as an optional replacement for the rule-based detector.
- Add time-aware transition planning if the clock is ever considered for physical flight.
