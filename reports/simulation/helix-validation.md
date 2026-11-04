# 3D helix validation - 4 November 2026

All 108 offline tests passed. Five new helix checks cover constant radius,
nonzero depth motion, analytic velocity/acceleration during entry and looping,
whole-polynomial separation at 0.5x/1x/1.25x, pose-synchronized color phase and
the keyboard command using blend request 88. Existing exhaustive formation
tests now include helix among all static and moving-source pairs, including
16 entry/loop phases at 1x and 32 phases at both speed bounds.

The native isolated run `helix-preview.json` passed heart -> sine -> spiral ->
moon -> helix -> heart, held helix through more than one full cycle, and finished
with measured grid-first landing. The helix's Y velocity remains nonzero in
combination with Z velocity; measured depth range for an individual drone
exceeds 2.5 m. No intermediate goTo command was issued during formation changes.

`helix-demo-fast.json` passed the complete five-formation demo at 1.25x, including
moving helix entry/exit and final landing. Both native runs recorded minimum
fleet center spacing about 0.556 m. The installed firmware planner checks also
passed 3 and 19 drones at 0.5x, 1x and 1.25x, with sixteen moving stop phases
per formation, native canonical normalization and high-level grid landing.

The static helix assignment certifies the direct grid path above 0.600 m.
Continuous entry/loop curves retain fixed distinct X coordinates with at least
0.6 m X spacing. All complete blend curves still require the existing >=0.52 m
center-separation and >0.6 m altitude certificates; the old front-plane rejection
has been replaced by finite 3D source-state validation plus those certificates.

The saved RViz configuration preserves the current front camera and adds
Front formations / 3D Helix saved views. MarkerArray remains enabled. Existing
formation geometry/IDs and all trained webcam labels are preserved. Games are
unchanged and remain on their separate launchers.

Tests use their own server/firmware objects on isolated ROS domain 88 and do
not command the live session. Results cover ideal simulation and center
separation, not physical rotor clearance or real tracking errors.
