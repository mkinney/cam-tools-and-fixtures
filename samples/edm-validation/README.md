# Wire EDM validation parts

Three small test parts for checking a wire EDM CAM and post path end to end. Made in SolidCraft (`.sc`, with a drawing inside), exported as STEP, with a PDF drawing and a picture of each. Millimetres, Z up, the part's bottom at Z0. Free to use.

| Part | File | What it tests |
|---|---|---|
| EDM-T1 square | `edm-test-square.*` | 40 x 40 x 10 plate with a 10 mm square opening at X0 Y0: the simplest die, one start hole, rough + skims. Same shape as a Sodick owner's known-good hand-written program. |
| EDM-T2 2-axis | `edm-test-2axis.*` | 60 x 40 x 20 block, straight walls: two chains of holes (dia 8 to 1) joined by 0.4 mm slits, an open comb (slots 1-3 mm), a closed comb of thin walls, scallops, a gear-like notched edge, a 0.3 mm kerf slit, a 6 mm angled corner. |
| EDM-T3 taper | `edm-test-taper.*` | 4-axis (UV): walls taper 50 x 30 to 44 x 24, a conical hole, a twisted 8 mm square (top turned about 20 deg), a round-to-square hole. |

Found with these in CamCraft 0.24.0 (wire EDM): NeoTech/Camcraft #3206-#3218 and #1500.
