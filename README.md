# SwarmGesture

Nineteen simulated drones controlled by a Windows MediaPipe/SVM webcam app and
ROS 2 Jazzy/Crazyswarm2 in WSL. Start **Start-SwarmGesture.cmd**.

Wait for Listening on UDP, enter a + Enter, enable sending with E in the webcam,
then show one finger to take off. Peace selects a pulsing heart, three fingers a
travelling sine wave, OK a rotating planar spiral. Fist returns to the airborne
grid; palm requests grid-first landing. After takeoff, enter moon or helix in the
bridge terminal for the moon outline or moving 3D corkscrew. demo cycles all five.
Grounded speed 0.5..1.25 changes loop speed and disarms takeoff.

Python input modules live in app/, developer utilities in tools/gestures/,
and simulation code is grouped into controllers/, servers/, core/, formations/,
runtime/, visualization/, tests/ and checks/. Optional launch/recovery controls
are available in SwarmGesture-Tools.cmd. Trained models and data are preserved.
Place the separately downloaded MediaPipe asset at models/hand_landmarker.task.

From this folder:

    python -m unittest discover -s simulation/tests -t . -p "test_*.py" -q

This is ideal preview only. Planned center spacing does not establish hardware
rotor clearance or real flight safety. Existing manual arming is required.

Automatic Snake is available through SwarmGesture-Tools.cmd or tools/launch/Start-SwarmGesture-Snake.cmd. It starts with three snake drones, twelve apples and four borders, splits at nine, and returns to the airborne grid on completion. See docs/snake.md.
