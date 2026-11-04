# Main folder cleanup - 4 November 2026

The main folder now contains two CMD entry points and no Python source files.
Normal Start-SwarmGesture.cmd keeps its original role. SwarmGesture-Tools.cmd
provides games, physics, stopped-bridge restart and confirmed WSL recovery.
Optional direct shortcuts and the shared PowerShell implementation now live
in tools/launch/. The shared script resolves the root two folders above itself.

Four Windows runtime modules moved into app/. Four recording/training/diagnostic
tools moved to tools/gestures/. MediaPipe's .task asset moved to models/.
The launcher guide moved to docs/launching.md. Current imports, CLI commands,
asset defaults, launcher dependencies and documentation links were updated.
A per-file explanation is in docs/project-map.md. Simulation organization was
not changed; its two helper imports and recovery hint were updated as needed.

Validation:
- All 108 existing offline tests passed on Windows.
- The ten playable-Snake/helper checks also passed in WSL after the import move.
- Webcam sender, recorder, trainer and prediction CLI help commands succeeded.
- The training CLI works from a different working directory.
- PowerShell syntax and the new menu's exit-only path passed without launching programs.
- All launcher dependency paths and active Markdown links resolve.
- All recorded data and trained model hashes match the before-cleanup manifest.
- The moved MediaPipe asset matches its original hash.
- Feature extraction, gesture-gating and hand-steering files are byte-identical.
- The mirrored classifier loads and its feature order matches the shared module.

Only obsolete root .pyc cache files were removed. No dataset, trained model,
working mode or historical source was deleted, and no live session was restarted.
A source snapshot is preserved in archive/main-folder-2026-11-04/; file-moves.json
and assets-before.json record the layout and asset checks.
