# Historical source snapshots

These files preserve earlier working stages and experiments. They are not
launch targets and are excluded from the active test suite. Current startup is
`../Start-SwarmGesture.cmd`; the optional modes are in `../SwarmGesture-Tools.cmd`.

| Folder | Preserved stage |
| --- | --- |
| `legacy-2026-11-02/` | Retired seven/eighteen-drone experiments and original planning material |
| `formation-baseline-2026-11-03/` | Validated continuous formations before the game work |
| `circular-snake-2026-11-03/` | Earlier circular Snake prototype |
| `grid-snake-tail-growth-2026-11-03/` | Earlier grid-node/tail-growth implementation |
| `automatic-snake-baseline-2026-11-03/` | Working automatic Snake before the separate hand-controlled mode |
| `main-folder-2026-11-04/` | Root scripts before the main-folder cleanup |
| `simulation-layout-2026-11-04/` | Working source/config layout before simulation packaging |

SHA256 manifests are retained where they were originally created. Git disables
line-ending conversion under this folder so historical byte hashes remain
meaningful on Windows and Linux. Old paths and launcher instructions inside a
snapshot describe that historical version; use current guides in `../docs/`.
