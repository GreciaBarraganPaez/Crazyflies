# Product direction

Reviewed against `C:/Users/Marco/Downloads/SwarmGesture_Codex_Handover.md`
(29 October 2026). Its vision remains relevant; its static-only implementation
and startup steps have been superseded by the current animated preview.

## End goal

SwarmGesture is an interactive drone choreography and game system. Gestures
select animations that keep running until changed, with recognizable audience
views, synchronized colors, manual takeoff arming and controlled grid-first
landing. The initial fleet is 15-20 simulated drones (currently 19), with more
only where shape resolution needs it. Physical flight and physical LEDs require
separate hardware work and validation.

## Current progress

Continuous symmetric heart, traveling sine and constant-size rotating spiral are
implemented, with joined transitions and pose-synchronized colors. The current
extension adds gold-purple spiral lighting, grounded speed selection, a demo
sequence, shared formation metadata, separate motion models and longer checks.
The preview controller now has separate playback/transition components, and
moon phases provide a first extension (full-to-half outline, selected by keyboard).
This covers the handover's first motion phase; visual acceptance of each update
still belongs to the user in RViz.

The analog clock is now implemented as a simulation formation. It uses a
two-hand wrist-pointing gesture, local Europe/Berlin time at startup, paired
landmark recording and a separate clock SVM. Session-held-out evaluation currently
reports 99.11% test accuracy with a 0.63 percentage-point train/test gap. The
clock remains simulation-only while its time-dependent entry routes are not yet
certified for physical flight.

The team also completed the first multi-role scene work this week: automatic
nineteen-drone Snake with growth/splitting and grid return, plus a separate
eight-drone hand-controlled Snake game. The shared continuous runtime now also
supports the moving 3D helix, joined transitions and pose-synchronized colors.

## Next development stages

| Stage | Product work | Required foundation |
| --- | --- | --- |
| More choreography | Moon phases, real-time analog clock | Time-aware hand updates and certified entry/transition routes; readability at fleet size |
| Interactive motion | Snake collecting drones into a following chain | Scene/game state, path history, assignment of head/chain/free drones, moving-path separation |
| 3D scenes | Interlocking rings; ball through a goal | General 3D trajectories, coordinated role groups, space-time clearance, deliberate camera viewpoint |
| Playable games | Tetris; gesture-controlled tic-tac-toe against a computer | Board state, turn logic, hand-position/cell selection, confirmation and clear visual feedback |
| Recognition and evaluation | More distinct gestures; independent participant/session testing | Add more clock participants/sessions and integrate the paired SVM into live recognition after validation |

The default preview is now separated from stepped physics inheritance.
Before interactive games, introduce a scene interface with explicit roles and state.
The current registry is an extension point for looping silhouettes, not a
replacement for that scene layer. See [architecture](architecture.md).

Optional Snake now traverses a rectangular board with smooth continuous corner
transitions. Three initial actors collect twelve visible apples; each apple
becomes its group's new head. Seeded winding courses replace the row sweep, and
the chain splits at nine into two snakes collecting in separate board regions.
Four cyan drones remain at the border, so maximum combined body length is
fifteen. Formation mode is preserved and older prototypes are archived.
A next milestone is richer game interaction or the next independent scene.
Moon phases are available for visual review; crescent/new-moon stages remain future work. Use the longer demo and random-switch checks as regression
evidence before each additional formation.
