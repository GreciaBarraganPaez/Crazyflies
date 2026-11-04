# Gesture control

Windows webcam -> MediaPipe 21 hand landmarks -> shared 63-feature normalization
-> mirrored SVM -> stable-gesture gate -> UDP 5055. In WSL: receiver -> controller
-> Crazyswarm2 simulator -> TF -> frame-locked RViz spheres.

| Label | Current default action |
| --- | --- |
| `one` | Take off only after manual arming |
| `peace` | Continuous heart pulse |
| `three` | Continuous travelling sine wave |
| `ok` | Continuous spiral: constant-size back-and-forth rotation (8 seconds) |
| `fist` | Return to grid |
| `palm` | Return to verified grid and land |

In the bridge terminal: **a + Enter** arms one takeoff; **x + Enter** requests
grid-first landing; **q + Enter** exits through the landing sequence.
Continuous-preview keyboard commands: `speed 0.5..1.25` while grounded
(for example `speed 1.25`), then arm again; `demo` after manual takeoff;
`demo off` to keep the current motion; `status` for current settings.
Speed resets to 1x on bridge restart. Any gesture or landing request cancels demo.

In the webcam window: **E** toggles transmission, **X** requests landing and
disables transmission, **Q** quits with a best-effort landing message.

The sender defaults to confidence >=0.80, a 0.7-second hold and 1.5-second
cooldown. A held label triggers once until changed/released. Unknown/uncertain
input sends nothing. UDP transmission is not a delivery acknowledgement.

After landing, restart the bridge with `tools/launch/Restart-SwarmGesture-Bridge.cmd` only
once the old process has stopped. Startup/profile changes require restarting
ROS too; see [launcher instructions](launching.md).

For a UDP-only diagnostic, stop the real bridge, run
`python3 -m simulation.controllers.gesture_bridge --dry-run` from the project root in WSL, then use
`python -m simulation.tools.send_test_gesture --host WSL_IP --gesture peace` from the
Windows project root. Stop the dry-run before starting the real bridge.

All flight work remains simulation-only. Palm/X request controlled landing,
not a guaranteed emergency motor cutoff. Planned/ideal-preview separation
checks do not validate physical flight.


Moon phases: after manual takeoff, enter `moon` + Enter in the preview bridge.
The outline changes smoothly between full and half moon over a 10-second cycle
at 1x. It is also included in `demo`. Existing hand gestures are unchanged;
no new webcam gesture has been trained. `heart`, `sine` and `spiral` also work
as keyboard formation commands. This update requires a full restart after landing:
stop bridge, markers and webcam, then ROS last; run Start-SwarmGesture.cmd again.
