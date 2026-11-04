# ROS and firmware checks

These are development/diagnostic programs, not the scripts used for startup.
Run module commands from the **project root**, in a ROS-configured WSL shell
with the existing firmware/Python paths available.

| Module | Scope |
| --- | --- |
| `check_blended_preview` | Current five-formation preview, smooth changes, colors and landing; isolated ROS domain 88 |
| `check_continuous_backend` | Isolated firmware objects: entry/loop/stop phases for all formations and speed bounds |
| `check_heart_backend` | Retained stepped heart/wave and resting-route firmware checks for the fallback |
| `check_snake_preview` | Nineteen-drone automatic Snake, split, collection, grid return and landing; domain 89 |
| `check_play_snake` | Eight-drone playable Snake, four directions, growth, blocked-path return and landing; domain 89 |
| `check_snake_markers` | Retained MarkerArray snapshot and both automatic Snake head labels; domain 89 |
| `check_play_snake_markers` | Eight-drone retained markers and actual head identity; domain 89 |
| `check_live_preview` | Manual check that deliberately commands the running ideal simulator; stop the interactive bridge first |

Examples, run sequentially:

```bash
ROS_DOMAIN_ID=88 python3 -m simulation.checks.check_blended_preview --report reports/simulation/preview.json
ROS_DOMAIN_ID=89 python3 -m simulation.checks.check_snake_preview --limit 15
ROS_DOMAIN_ID=89 python3 -m simulation.checks.check_play_snake
ROS_DOMAIN_ID=89 python3 -m simulation.checks.check_snake_markers
ROS_DOMAIN_ID=89 python3 -m simulation.checks.check_play_snake_markers
python3 -m simulation.checks.check_continuous_backend
```

The isolated checks create their own server/planner objects and do not command
the live project. Do not run two checks on the same isolated domain together.
`check_live_preview` is intentionally different: it controls the currently
running ideal simulator and reserves UDP 5055. It is never part of the offline
suite or normal startup.

`helpers.py` provides adapters to the check process's own server; it is shared
by the formation and game checks. Center-spacing results apply to ideal motion,
not real rotor clearance or tracking error.
