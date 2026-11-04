# Simulation architecture and extension guide

The current system is suitable for additional fixed-fleet looping silhouettes.
It is not yet a general game/3D scene engine. This review uses the checked-out
implementation and the 29 October handover's product vision; the handover's
static-only startup instructions describe an older version.

## Active boundaries

| Files | Responsibility |
| --- | --- |
| `simulation/core/formation_registry.py` | One declaration per formation: gesture, period, entry/loop/request IDs, interpolation resolution, motion function |
| `simulation/formations/heart.py`, `sine.py`, `spiral.py`, `moon.py`, `helix.py` | Pure per-point position/velocity/acceleration models; no ROS, input or flight state |
| `simulation/core/static_shapes.py` | Fleet/grid geometry, canonical silhouettes and fixed drone assignment |
| `simulation/core/continuous_trajectories.py` | Shared entry phase ramp, speed scaling and quintic compilation |
| `simulation/core/blended_transitions.py` | Full-fleet C2 joins and conservative whole-curve center-distance/height certification |
| `simulation/core/playback_controls.py` | Demo schedule using simulation time; produces ordinary gesture requests |
| `simulation/controllers/smooth_animation_bridge.py` | Preview flight lifecycle, backend selection, grounded speed uploads and keyboard controls |
| `simulation/runtime/playback.py` | Native loop state and measured canonical normalization before grid return |
| `simulation/runtime/joined_transitions.py` | Transition status protocol, source-state restoration on rejection and palm-priority queue |
| `simulation/controllers/gesture_bridge.py` | UDP/keyboard input, manual arming, static state machine, fresh-TF grid-first landing |
| `simulation/controllers/heart_animation_bridge.py`, `simulation/controllers/formation_animation_bridge.py` | Active stepped fallback, stop sequencing and resting-shape routes |
| `simulation/servers/preview_server.py` | ROS adapter, native firmware playback, asynchronous planning and exact loop scheduling |
| `simulation/visualization/formation_colors.py`, `simulation/visualization/drone_markers.py` | Geometry-fitted palettes and frame-locked RViz visualization |
| `simulation/config/`, `simulation/launch/choreography_preview.launch.py`, `start_*.sh` | Fleet/RViz configuration and startup |
| `simulation/test_*.py`, `check_*.py` | Offline tests and isolated/live integration checks |

The motion compiler, request mapping, gesture selection and demo order all use
the registry. Existing script entry points and canonical geometry stay in place
so the launchers, physics fallback and historical tests continue working.

## Playback and transitions

The ideal preview runs at 50 Hz. At 1x the periods are heart 3.2 s, sine 6 s,
spiral 8 s and moon 10 s. The spiral rotates back and forth at constant size;
moon phases move its left terminator between full and half outlines. `speed 0.5..1.25` is accepted only while grounded and disarms takeoff;
all entry/loop trajectories are re-uploaded before the next flight. Speed resets
to 1x on bridge restart. Velocity scales with speed and acceleration with its
square. Takeoff, transition and landing timing stay independent of loop speed.
Colors fit actual poses, so they follow speed without a second oscillator.

The server derives the destination speed from the uploaded loop duration and
checks that all drones have matching loop durations. Its capability parameter
prevents a new bridge from silently using a pre-speed-support server.

Shape changes forecast the outgoing state 0.30 simulation seconds ahead, plan
on a worker thread, and compare the actual state at commitment. Three joined
quintics fan out into graph-colored depth lanes, morph, and join the next loop
with matched position, velocity and acceleration. Bernstein hull subdivision
checks the complete curves against 0.52 m center separation and 0.6 m altitude;
uncertain plans are rejected and the outgoing animation continues. Additional
short fan-out candidates handle fast heart-entry switches without reducing
clearance. These checks describe ideal point trajectories, not physical drone
body/rotor clearance or physics tracking-error guarantees.

Reserved IDs come from the registry: heart 70/71/80, sine 72/73/82, spiral
74/75/84 and moon 76/77/86 (entry/loop/blend request). ID 90 is the reusable three-piece blend.

`demo` starts only from the airborne grid or a running formation. It holds each
shape for at least 12 simulation seconds and two loop periods, then cycles
heart -> sine -> spiral -> moon. It never arms or takes off automatically. Any received
gesture or landing request cancels it; `demo off` lets the current motion finish
its ongoing transition and continue. A rejected transition cancels the demo.

## Adding a formation

1. Add its assigned canonical targets to `simulation/core/static_shapes.py`. Check target count,
   height, spacing, and both grid paths; do not silently reorder drone IDs.
2. Add a pure `evaluate(point, phase, phase_velocity, phase_acceleration)` in
   `simulation/formations/`. Its phase-zero position must equal the canonical
   targets; position, velocity and acceleration must agree across 2-pi wrapping.
3. Register it once in `simulation/core/formation_registry.py`, with unique IDs excluding 90.
   A new recognized webcam gesture also requires recognition/training and sender support;
   the registry alone does not create a new recognized hand gesture.
4. Add pose fitting and a palette in `simulation/visualization/formation_colors.py`. This remains a
   separate visualization concern. The existing fitter supports only known shapes. Moon uses terminator position;
   constant-size spiral colors use its observed rotation.
5. Run the generic entry/loop, full-curve transition, speed-boundary, stop and
   landing checks. A formation that is safe at rest can still be unsuitable
   for the current transition or grid-return route.

For this class of formation, the compiler and preview server should not need
another shape-specific branch. Physics animation remains opt-in per formation:
new preview models do not automatically become tested physics behaviors.

## What still needs restructuring

The default preview now inherits directly from the shared static flight lifecycle
(`SimulationController`), rather than through the stepped heart and sine classes.
Playback and transition protocol state live in separate composed runtime
components. `configure_backend` selects a separate stepped controller for physics;
the receiver uses that returned controller. Preview initialization does not run
stepped-heart preflight or fallback animation logic. Palm retains priority during
blends, initial formation entry and canonical normalization; fresh measured poses
gate grid return after normalization.

Tests, checks and entry scripts remain mixed in the simulation root, preserving
existing launcher and check commands. The `formations/` and `runtime/` packages
provide the first functional boundaries. A future cleanup can relocate tests and
visualization together with their import changes. General games still need scene
state and roles beyond this flight/playback separation.

The formation fleet remains nineteen drones. The moving helix extends the
formation models into Y depth; certified blends accept full 3D source position,
velocity and acceleration. Resting transitions color projected X-Z conflicts
before checking all depth-lane stages. Rings, a goal/ball and games still need
scene roles and dynamic targets beyond the formation registry. The separate
hand-controlled Snake uses its own eight-drone layout and scene planner.

## Validation and startup

Run `python -m unittest discover -s simulation/tests -t . -p "test_*.py" -v` from the root.
The suite includes all formation pairs, 16 default-speed entry/loop phases and
32 entry/loop phases at both speed bounds, including full-curve clearance and
moving destination derivatives. Firmware checks cover 3 and 19 drones at
0.5x, 1x and 1.25x, repeated loops and 16 stop phases per shape.

`simulation/checks/check_blended_preview.py` requires ROS_DOMAIN_ID=88 and invokes its own isolated
server callbacks. `--demo-rounds N` checks real demo scheduling; `--switches N`
uses seeded random switching moments; `--speed` selects the loop speed and
`--report PATH` saves measured results. See `simulation/README.md` for commands.
The current reports are in `reports/simulation/`.

Use the root launcher after landing and stopping the old bridge, markers,
webcam and ROS (ROS last). These changes require a full restart. Offline and
isolated checks do not start hidden copies of the live project.

The older experiments and documentation remain preserved under
`archive/legacy-2026-11-02/`, including checksums in its manifest. Models,
landmark data and the MediaPipe asset are unchanged.


## Moon input and appearance

`moon` + Enter in the continuous-preview bridge selects the new formation after
manual takeoff. Existing six webcam gestures keep their mappings; no additional
classifier gesture was trained. The demo includes moon automatically. The first
version changes between full and half outlines, with a fixed right circular limb
and a horizontally moving left terminator. It does not yet model a full lunar
cycle including new/crescent moon. The palette shifts between cool blue-white
and warm ivory using the fitted terminator position.


## Optional multi-role scene foundation

The eight-drone hand-controlled Snake is a separate scene, fleet configuration
and launcher, documented in [Hand Snake](snake-player.md). The shared flight
lifecycle exposes fleet names/home points as class defaults; the grid feedback
monitor accepts that same layout. Native scene scheduling accepts an injected
fleet and pure planner. The original nineteen-drone defaults are preserved.
Playable motion stores an ordered body trail plus a committed future cell;
hand input changes only future planning. Apple drones become the new head,
blocked/unvalidated routes use the certified grid exit, and this mode never
splits. The automatic Snake remains an independent animation mode.

Snake now supplies the first multi-role scene, with independent actor state,
roles, pickup/score rules and shared full-fleet trajectory planning. The existing
formation controller/server remain the default. The opt-in scene and native
runtime are documented in [Snake architecture](snake.md). It implements autonomous board traversal with continuous C2 corner transitions,
identity-preserving head growth, twelve visible apples and four actual border
drones. Seeded maze cycles replace the row sweep. At nine actors a certified
transition splits the chain into two independently growing snakes in separate
board regions; the combined length can reach fifteen. Every eaten apple becomes
its group's new leader. `scenes/snake_routes.py` builds the winding cycles,
`Snake` holds per-group state, and `SnakeScene` owns shared fleet roles. The
experimental pickup color pulse has been removed. Earlier circular/stop-at-node prototypes are archived. Freehand paths,
multiple scenes, other board games and a broader scene policy
interface remain future extensions; this does not turn the formation registry
into a game-state container.
