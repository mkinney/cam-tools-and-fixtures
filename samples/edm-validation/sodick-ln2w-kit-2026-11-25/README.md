# Sodick LN2W dry-run kit, round 2 (2026-11-25)

Posted with the **new** CamCraft post **Sodick Wire EDM (LN2W)** (PR [NeoTech/Camcraft#4065](https://github.com/NeoTech/Camcraft/pull/4065), head `b12db2f06`), built from Sam's notes and the Sodick LN1W/LN2W manual. Same two test parts as round 1, so you can compare.

| File | Part |
|---|---|
| `edm-test-square-1pass-ln2w.nc` | [square](../edm-test-square.pdf), one contour, 1 pass |
| `edm-test-2axis-1pass-ln2w.nc` | [2-axis block](../edm-test-2axis.pdf): holes and a notch, re-threads between cuts |

What changed from round 1:
- No `G21` (it alarmed with E00170).
- Start order as Sam gave it: `G00 X Y` -> `Z0.` -> `T91` -> `T84` -> `T94` -> `C000` -> `U0. V0.` -> first cut.
- Header says the program threads the wire (T91) at each start point.

Please **dry run with threading enabled**, same as last time. Set the control's units to **mm**, set **Z0 at the upper head height above the part**, and the work offset at X0 Y0. The header line "(Sodick ALC400G test conditions)" is just the old test project's name; the words are the LN2W post's.

Tell us: does each program run end to end, any alarm (number + text + line), and anything else your control wants differently.

Clean-room: please describe what your control accepts; no programs from other CAM software.
