# Sodick LN2W dry-run kit, round 3 (2026-11-26)

Posted with the CamCraft post **Sodick Wire EDM (LN2W)** at PR [NeoTech/Camcraft#4065](https://github.com/NeoTech/Camcraft/pull/4065) head `5bd7ff4dd` (reviewed clean). Same two test parts as rounds 1 and 2.

| File | Part |
|---|---|
| `edm-test-square-1pass-ln2w.nc` | [square](../edm-test-square.pdf), one contour, 1 pass |
| `edm-test-2axis-1pass-ln2w.nc` | [2-axis block](../edm-test-2axis.pdf): holes and a notch, re-threads between cuts |

What changed from round 2 (the machine owner's correction):
- `U0. V0.` is now **on the rapid to each start point**: `G00 X.. Y.. U0. V0.`, then `Z0.`, `T91`, `T84`, `T94`, `C...`, then the first cut. There is no separate `U0. V0.` line any more. Reason: the heads are upright before threading, so they stay upright after it.
- Still no `G21` (E00170 in round 1).

Please **dry run with threading enabled**, as before: units **mm**, **Z0 at the upper head height above the part**, work offset at X0 Y0.

Tell us: does each program run end to end, any alarm (number + text + line), and anything else the control wants differently.

Clean-room: please describe what your control accepts; no programs from other CAM software.
