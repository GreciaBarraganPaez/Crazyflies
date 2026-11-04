# Moving 3D helix

Use the normal **Start-SwarmGesture.cmd** formation launcher. Land and stop the
four existing programs before restarting so the ROS server loads helix support.
This mode uses the original nineteen-drone fleet; the game launchers stay separate.

Arm with `a` + Enter, enable webcam sending with E, and show one finger to take
off. In the **bridge terminal**, enter **`helix` + Enter**. You can start from
the airborne grid or switch directly from another running formation. The normal
fist/grid and palm/landing controls still apply.

The new formation is a two-turn corkscrew along the horizontal X axis. It is
10.8 m long with a constant 1.4 m radius and center height 3.4 m. Each drone
keeps its X position and circles in Y and Z; the phase travels along the coil,
like a sine wave extended into depth. The loop period is six seconds at 1x speed.
It has no radius pulse, endpoint stop or cell-by-cell motion. Rainbow colors
follow the measured helix phase rather than an independent clock.

The front camera projects the helix into a sine-like view. In RViz's **Views**
panel, double-click the saved **3D Helix** view to see the corkscrew depth. The
saved **Front formations** view restores the existing front angle. The startup
camera is unchanged. MarkerArray stays enabled in the saved configuration.

The existing `demo` sequence now includes heart, sine, spiral, moon and helix.
The six trained webcam labels are unchanged; helix is a keyboard formation
command, like moon. Grounded `speed 0.5..1.25` also controls the helix animation.
The continuous version is provided by the ideal preview; the physics/static
fallback displays the resting helix geometry.

`formations/helix.py` supplies pure geometry and analytic position, velocity and
acceleration. The registry reserves entry/loop IDs 78/79 and blend request 88.
Existing IDs and geometry are preserved. The full-curve transition planner now
accepts finite 3D source motion, retaining its separation and altitude
certificates. The resting transition planner colors X-Z conflicts even when
endpoint depths vary, checking every resulting stage.

Offline tests cover entry/loop C2 boundaries, phase-speed scaling, derivatives,
constant radius, actual depth motion, pose-fitted colors, complete polynomial
clearance and transitions from all sampled phases at the supported speed
extremes. Native integration covers the full demo, helix entry/exit and measured
grid landing. These remain ideal center-spacing checks, not hardware flight
or physical rotor-clearance validation.
