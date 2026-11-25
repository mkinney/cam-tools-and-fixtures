# Siemens 840D sl test kit (2026-11-25)

Three metric programs posted by CamCraft from `main` at `83d52ef6a` with the built-in post **Siemens 840D**
(3-axis, `G17 G710 G90 G54`). Please **simulate first, then air cut** (spindle off, Z well above the part).

| File | Part | Operations |
|---|---|---|
| `first-part-840d.mpf` | 2D first part | face, pocket, contour, drill (D10 + D6 end mills, D6 drill) |
| `hole-work-840d.mpf` | hole work | drill (incl. a bolt circle), tap drill, thread milling (D6 thread mill) |
| `rough-finish-840d.mpf` | 3D rough + finish | 3D pocket roughing (D6 end mill) and finishing (D6 ball nose); a long program |

Tools: each program names its tools in comments (`; T3 EM-1000-4FL - FLAT END MILL D10` ...); map them to your own tools/pockets or edit the T/D words. Work offset G54 at the part zero described in the program header.

## What we would like to know (as statements, please)

1. **Control:** 840D sl software version (from the control's version screen).
2. **Does each program load and simulate** in the control's simulation (ShopMill or the program editor)? Any alarm: the number, text and line.
3. **Words:** `G710`, `T3 D3 M6` tool change, `G0/G1/G2/G3`, `M8`, the `N` numbering - anything your 840D sl wants differently (e.g. `T="name"`, `CYCLE81/83` for drilling, `G64`/`CYCLE832` for smoothing).
4. **Air cut:** does it move as the plot shows?

**Clean-room:** please describe what your control accepts. Do not send programs or posts made by other CAM software (SolidCAM, Tebis, Fusion ...).

Report back to Mike (Discord) or on a GitHub issue in NeoTech/Camcraft.
