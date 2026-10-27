# SwarmGesture — Gesture-Controlled Crazyflie Swarm

**Course project | Winter semester 2026/27**  
**Team:** TODO · **Repository:** `aiproject-ws26-swarmgesture`  
**Updated:** 27 October 2026 · **Next milestone:** MS2, 28/29 October

## 1. Project idea

We want to control a small swarm of Crazyflie drones with **hand gestures** instead of a controller. A webcam detects a hand, our model recognizes the gesture, and the drones move into a matching formation.

Our target users are students, researchers and demonstrators in a lab. We will test the system **in simulation first**, then on real drones if the lab setup allows it.

**Planned pipeline:** Webcam → MediaPipe hand landmarks → our gesture classifier → formation planner → simulated / real drones.

### Our AI contribution

MediaPipe already detects **21 hand landmarks**; we are not training a new hand detector. Our own work is to collect gesture data, train and compare classifiers, and translate gestures into drone formations.

## 2. Scope and requirements

### Minimum viable product (MVP)

- Recognize six hand gestures and show the predicted gesture.
- Convert a stable, confident prediction into a formation command for **2–3 simulated drones**.
- Provide an independent keyboard emergency stop in addition to a stop gesture.
- Make the simulation reproducible with one documented start command.

### Planned gesture commands

| Gesture | Command |
|---|---|
| Open palm | Stop |
| Fist | Hover |
| Index finger up | Take off |
| Peace sign | V formation |
| Three fingers | Line formation |
| OK sign | Circle formation |

*These mappings are proposals and can change after testing.*

### User stories and acceptance checks

| ID | User story | How we will check it |
|---|---|---|
| US-01 | As an operator, I want to change formations with gestures. | A stable recognized gesture triggers the correct simulated formation; uncertain input does nothing. |
| US-02 | As an operator, I want to stop the drones safely. | Stop gesture and independent keyboard stop override formation commands. |
| US-03 | As an operator, I want to create a formation based on my hand shape. | Later: drones reach target points based on a detected hand shape. |
| US-04 | As a teammate, I want to start the simulation easily. | Documented setup and one start command work on a fresh machine. |
| US-05 | As an operator, I want to test with real Crazyflies. | Later: test 2–3 drones with suitable tracking and safety measures. |
| US-06 | As a developer, I want to record and retrain gestures. | Save labeled landmarks to CSV; training produces a model and evaluation results. |

**Not in scope:** training our own hand detector, outdoor flight, large swarms or dynamic gesture recognition. Hand-shape formations and real flights are later goals, not required for the first prototype.

### Success criteria (targets, not yet measured)

1. **Accuracy:** at least **90%** across six gestures, tested on **at least three people not used in training**.
2. **Speed:** 90% of camera-to-command times below **300 ms**.
3. **Simulation:** three drones reach their formation without getting closer than **0.3 m** in at least **18 of 20** tests.

## 3. Plan and progress

### Milestones

| Date | Goal |
|---|---|
| 14/15 Oct — MS1 | Choose and announce topic |
| 28/29 Oct — MS2 | Plan, requirements and repository |
| 18/19 Nov — MS3 | Gesture-to-formation prototype in simulation |
| 16/17 Dec — MS4 | Release candidate and possible hardware tests |
| 9 Jan — MS5 | Final report, release and presentation |

### Work packages

| ID | Task | Status |
|---|---|---|
| W01 | Live MediaPipe hand tracking | **Done** |
| W02 | Record labeled landmarks to CSV | **Doing** |
| W03 | Simple rule-based gesture classifier | Planned |
| W04 | More gesture data, trained model and evaluation | **Doing** (data collection started) |
| W05 | Stop gesture and keyboard emergency stop | Planned |
| W06 | ROS 2 / Gazebo / CrazySim simulation setup | Planned |
| W07 | Assign drones to formation positions safely | Planned |
| W08 | Connect gesture recognition to simulation | Planned |
| W09 | Document a one-command simulation start | Planned |
| W10 | Create formations from the hand shape | Later |
| W11 | Real drone control and tests | Later; lab visit and protector printing started |

**Current progress (27 October):** `hand_tracker.py` detects hand landmarks live. A local prototype recorder has been used to collect about **108 `palm` samples**. We visited the lab and 3D printed propeller protectors, which still need to be checked. **No trained gesture classifier or working drone simulation yet.** See the [learning journal](learning-journal.md).

## 4. Technical approach and decisions

**Hand tracking and recognition.** We use MediaPipe to find 21 landmarks per hand. Each sample has 63 normalized coordinates (x, y, z). We plan to compare a simple rule-based classifier with a trained model, starting with an **SVM**.

**Dataset.** We started recording our own labeled samples. We may also use a public dataset such as **HaGRID**, extracting landmarks from its images. We will keep training and testing people separate to avoid overly optimistic results.

**Simulation setup (proposed).** Run webcam processing on Windows and the ROS 2 / Gazebo side on Ubuntu/WSL2; send recognized gestures between them, possibly over UDP. We will confirm this after testing the setup.

**Alternatives considered.** Using MediaPipe's ready-made gesture recognizer would be easier but would give us less of our own AI work. Training directly on images is also possible, but landmark features are simpler for our first model.

**Safety.** An emergency stop must not depend only on gesture recognition. Hardware flights need a suitable lab setup, checked propeller protectors and an independent way to stop the drones.

## 5. Evaluation and risks

We will report gesture accuracy, a confusion matrix, recognition delay and formation success. For real-world evaluation we need more participants, varied lighting and different camera angles. The first 108 samples are **test data for the recording process**, not an accuracy result.

Main risks are inconsistent gesture detection, simulation setup problems and limited access to flight hardware. We will test the recognition pipeline separately and keep simulation as the main demonstration if real flights are not possible.

## 6. Final report and contributions (to complete later)

- **Results:** model comparison, latency, simulation tests and (if possible) real flights.
- **Reflection:** what worked, problems we faced and what we would improve.
- **Team contributions:** TODO — add names and links to work packages, commits or merge requests.
- **AI tools:** Claude supported idea discussion and documentation structure; ChatGPT supported discussion and initial code drafts for the gesture recorder. The team must review and test any AI-generated material.
