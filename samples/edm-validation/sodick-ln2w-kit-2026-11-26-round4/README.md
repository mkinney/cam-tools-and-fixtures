# Sodick LN2W dry-run kit, round 4: taper (2026-11-26)

Posted with the CamCraft post **Sodick Wire EDM (LN2W)** at upstream `main` `1c0152c91`, which includes the 4-axis taper from PR [NeoTech/Camcraft#4171](https://github.com/NeoTech/Camcraft/pull/4171).

| File | Part |
|---|---|
| `edm-test-taper-1pass-ln2w.nc` | [taper test part](../edm-test-taper.pdf), outer walls, one pass |
| `edm-test-taper-1pass-ln2w.camproj` | the CamCraft project that posts it |

What is new from round 3:
- **A small constant taper.** The four outer walls of the taper test part lean 3 mm over its 20 mm height: 50 x 30 at the bottom, 44 x 24 at the top, 8.531 deg. They are straight lines only (no arcs), cut as a punch at X-35. Y0.
- **4-axis G74, the way the machine owner writes it.** After `C001` the program writes `TP`, `TN`, `G74`. Then each cut is `G01 X.. Y.. U.. V..`, with U V on every move. `G75` comes after the last cut, before `T90`. No `G51` / `G52`.
- **TP / TN words.** `TP` is the part bottom above the worktable and `TN` = `TP` + 20 mm (the part height).
- **TP is a PLACEHOLDER: `TP0.`** (part bottom on the table), so `TN20.`. We do not know your real height yet; see the question below.
- The start order stays: `G54` / `G00 X.. Y.. U0. V0.` / `Z0.` / `T91` / `T84` / `T94` / `C001` / then the taper words and the cut. Still no `G21`.

Please **dry run with threading enabled**, as before: units **mm**, **Z0 at the upper head height**, work offset at X0 Y0.

Tell us:
- does it run end to end,
- any alarm (number + text + line),
- does the taper look right on the control's graphics (top smaller than bottom, walls leaning in by 3 mm).

One question: **what is the real height of the part bottom above the table** (mm) in your setup? We will put it in as `TP`.

Clean-room: please describe what your control accepts; no programs from other CAM software.
