# Tormach tooling for CamCraft

> **Not made, endorsed or supported by Tormach in any way.** This is an independent community library for [CamCraft](https://github.com/NeoTech/Camcraft), the open-source CAM package. Tormach, PathPilot, TTS and the part numbers below are Tormach's. Please don't contact Tormach support about these files; open an issue in this repository instead.

These libraries let a CamCraft user pick real Tormach tools by part number instead of typing in each one's dimensions.

## What is here

The files are in `tools/` on the `main` branch, in CamCraft's tool library format (`camcraft-tools/1`, millimetres).

| Library | Tools | What |
|---|---|---|
| `tormach-tts.camtools` | 107 | Tormach end mills, bull noses, chamfer mill and drills, each in a TTS ER16/ER20 holder |
| `tormach-bt30.camtools` | 107 | The same tools in BT30 ER16/ER20 holders |
| `tormach.camtools` | 107 | The same tools without holders |
| `tormach-lathe.camtools` | 78 | Turning, boring, grooving and threading holders, each with its insert (e.g. 33132 MTFNR 12-3C + 33139 TNMG 332) |
| `tormach-{aluminum,mild-steel,stainless,brass,acetal}.camtools` | 107 each | The holderless set, with starting rpm and feed values for that material |

- **Import:** in CamCraft, use Tools > Import library, or the MCP tool `import_tool_library`. All of them import with zero refusals (`tools/PROVENANCE.md`).
- **Feeds and speeds** come from CamCraft's own cutting table, at the conservative end, capped at 10,000 rpm. They are not Tormach's recommendations.

## How it was made

- **Sources:** only Tormach's public product pages, fetched within robots.txt at 1 request per second or less. They supplied each tool's part number, diameter, flutes, lengths, corner radius and coating.
- **Not used:** no Tormach CAM library, tool table export or feeds chart was downloaded or read.
- **Scripts:** the builder scripts are in `tools/builder/` (`crawl_tormach.py`, `map_tormach.py`, `map_tormach_lathe.py`).
- **Accuracy:** dimensions can be wrong or out of date. Check each tool against the current Tormach page, and touch it off, before cutting.

## What would make this better (for Tormach, if interested)

- An official, machine-readable tool data file: part numbers, geometry, and holder stick-out for TTS and BT30.
- Official download links for STEP models of the tools, TTS/BT30 holders and machine envelopes (770MX, 1100MX, 1500MX, 24R), and permission to turn them into CamCraft tool, fixture and machine files. None of them are in this repository today.
