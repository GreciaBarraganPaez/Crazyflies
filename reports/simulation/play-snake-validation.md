# Hand Snake validation - 3 November 2026

The offline suite passes 103 tests, including 10 new checks for four-zone hand
input, dwell/debounce/neutral/tracking loss, per-mode UDP labels, eight-drone
manual takeoff, future-turn C2 consistency, forbidden reversal, apple identity,
whole-path clearance, continuous body speed and certified wall exit.

`play-snake.json` records an isolated native ROS domain 89 run using exactly
eight actual simulated drones. Scripted hand-direction commands go through the
same controller handle entry point as webcam UDP. All four directions were
used; one snake collected all five apple drones and grew from three to eight.
Every eaten actor became the head. Minimum measured center spacing was 0.7000 m,
minimum existing-body speed was 0.4419 m/s, and no trajectory join was missed.
No per-frame SDK goTo stream was used.

The native run also checks automatic grid return and restart after completion,
automatic grid return at a blocked forward path, palm landing during growth,
refusal of unarmed takeoff and successful manual rearming.

The playable MarkerArray check confirms retained late-subscriber delivery,
eight TF-bound spheres/halos, five initial red apples, the saved board and one
head label bound to the actual eaten drone. YAML/PowerShell/Bash checks verify
the separate fleet, saved view, sender flag and launcher mode wiring. The sender
CLI imports its Windows dependencies and accepts --snake-player.

Regression evidence: `automatic-snake-after-player.json` passes the full
nineteen-drone winding/splitting animation, and `formations-after-player.json`
passes four native formation transitions, palette synchronization and measured
grid landing. The formation test's sine-crest assertion is scoped to active
sine playback; palette hysteresis during a blend does not imply intermediate
positions still form a sine curve. Formation movement and color logic are unchanged.

Before these shared extensions, the working automatic Snake and launcher files
were saved with SHA256 hashes in archive/automatic-snake-baseline-2026-11-03/.

No test commands target the user's live domain. Human steering still needs a
camera-visible one-finger gesture above the existing confidence threshold.
These results cover ideal preview and center-spacing certificates, not real
tracking error, rotor clearance or hardware flight.
