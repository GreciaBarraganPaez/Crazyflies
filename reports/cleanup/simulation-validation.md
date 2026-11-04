# Simulation folder cleanup - 4 November 2026

Fifty loose source/startup/check files moved into responsibility-based packages.
The simulation root now contains the folder guide and package marker. Runtime
code is grouped into controllers/, servers/, core/ and visualization/, alongside
the existing formations/, runtime/ and scenes/. Startup scripts live in launch/;
maintenance utilities in tools/. Fifteen offline test files live in tests/ and
eight integration/firmware/manual checks in checks/.

No test coverage or working controller was removed. The stepped controllers
remain active physics-fallback dependencies. Shared fake fleets/input scenarios
now live in tests/helpers.py; native check adapters in checks/helpers.py. Runtime
packages have no dependency on tests or checks. All source imports use qualified
simulation package names. Shared config/report locations use core/paths.py.

Normal root startup and the optional tools menu are unchanged. Their shared
launcher resolves scripts from simulation/launch/. Bash scripts start modules
from the project root. ROS starts servers using -m with an explicit project
working directory. Duplicate guards recognize both previous script processes
and the new module processes. Tests/checks are not loaded at normal startup.

Validation:
- All 108 offline tests passed with discovery rooted at simulation/tests.
- The native five-formation sequence (including helix) passed, minimum spacing 0.556 m.
- The nineteen-drone automatic Snake/split/completion/landing regression passed.
- The eight-drone playable Snake/directions/growth/blocked-return/landing check passed.
- Both retained MarkerArray/head-identity checks passed.
- Each actual ROS launch mode started its module and shut down cleanly in isolated domain 88.
- ROS launch argument discovery, Bash syntax and PowerShell syntax passed.
- Controller/UDP-tool help commands import successfully as modules.
- Runtime dependency boundaries, current Markdown links and launcher dependency paths resolve.
- All saved fleet/RViz config hashes and data/model/MediaPipe hashes are unchanged.

Native tests use domains 88/89 and do not command the live session. The startup
probe is headless, with no flight commands, and forwards one shutdown interrupt
through ros2 launch. The live preview checker was not run. No user session was
restarted and no model was retrained.

The original source/config layout is preserved in
archive/simulation-layout-2026-11-04/ with SHA256.json. File moves are recorded in
simulation-file-moves.json. Obsolete bytecode caches at the old flat paths were
removed; generated package caches may reappear normally. Validation JSON and
successful launch logs are stored beside this report.
