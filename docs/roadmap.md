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

## Next development stages

| Stage | Product work | Required foundation |
| --- | --- | --- |
| More choreography | Moon phases, real-time analog clock | Additional geometry/role definitions; correct time zone for clock; readability at fleet size |
| Interactive motion | Snake collecting drones into a following chain | Scene/game state, path history, assignment of head/chain/free drones, moving-path separation |
| 3D scenes | Interlocking rings; ball through a goal | General 3D trajectories, coordinated role groups, space-time clearance, deliberate camera viewpoint |
| Playable games | Tetris; gesture-controlled tic-tac-toe against a computer | Board state, turn logic, hand-position/cell selection, confirmation and clear visual feedback |
| Recognition and evaluation | More distinct gestures; independent participant/session testing | Preserve existing controls, train/evaluate new labels, update the learning journal and academic results |

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
