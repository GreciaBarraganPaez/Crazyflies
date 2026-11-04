# Winding and split Snake validation - 3 November 2026

The current offline suite passes 93 tests, including the existing formation
checks. The red pickup-color experiment has been removed from the active code;
markers now use fixed role colors.

The seeded maze generator produces one adjacent-cell cycle through each region.
The default full-board route has 36 turns instead of a row sweep. Tests verify
unique coverage, different seeded layouts, C2 joins, continuous body motion,
new-head identity, pickup-cell timing and complete polynomial clearance.

At nine members the chain splits into groups of five and four. All identities
are preserved, apples are redistributed between separate left/right regions,
and the four border drones remain stationary throughout the split. The default
run finishes with groups of eight and seven. Smaller caps retain one snake.

| Isolated native run | Split | Final lengths | Minimum measured center spacing | Missed joins |
| --- | --- | --- | --- | --- |
| `snake-split-15.json` | yes | 8 / 7 | 0.7000 m | 0 |
| `snake-split-seed1.json` | yes | combined 15 | 0.7001 m | 0 |
| `snake-winding-8.json` | no | 8 | 0.7000 m | 0 |

The default full run checks all twelve apple identities, both independently
growing snakes, no stopped body actors during the split, fixed border positions,
fist return/restart, landing during growth and manual rearming. Minimum observed
playing body speed is 0.5303 m/s and minimum splitting body speed is 0.2573 m/s.
The second seeded run additionally requests palm landing during the split; its
precertified exit joins successfully. No SDK goTo stream is used.

The ROS MarkerArray smoke check verifies retained delivery to a genuinely late
subscriber, nineteen frame-locked drone spheres/halos, fixed role colors, all
initial apples/borders and both head labels attached to the correct drone frames.

All native runs use isolated ROS domain 89 and do not command the user's live
session. Whole-fleet polynomial certificates require center spacing >=0.52 m
and altitude >0.6 m. Results apply to ideal preview, not physical rotor/body
clearance or real tracking errors. Older JSON reports remain historical evidence
for earlier Snake versions; see docs/snake.md for current reproduction commands.

## Automatic completion return

After the final apple handoff completes, the runtime starts its already certified
grid exit at the exact trajectory boundary. It queues no further game movement.
The controller waits for fresh grid position feedback, then holds airborne and
accepts a new game. A palm request during the return still upgrades it to landing.
Isolated runs `snake-auto-grid-15.json`, `snake-auto-grid-8.json` and
`snake-auto-grid-3.json` check full collection, automatic return without landing,
restart, explicit landing and manual rearming. The no-apple count-three case
returns after entry. These runs supersede the earlier keep-moving completion
behavior in the historical split reports.
