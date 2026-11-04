# Archive inventory

The cleanup preserved original bytes; `manifest.json` records SHA-256 checksums.

- Root `gesture_bridge.py` and `drone_markers.py`: stale copies; active versions live in `simulation/`.
- `simulation/formations.py`, `formation_demo.py`, `test_gesture_bridge.py`: retired seven-drone geometry/controller experiment.
- `simulation/animations.py`, `test_phase1.py`: retired eighteen-drone animation experiment.
- `simulation/README_ANIMATION_FIX.md`: obsolete replacement/ZIP instructions.
- `formation_preview.png`, `static_shapes_preview.png`: historical generated previews.
- `Start-SwarmGesture-Preview.cmd`: redundant alias; the normal launcher already defaults to preview.
- Root `README.md`, `docs/gesture-control.md`, `simulation/README.md`: historical documentation snapshots before consolidation.

The old gate/protocol assertions were retained in the active `simulation/test_gesture_gate.py`.
The project plan was relocated to `docs/project.md` in the active tree, rather than archived.

Do not launch archived code against the current nineteen-drone fleet. Older
scripts and tests assume different counts, coordinates and controller interfaces.
