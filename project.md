# Gesture-Controlled Crazyflie Swarm

Team: TODO (names) | Repository: `aiproject-ws26-swarmgesture` | Status: draft for MS2 (28/29 Oct 2026)

> Everything marked **TODO** or "planned" must be confirmed by the team. Numeric targets are planned values and will be refined after the first baseline measurements.

## 1. Problem and target users

**Problem:** Controlling several drones usually means scripted trajectories or one joystick per drone. This is slow, needs training, and ties up the operator's hands.

**Target user:** An operator of a small drone swarm in a lab or demo setting (for example a researcher, teacher or student) who wants to direct the swarm quickly and intuitively. The same interaction idea is relevant for rescue or inspection work, where hands are busy and a controller is impractical (motivation only, not a project goal).

**Idea:** A webcam tracks the operator's hand. Our own trained model recognizes gestures, and the gestures (later also the hand shape) are turned into swarm formations that a Crazyflie swarm flies, first in simulation and then on real hardware.

## 2. AI / robotics contribution

- **Hand tracking:** pretrained MediaPipe Hand Landmarker (21 landmarks per frame). Not our own contribution; used as an input stage.
- **Gesture recognition (own contribution):** own gesture dataset recorded with several people, rule-based baseline from finger geometry, and a trained classifier on normalized landmarks (k-NN / SVM / small MLP). Compared by accuracy, confusion matrix and latency.
- **Shape-to-formation planning (own contribution):** gesture or hand shape becomes N target points, drones are assigned to targets (Hungarian algorithm), and trajectories are planned collision-free.
- **Robotics:** Crazyflie swarm controlled through ROS 2 and Crazyswarm2, simulated in Gazebo (CrazySim), then flown on real hardware.

## 3. Scope

**MVP:** US-01, US-02, US-04. A recognized gesture triggers a predefined formation on 2-3 simulated drones, with a reliable stop, and the simulation starts with one documented command.

**Later (planned within the semester):** US-03 (hand shape to formation), US-05 (real Crazyflies), US-06 (recording tool is needed early, so it is part of Stage 1 work).

**Stretch:** dynamic gestures (swipe, circle) with a sequence model, animal-like formations (for example a bird with flapping wings), pose tracking for coarse body control.

**Non-goals this semester:** training our own hand tracker, outdoor flight, onboard (AI Deck) vision, any follow-me mode, large swarms on real hardware (more than the drones available in the lab).

## 4. Three measurable success criteria

1. **Gesture accuracy:** at least 90 % accuracy on a 6-gesture set, measured on a held-out test set from at least 3 people who are not in the training data.
2. **Latency:** p90 time from camera frame to published formation command below 300 ms, measured on the team laptops.
3. **Simulation reliability:** the simulated swarm of 3 drones reaches the commanded formation with a minimum inter-drone distance of at least 0.3 m (no collision) in at least 18 of 20 runs; the simulation starts with one documented command on a fresh machine.

Record the test data, the people (anonymous), hardware and software versions for every measurement. Real-hardware flights are a target, but not one of the three criteria because they depend on lab availability.

## 5. Risks and rough work plan

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Few or no Crazyflies or no positioning system available | Stage 3 cannot be done | Ask the lecturer early; simulation must work on its own |
| ROS 2 / Gazebo / CrazySim version mismatch | Weeks lost | Test the setup in week 1-2; pin versions; Docker image |
| Gesture accuracy drops with other people, lighting, distance | Criterion 1 missed | Record data from several people early; split by person; analyze errors |
| Camera not available inside WSL2 | Pipeline breaks | Run hand tracking natively on Windows, send results to WSL2 over UDP (ADR-01) |
| Safety (real flights) | Injury or damage | Stop gesture, keyboard kill switch, netted area, spare props |
| Latency too high | Poor control feel | Measure early; lower camera resolution; one hand only |

### Milestones

| Milestone | Date | Target |
|---|---|---|
| MS1 | 14/15 Oct | Topic notification |
| MS2 | 28/29 Oct | Plan, requirements, user stories, repository |
| MS3 | 18/19 Nov | Prototype: gesture to formation in simulation |
| MS4 | 16/17 Dec | Release candidate, first real-hardware flights |
| MS5 | 09 Jan | Final release, report, presentation upload |

### Work packages

| ID | Task | Story | Owner | Status |
|---|---|---|---|---|
| W01 | Hand tracking demo with MediaPipe (`hand_tracker.py`) | US-01 | TODO | Done |
| W02 | Recording tool: normalized landmarks + label to CSV | US-06 | TODO | Ready |
| W03 | Rule-based gesture baseline | US-01 | TODO | Backlog |
| W04 | Gesture dataset (>= 3 people) and trained classifier + evaluation notebook | US-01 | TODO | Backlog |
| W05 | Stop gesture and keyboard kill switch | US-02 | TODO | Backlog |
| W06 | ROS 2 + Gazebo + CrazySim: one simulated Crazyflie responds to a command | US-04 | TODO | Ready |
| W07 | Formation planner: target points, Hungarian assignment, collision avoidance | US-01 | TODO | Backlog |
| W08 | ROS 2 nodes and Windows-to-WSL2 bridge (UDP) | US-01 | TODO | Backlog |
| W09 | Docker image and one-command simulation start | US-04 | TODO | Backlog |
| W10 | Hand shape to formation (silhouette to N points) | US-03 | TODO | Backlog |
| W11 | Real Crazyflie backend and flight tests | US-05 | TODO | Backlog |

#### W01: Hand tracking demo
Done when: the script shows 21 landmarks per hand live from the webcam.
Evidence: `hand_tracker.py`, first commit.

Status values: Backlog, Ready, Doing, Review, Done. Record dependencies and blockers beside the package.

## 6. Requirements and design

### Functional requirements

- FR1 (Must): capture webcam video and detect hand landmarks in real time.
- FR2 (Must): classify a hand gesture from a defined set of 6 gestures with a confidence value.
- FR3 (Must): translate a gesture into a formation command only if confidence is at least the configured threshold and the gesture is held for at least the configured time.
- FR4 (Must): compute target positions for N drones and assign each drone to one target without collisions.
- FR5 (Must): fly the commanded formation in the simulation.
- FR6 (Must): a stop gesture and a keyboard kill switch override every other command.
- FR7 (Should): convert a hand silhouette into N target points for a formation.
- FR8 (Should): run the same pipeline on 2-3 real Crazyflies.
- FR9 (Should): record labeled gesture samples and retrain the classifier with a documented command.
- FR10 (Could): recognize dynamic gestures (swipe, circle).

Draft gesture set (to be tested and revised): open palm = stop, fist = hover, index finger up = take off, peace sign = V formation, three fingers = line, thumb and index circle = circle formation.

### Non-functional requirements

- NFR1 (Must): gesture accuracy at least 90 % on the held-out test set (criterion 1).
- NFR2 (Must): p90 latency from camera frame to published command below 300 ms (criterion 2).
- NFR3 (Must): minimum distance of 0.3 m between drones in at least 18 of 20 simulation runs (criterion 3).
- NFR4 (Must): the simulation starts with one documented command on a fresh Ubuntu or WSL2 machine.
- NFR5 (Must): no API keys or tokens in Git.
- NFR6 (Should): stop command reaches the drones within 200 ms of the stop gesture.

### User stories

#### US-01: Direct the swarm with a gesture
Priority: Must | Delivery: MVP | Requirements: FR1, FR2, FR3, FR4, FR5
As an operator, I want to show a gesture so that the swarm flies the matching formation without a controller.

Acceptance criteria:
- Given a visible hand showing "peace sign" with confidence at or above the threshold, when I hold it for the required time, then the V formation command is published and the simulated drones fly it.
- Given no hand or a gesture below the confidence threshold, when frames are processed, then no command is published.

#### US-02: Stop the swarm at any time
Priority: Must | Delivery: MVP | Requirements: FR6, NFR6
As an operator, I want a reliable stop so that I can end the flight immediately.

Acceptance criteria:
- Given a flying swarm, when I show the open palm, then all drones hover or land and further formation commands are ignored.
- Given hand tracking fails or the camera is disconnected, when I press the kill-switch key, then all drones stop.

#### US-03: Form a shape from my hand
Priority: Should | Delivery: Later | Requirements: FR7, FR4
As an operator, I want the swarm to copy the shape of my hand so that I can create formations without predefined gestures.

Acceptance criteria:
- Given a hand silhouette and N drones, when the shape is confirmed, then the swarm flies to N target points sampled from the silhouette without collisions.
- Given a silhouette that cannot be segmented, then the system reports an error and keeps the current formation.

#### US-04: Start the simulation with one command
Priority: Must | Delivery: MVP | Requirements: NFR4
As a reviewer or teammate, I want to start the simulation with one documented command so that I can reproduce the results on my own machine.

Acceptance criteria:
- Given a fresh machine with the documented prerequisites, when I run the documented start command, then the simulated swarm and the gesture pipeline start.
- Given a missing dependency, then the start script reports which one is missing.

#### US-05: Fly real drones
Priority: Should | Delivery: Later | Requirements: FR8, FR6
As an operator, I want to run the same pipeline on real Crazyflies so that I can show the system on hardware.

Acceptance criteria:
- Given 2-3 Crazyflies and a working positioning system, when I show a formation gesture, then the real drones fly the formation with the stop gesture still working.
- Given a lost radio link, then the drones land.

#### US-06: Record and retrain gestures
Priority: Should | Delivery: MVP | Requirements: FR9
As a developer, I want to record labeled samples and retrain so that I can extend the gesture set.

Acceptance criteria:
- Given the recording tool and a selected label, when I press the record key, then a normalized 63-value vector with the label is appended to the CSV.
- Given a CSV, when I run the documented training command, then a model file and an evaluation report are produced.

### Architecture decisions

#### ADR-01: Where does hand tracking run?
Status: Proposed | Date: 10 Oct 2026
Context: the webcam is hard to access from WSL2, while ROS 2 and Gazebo run best on Ubuntu.
Alternatives: everything in WSL2 with USB camera forwarding; everything on native Ubuntu; hand tracking on Windows and ROS 2 in WSL2.
Decision: run hand tracking and gesture classification natively on Windows and send the gesture result over UDP to a bridge node in WSL2.
Consequences: simple camera access and a gesture stage independent of ROS (easy to test), but an extra bridge and two setups to document.
Revisit if the team moves to native Ubuntu.

#### ADR-02: How are gestures recognized?
Status: Proposed | Date: 10 Oct 2026
Context: the course expects our own contribution, and MediaPipe already tracks hands and offers a built-in gesture recognizer.
Alternatives: MediaPipe Gesture Recognizer only; rule-based geometry only; own classifier on normalized landmarks.
Decision: use a rule-based baseline and an own classifier trained on our dataset, and compare them.
Consequences: more work (data collection, evaluation), but a measurable own contribution and a justified choice.

## 7. Implementation and runnable release

TODO (fill during the semester): architecture diagram, ROS 2 nodes, how to build, how to run, release tag.

## 8. Evaluation

TODO: gesture accuracy and confusion matrix, latency measurements, formation error and collision runs, comparison of baseline and trained classifier, simulation versus real hardware.

## 9. Limitations and reflection

TODO: what missed the targets and why, what worked well, what we would do differently.

## Appendix A: Use of AI tools

- Claude (chat) was used to discuss project ideas, compare tool options and draft this document structure. The team reviewed and adjusted the content.
- OpenCode with the university models: TODO (record what it proposed, what we changed, what we verified).

Keep this section honest and current: what the AI proposed and what we came up with ourselves.

## Appendix B: Individual contributions

| Member | Contribution | Links (work packages, commits, MRs) |
|---|---|---|
| TODO | TODO | TODO |
