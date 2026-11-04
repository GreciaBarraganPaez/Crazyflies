# Simulation validation — 2 November 2026

Current implementation: independent preview flight controller with composed
playback and joined-transition components; constant-size rotating spiral;
full-to-half moon outline as the fourth formation. The active offline suite
passed 75 tests. Installed firmware planner checks passed for 3 and 19 drones
at 0.5x, 1x and 1.25x, with repeated loops and 16 canonical/in-place stop phases
per formation. All formation pairs are checked over entry/loop phases and
supported speed boundaries.

These reports come from isolated preview-server integration on ROS domain 88:

| Report | Speed | Completed transitions | Simulation seconds | Minimum measured center spacing |
| --- | --- | --- | --- | --- |
| `default-1x.json` | 1x | 4 | 58.30 | 0.5562 m |
| `demo-1.25x.json` | 1.25x | 8 | 154.22 | 0.5562 m |
| `demo-0.5x.json` | 0.5x | 4 | 139.84 | 0.5562 m |
| `random-1.25x.json` | 1.25x | 30 | 261.46 | 0.5562 m |

All four runs checked center separation >=0.52 m, airborne formation/transition
height >0.6 m, no intermediate goTo commands during formation changes, no
rejected transitions and final grid-first landing. The lowest measured airborne
height was 0.6077 m in the random run. Each offline transition plan also needs
the existing whole-polynomial certificate; sampled measurements alone are not
the planning acceptance test.

Demo checks exercise actual scheduling over all four formations, loop speed
uploads, automatic joins, constant spiral size and full/half moon travel.
Unit tests cover manual override, palm priority during blends/entry/normalization,
measured normalization arrival before grid return, grounded-only speed changes,
invalid inputs, pose-synchronized palettes and separate physics selection.

This is ideal-motion simulation evidence, not physical-drone clearance or
tracking-error validation. Reproduce using `simulation/README.md`; reports are
overwritten only when their paths are explicitly passed with `--report`.
