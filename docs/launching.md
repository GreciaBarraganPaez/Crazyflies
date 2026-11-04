# SwarmGesture launcher

Double-click **Start-SwarmGesture.cmd** in the repository root. It opens four
terminals: ROS + RViz, gesture bridge, colored markers, and Windows webcam.
The default is the fast **ideal-motion preview**, without physics.

Wait for **Listening on UDP** in the bridge, enter **a + Enter**, then click
the webcam window and press **E** to enable gesture sending.

| Gesture | Action |
| --- | --- |
| One | Take off |
| Peace | Continuous pulsing heart |
| Three | Continuous travelling sine wave |
| OK | Spiral rotates back and forth at constant size (8-second cycle) |
| Fist | Return to grid |
| Palm | Return to verified grid, then land |

The preview runs at 50 updates per second. Heart period: **3.2 seconds**;
wave period: **6 seconds**. Uploaded polynomial pieces join in position,
velocity and acceleration. The preview server repeats them at exact simulation
time boundaries, so the heart passes its middle size without stopping and the
wave no longer hovers at every sampled point. First entry accelerates smoothly
from rest; natural size extrema and wave peaks still reverse direction.

The default bridge is `simulation/controllers/smooth_animation_bridge.py`. It uploads the
programs before printing Listening. It requires the current `simulation/servers/preview_server.py`;
a bridge-only restart cannot upgrade an older running server. Existing stepped
heart/wave scripts are retained. Physics mode uses their conservative timings.

## Speed and automatic demo

Enter commands in the bridge terminal, each followed by Enter:

| Command | Behavior |
| --- | --- |
| `speed 0.75` | Slower animation loops; accepted only while grounded |
| `speed 1.25` | Faster loops; supported range 0.5-1.25 |
| `speed 1` | Restore default speed |
| `demo` | After manual takeoff, cycle heart -> sine -> spiral -> moon -> helix |
| `demo off` | Stop cycling; keep the current animation/ongoing transition |
| `status` | Print flight state, current formation, speed and demo status |

Speed re-uploads all loops and disarms takeoff; enter `a` again afterward.
Speed resets to 1x when the bridge restarts. Takeoff, morphs and landing keep
their normal timing. Speed/demo commands require the continuous preview backend.
Demo mode holds each formation for at least 12 simulation seconds and two loop
periods. Any received gesture or landing request cancels it. For an unattended
show, disable webcam sending with E before entering `demo`. Manual arming,
takeoff and grid-first landing still apply.

This update changes the server, motion imports and marker colors: perform a
full restart once, using the sequence below. Validation does not launch a
background live simulator.

## Restart after editing

| Change | Restart procedure |
| --- | --- |
| Bridge input/keyboard logic only | Land and verify grounded. Ctrl+C in terminal 2 and wait for Bridge stopped. Double-click **tools/launch/Restart-SwarmGesture-Bridge.cmd**. Keep ROS, markers, webcam open; arm again. |
| Motion models, registry, preview server, configuration, or backend | Land and verify grounded. Stop bridge, webcam and markers with Ctrl+C, then ROS last. Wait for the processes to stop; use **Start-SwarmGesture.cmd** again. |

Keep ROS running while the bridge finishes landing. Closing windows abruptly
can leave processes alive; Ctrl+Z suspends them. Duplicate simulator/bridge
starts are refused. Bash files must retain LF line endings (`.gitattributes`).

**tools/launch/Start-SwarmGesture-Physics.cmd** selects NumPy physics, which was measured at
~0.08x real time for 19 drones on this machine. The normal launcher now selects
preview. Both the ROS window title and bridge startup messages identify the mode.

`tools/launch/Start-SwarmGesture.ps1 -FormationMode heart` selects the old heart-only
controller; `-FormationMode static` selects static formations.

If WSLg reports a missing X11 socket or cannot open RViz, finish landing and stop
the programs first. **tools/launch/Start-SwarmGesture-Clean.cmd** is a recovery option that
shuts down **all** WSL distributions, including unrelated Docker workloads.
It is not needed for routine Python edits. ROS setup is sourced without Bash
nounset, and all scripts use the named SwarmGesture-Ubuntu distribution.

## Transitions and separation

Fast-preview shape switches use a single joined high-level trajectory. The
outgoing position, velocity and acceleration are continued into a depth-lane
morph, whose endpoint joins the next animation's moving loop. There is no
separate stop-at-current-position command, alignment hover, or per-waypoint
wait. A short look-ahead lets planning run while the old animation continues.

The complete polynomial paths are conservatively checked with Bernstein hull
subdivision against the 0.52 m center-separation threshold and 0.6 m height
floor. Unresolved/unsafe plans are refused, leaving the old formation running.
The source state is checked again at the scheduled join to prevent stale plans.
Physics fallback retains the earlier staged transition/feedback behavior.
Fist and palm still stop, return to the verified grid, and land when requested.

These are simulation point-trajectory and waypoint checks, not physical collision
avoidance or a guarantee about body/rotor contact under tracking errors. The ideal
preview follows planned positions exactly. Validate measured physics trajectories
separately before treating these routes as safe for physics or real flight.

## Checks

From simulation/ in the ROS-configured WSL shell:

```bash
python3 -m unittest discover -p "test_*.py" -v
python3 -m simulation.checks.check_continuous_backend
```

The backend check creates isolated planner objects; it sends no fleet commands.
For the live ideal-preview check, first stop the interactive bridge, then run:

```bash
python3 -m simulation.checks.check_live_preview --ros-args -p use_sim_time:=true
```

It reserves UDP 5055, refuses non-ideal backends, deliberately arms the simulated
fleet, checks heart loops and sine loops, switches shapes, and lands via grid.
The previous successful continuous-playback live run completed at 1.00x real
time with 0.556 m minimum measured center spacing. The subsequent current-pose
switch fix passes the offline and isolated firmware checks; its live recheck
was blocked during ROS client startup before takeoff. This is not a universal
clearance guarantee.


## Saved RViz colors

Both launch modes load `simulation/config/swarmgesture.rviz`. It contains an
already-enabled MarkerArray for `/swarmgesture/markers`, Fixed Frame `world`,
the saved front-facing camera view, and disabled TF axes/robot-model overlays.
Keep the markers terminal running: it provides the spheres and colors. No need
to add the MarkerArray display after reopening RViz. Save later layout/camera
adjustments to this project configuration with File -> Save Config (Ctrl+S).


The joined-transition update requires restarting **both ROS and bridge** once,
after landing, because its scheduler lives in the preview server. Continue using
`Start-SwarmGesture.cmd`; the saved colored RViz configuration is unchanged.

For an isolated check of the actual preview server, worker and controller:

```bash
ROS_DOMAIN_ID=88 python3 -m simulation.checks.check_blended_preview
```

Run from simulation/ in the configured WSL shell. It creates its own simulator
on domain 88, uses direct callbacks, and does not send commands to your live
fleet. The heart -> sine -> spiral -> moon -> heart -> grid-landing check passed with
no intermediate goTo commands during shape changes and minimum measured
center spacing 0.556 m. This validates the ideal preview, not physical tracking.


## Automatic animated colors

The marker terminal defaults to `--palette auto`:

- Heart: deep crimson while small, warm light red while expanded; the halo follows brightness.
- Sine: a full rainbow travels with the actual wave; crests glow brighter.
- Grid: calm cyan. Animated spiral: a traveling gold-purple gradient at constant brightness; size stays fixed.
- Between formations: palettes fade smoothly through a neutral color.

`simulation/visualization/formation_colors.py` fits the known assigned geometry to current TF positions
and uses heart scale / sine phase / spiral rotation and scale for colors, including entry ramps. There is
no independent color oscillator to drift away from the motion. Color messages
update at 20 Hz; marker positions remain frame-locked and follow RViz's normal
TF/render rate. The color layer never sends flight commands.

To restore the old static rainbow, stop the marker terminal and run
`python3 simulation/visualization/drone_markers.py --palette rainbow --ros-args -p use_sim_time:=true`
from simulation/ in the configured WSL shell. Other static palettes remain
cyan, pink, gold and violet. After color-only code edits, restart just the
marker terminal (`tools/launch/Start-SwarmGesture.ps1 -Role markers`) after stopping the old
one; the flight controller and current animation can keep running.


Moon phases: after manual takeoff, enter `moon` + Enter in the preview bridge.
The outline changes smoothly between full and half moon over a 10-second cycle
at 1x. It is also included in `demo`. Existing hand gestures are unchanged;
no new webcam gesture has been trained. `heart`, `sine` and `spiral` also work
as keyboard formation commands. This update requires a full restart after landing:
stop bridge, markers and webcam, then ROS last; run Start-SwarmGesture.cmd again.


## Moving 3D helix

The normal formation launcher also supports `helix` + Enter after takeoff:
a continuously moving 3D corkscrew, included in `demo`. Use RViz's saved
**3D Helix** view for an angled camera, or **Front formations** to restore the
front view. Restart all four formation programs after landing to load this
update. See [3D helix](helix.md).

## Separate Snake mode

For the **eight-drone hand-controlled game**, use
`tools/launch/Start-SwarmGesture-Snake-Player.cmd`. It keeps one snake with three initial
members and five apples. Arm, enable sending with E, take off with one finger,
then start with peace. Point one finger and move the hand left/right/up/down in
the mirrored webcam view. Center means straight; steer early for smooth turns.
Fist returns to grid and palm lands. All apples collected or a blocked path
returns to the airborne grid automatically. See [Hand Snake](snake-player.md).
Stop the four existing programs before switching to this separate eight-drone
fleet. The nineteen-drone automatic Snake below remains available.

`tools/launch/Start-SwarmGesture-Snake.cmd` selects autonomous grid Snake. After takeoff,
peace/three/OK starts automatic movement and growth; no steering/collect input
is needed. This update needs a full Snake server/bridge/marker restart. The fresh
`snake-smooth.rviz` view loads the retained MarkerArray automatically. Default
layout: three snake drones, twelve apples and four static cyan border drones.
Winding routes replace the row sweep; at nine drones the snake splits into two
groups collecting in separate regions. Fixed role colors replace the removed
red pickup pulse. The default
`Start-SwarmGesture.cmd` still starts the existing formations. Land and stop
all four programs before switching modes. Snake uses the same nineteen-drone
configuration, its own view/colors, and the same manual arming and grid-first
landing controls. For Snake-only bridge restarts, use
`tools/launch/Restart-SwarmGesture-Snake-Bridge.cmd`. See [Snake instructions](snake.md).
