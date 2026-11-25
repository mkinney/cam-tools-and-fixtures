# Sodick dry-run kit (2026-11-25)

Two small wire EDM programs posted by CamCraft from `main` at `3bb6647f6` with the built-in post
**Sodick Wire EDM (Mark 21)** and the ALC400G test machine. Please **dry run only** (no wire, no cut):
load each program, run it on the control without machining, and tell us what the control says.

| File | Part | What it cuts |
|---|---|---|
| `edm-test-square-1pass-sodick.nc` | [edm-test-square](../edm-test-square.pdf) | one contour of a small square with rounded corners, 1 pass |
| `edm-test-2axis-1pass-sodick.nc` | [edm-test-2axis](../edm-test-2axis.pdf) | the 2-axis test block (a row of holes and a notch), 1 pass |

## What we would like to know (as statements, please)

1. **Control:** model and version (LN1, LN2, LN3, ...?).
2. **Does each program load?** Any line the control rejects or warns about: the line and the message.
3. **Words:** are `T91`, `T84`, `T94`, `C000`, `G54`, `G40`, `G03 ... I J` read the way the comments in the program say?
4. **Conditions:** the program calls `C000`. What does your control expect a condition call to look like?
5. **Taper (issue [#2130](https://github.com/NeoTech/Camcraft/issues/2130)):** your machine's heights (worktable to lower guide, worktable to program plane / part bottom, upper guide), and whether taper is `G74/G75` with `U V` or `TP/TN` - as your manual or control describes it.

**Clean-room:** please describe what your control accepts. Do not send programs made by other CAM software.

Report back on [NeoTech/Camcraft#1500](https://github.com/NeoTech/Camcraft/issues/1500) (or via Mike).
