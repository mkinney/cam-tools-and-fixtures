# CAM tools and fixtures

Ready-to-import cutting-tool libraries and fixture models for [CamCraft](https://github.com/NeoTech/Camcraft), the open-source CAM package. Vendors publish their tools as product pages, not as CamCraft libraries, so these libraries were built from those pages.

**Not affiliated with any vendor named here.** Names and part numbers identify the products. Check every dimension against the vendor's current page before you cut.

## Tools: `tools/`

There are 47 libraries in CamCraft's tool library format (`camcraft-tools/1`, millimetres):

| Library | What |
|---|---|
| `lakeshore-carbide*.camtools` | Lakeshore Carbide end mills, ball and bull noses, chamfer mills, etc. |
| `almar-inch*.camtools` | Almar tools, inch |
| `tormach*.camtools` | Tormach TTS and BT30 tooling, plus the lathe set |
| `drills-{inch,metric}[-{carbide,hss}]*.camtools` | Generic jobber drills by size |

Each base library also comes in a per-material variant: `-aluminum`, `-mild-steel`, `-stainless`, `-brass` and `-acetal`. The variants carry starting rpm and feed values for that material.

- **Import:** in CamCraft, use Tools > Import library, or the MCP tool `import_tool_library`. All 47 files imported cleanly with zero refusals (`tools/PROVENANCE.md`).
- **Feeds and speeds** come from CamCraft's own cutting table, at the low end of each window. They are conservative starting points, not limits, and no vendor chart was used. See `tools/FEEDS-AND-SPEEDS.md` (and `.csv`). The rpm is capped at 10,000 for Tormach 770MX/1100MX spindles.
- **How they were made:** only the vendors' public HTML product pages, fetched within robots.txt at 1 request per second or less. No vendor CAM library file (Fusion, HSM, Vectric or CSV exports) was downloaded or read. The scripts are in `tools/builder/`; their crawl cache is not included.

## Fixtures: `fixtures/`

See `fixtures/README.md`. Vendor CAD is fetched from the vendor, never rehosted here.

## Licence

Scripts are under MIT (`LICENSE`). The library data (`.camtools`, FEEDS-AND-SPEEDS) is under CC BY 4.0. The underlying dimensions are facts from the vendors' public pages.

Corrections and new vendors are welcome: open an issue or a PR.
