"""The hand-written text of REPORT.md; make_report.py fills the {{...}}
counts and tables from reports/*.json."""

TEMPLATE = r'''# CamCraft tool libraries: build report

Built on 2026-11-11 from the vendors' public HTML product pages only. No vendor CAM
library file was downloaded, read or converted. Every fetch obeyed the site's
robots.txt, ran at ≤ 1 request/s, and used the User-Agent
`camcraft-tool-library-builder (personal use)`. Tool names are generated from
dimensions and part numbers; no marketing text is copied. Lengths are in mm
(inch × 25.4 exactly).

All {{N_FILES}} library files were import-checked through CamCraft's own MCP
`import_tool_library`. `camcraft-cli` was built from upstream main `4c3f7565` in a
private worktree with a private `CARGO_TARGET_DIR`; the worktree has since been
removed. **Import refusals:** {{REFUSED}}

{{IMPORTS}}

## Files

| File | What |
|---|---|
| `lakeshore-carbide.camtools` | Lake Shore Carbide, base (aluminium-row feeds) |
| `almar-inch.camtools` | Almar Tools inch line, base |
| `almar-metric.camtools` | **not written**: Almar publishes no metric product pages (see Almar) |
| `tormach.camtools` | Tormach mill cutting tools, base |
| `tormach-bt30.camtools`, `tormach-tts.camtools` | the same Tormach tools with a BT30 or TTS holder envelope |
| `tormach-lathe.camtools` | Tormach lathe tools (holder + insert pairs) |
| `drills-inch*.camtools`, `drills-metric*.camtools` | vendor-neutral jobber drills; HSS and carbide variants, and both together |
| `<base>-{aluminum,mild-steel,stainless,brass,acetal}.camtools` | per-material variants of every mill/drill base file (`lakeshore-carbide`, `almar-inch`, `tormach`, `drills-{inch,metric}-{hss,carbide}`) |
| `FEEDS-AND-SPEEDS.md` / `.csv` | rpm, feed (mm/min and in/min), fz and conservative engagement per tool × material, plus the turning section |
| `src/` | scrapers, mappers, builders, README (how to re-run) |
| `cache/` | the fetched HTML and the crawl JSON |

### Rules that apply to every library

- **Kinds:** each product maps to the closest *exact* CamCraft kind (`end_mill`,
  `ball_nose`, `bull_nose`, `drill`, `taper`, and on the lathe `turning`, `bore`,
  `groove`, `thread`). Anything else is listed as unmapped with its URL, never forced in.
- **Stack:** `flute_len` = the page's flute length / LOC. `shank_len` = OAL − LOC (the
  plain stack above the flutes). No holder is set (`holder_d`/`holder_len` = 0, the
  setup's holder), except in `tormach-bt30`/`tormach-tts`.
- **Tool material and flutes:** every milling tool and drill carries `tool_material`
  (carbide unless the page says HSS or cobalt; cobalt uses the HSS column) and `flutes`
  from the page, so CamCraft's own feeds/speeds suggestion works for any work material.
  A tool whose page gives no flute count has `flutes` unset (listed under decisions).
- **Feeds and speeds:** CamCraft's own `crates/tools/src/cutting.rs` table and
  formulas, reimplemented in `src/common.py`. They use the **low end** of each window,
  which is at or below CamCraft's own suggestion (`app/src/cutting.rs` `compute` uses
  the midpoint). rpm is **capped at 10 000** (Tormach 770MX/1100MX spindle max), so
  small tools sit at the cap and their feed is computed at the capped rpm. No vendor
  feeds/speeds chart was used. Details and engagement rules are in
  `FEEDS-AND-SPEEDS.md`.
- **Base files** carry the aluminium row (`material_group` `aluminium_6061`), because
  the format requires rpm > 0 and feed > 0 and has no "blank".
- **Variant names** append ` - aluminum`, ` - mild steel`, … to the base name.
- **Part numbers** go in the tool name, since `ToolDto` has no part-number or comment
  field.

## Lake Shore Carbide (`lakeshore-carbide.camtools`)

- Pages: {{LSC_CATS}} category pages and 1 488 product pages crawled.
  {{LSC_OPT_PAGES}} more "option" pages each sell several sizes or radii through a
  drop-down, with no part number. They were expanded into their {{LSC_OPT_ROWS}}
  dimension-table rows, keyed by the URL slug + row (e.g. `…cornerradius-altin#.030`).
  That gives {{LSC_PRODUCTS}} products in all, deduplicated by part number.
- Fetch stats: {{LSC_FETCH}}.
- **Tools written: {{LSC_WRITTEN}}** ({{LSC_KINDS}}).
- Dimensions come from the product page's spec table. Where a page has none, they come
  from the dimension list in its title or description, e.g. `3/16 DIA., .030 CORNER
  RADIUS, 7/32 LOC, 3/16 SHANK, 2.0 OAL`. Only those numbers are read.
- **Unmapped: {{LSC_NUNMAPPED}}**

{{LSC_UNMAPPED}}

## Almar Tools (`almar-inch.camtools`)

- Pages: the public `product-sitemap.xml` lists {{ALMAR_PRODUCTS}} products, which
  matches the store's own model counts. Fetch stats: `{{ALMAR_FETCH}}`.
- **Tools written: {{ALMAR_WRITTEN}}** ({{ALMAR_KINDS}}).
- **No metric line on the HTML pages.** Every product page and every store filter value
  is inch. A metric range may exist only in the PDF catalog, which is not an HTML product
  page and was not opened. So `almar-metric.camtools` is **not written**; a human should
  decide whether a metric line exists and where it is published.
- Almar's own part code (e.g. `4VX01250500A000`) is in the name, in brackets, after the
  SKU.
- **Unmapped: {{ALMAR_NUNMAPPED}}**

{{ALMAR_UNMAPPED}}

## Tormach mill tools (`tormach.camtools`)

- Pages: Tormach's category pages list only kits and featured items, so SKUs were
  enumerated from the public sitemap (1 928 URLs), filtered by URL slug to
  {{TOR_pages}} candidate pages and fetched. Of those:
  - {{TOR_non_cutting_skipped}} were not cutting tools (machine parts, accessories);
  - {{TOR_category_pages}} were category or listing pages;
  - {{TOR_lathe_pages_routed}} were lathe tooling, handled in `tormach-lathe` below;
  - **{{TOR_products}} were mill cutting-tool products.**
- Fetch stats: `{{TOR_FETCH}}`. The first slug filter missed nothing in a manual sample of the
  excluded URLs (machine parts, holders, workholding).
- **Tools written: {{TOR_WRITTEN}}** ({{TOR_KINDS}}). Most are YG-1 jobber drills
  that Tormach sells. Their dimensions come from the product title (`D x flute x OAL`);
  shank = D for a straight-shank jobber.
- Holders were not taken from the site: CamCraft has BT30/ER and TTS built in.
- **Unmapped: {{TOR_NUNMAPPED}}**

{{TOR_UNMAPPED}}

### Tormach with holders (`tormach-bt30.camtools`, `tormach-tts.camtools`)

**A `.camtools` file cannot carry a holder profile.** The reader is
`app/src/tool_library.rs:109`, which calls `project::tool_from_json`, which calls
`ToolDto::to_tool` (`app/src/project/file.rs:462`). `ToolDto::to_tool` builds a `Tool`,
and `Tool` (`tools/src/tools.rs:137`) has no body. A tool's drawn holder (`body`,
`tool_body_wire`) is therefore dropped on import, and export writes `body: None`
(`file.rs:456`). No format was invented. Each tool instead carries CamCraft's
`holder_d`/`holder_len` **cylinder** as a conservative envelope of the built-in entry
(`crates/tools/src/holder_library.rs`, `holder_library_tts.rs`): its largest drawn
diameter (flange or collar, ER nut, or Weldon body + clamp-screw allowance) over its
whole gauge length.

- BT30 (770MX/1100MX/1500MX):
  - `BT30 ER16` for shanks ≤ 10 mm and `BT30 ER20` for shanks ≤ 13 mm, each Ø46
    (flange) × 60;
  - a `BT30 Weldon` bore on an exact bore match;
  - otherwise `BT30 ER25`/`ER32`.
- TTS (R8 770M/1100M/PCNC):
  - `TTS ER16` for shanks ≤ 10 mm (Ø38.1 × 49) and `TTS ER20` for shanks ≤ 13 mm
    (Ø38.1 × 52);
  - TTS set-screw bores (Ø40.1 × 60) on an exact match.
- **Stick-out default:** flute length + 5 mm, capped at OAL. `shank_len` is set to
  stick-out − LOC so the cylinder starts at the holder nose. **This is a default to
  measure**, not a fact.
- The holder's name is in each tool name (`[BT30 ER20]`), so the real drawn profile can
  be landed from the tool editor's holder picker. MCP has no tool for that (see gaps).
- The cylinder over-reports below the flange (an ER20 nut is Ø35 under a Ø46 flange),
  which can only block a post, never pass a rub.

{{HOLDERS}}

## Tormach lathe (`tormach-lathe.camtools`)

- Pages (from the same Tormach crawl):
  - {{LATHE_holders}} turning/facing/profile holders, {{LATHE_boring_bars}} boring
    bars, {{LATHE_grooving_holders}} grooving holders and
    {{LATHE_threading_holders}} threading holders;
  - {{LATHE_inserts}} turning inserts, {{LATHE_thread_inserts}} threading inserts and
    {{LATHE_groove_inserts}} grooving inserts.
- **Tools written: {{LATHE_WRITTEN}}** ({{LATHE_KINDS}}). A CamCraft lathe tool is one
  holder *with* its insert, so each holder page is paired with every Tormach insert page
  that fits its pocket. A pair matches when the shape letter, clearance letter and IC
  size digit agree; the pages print these codes (ANSI B212.4 / ISO 1832 insert code,
  ANSI / ISO 5608 holder code).
- **Model,** as the shipped `assets/tools/catalog.json` lathe tools do it:
  - `diameter` = shank or bar size;
  - `nose_radius` = the insert page's corner radius, or IC/2 for a round insert;
  - Groove `width` = the GTN insert page's thickness;
  - Thread `width` = 0.866 × the largest pitch in the insert's partial-profile range
    (A: 16 TPI, AG: 8 TPI), `tip_angle` 60;
  - `flute_len` = the insert IC (a default exposed length);
  - `shank_len` = tool length − IC.
- **Grooving holders:** the pages publish no tool length, so no shank band is claimed
  (`shank_len` 0) and the groove depth defaults to 2 × width.
- **Orientation** (LinuxCNC 1–9, `crates/tools/src/orientation.rs`). This is
  **assumed** to be how a PathPilot user mounts the tools on the 8L/15L tool post;
  check it per setup. The code is in each tool name.

  | Tool | Code |
  |---|---|
  | RH OD | 2 |
  | LH OD | 1 |
  | Neutral (points −X) | 6 |
  | RH boring bar | 3 |
  | LH boring bar | 4 |
  | Grooving blade (the −Z corner, CamCraft's default) | 2 |

  Threading inserts carry none (the field is inert on that kind).
- **The model is the nose circle only.** CamCraft's turning kind has no insert shape,
  approach angle or holder-body field, so a 35° VNMG and an 80° CNMG with the same nose
  radius write the same tool. The real flank clearance is not judged (see gaps).
- **Feeds:** rpm 500 and feed 25 mm/min on every lathe tool, as a placeholder. Turning
  starting values are in `FEEDS-AND-SPEEDS.md` → *Turning*. No per-material lathe
  variants are written: a turning rpm depends on the work diameter.
- Quick-change tool-post holders (8L / 15L) were not crawled. The slug filter drops
  toolholding, and they hold no cutting edge.
- One Tormach page is inconsistent: the 16ILAG60 page's "Designation" field reads
  `16IRAG60 (16NLAG60)`. The code in the product name was used.
- **Unmapped: {{LATHE_NUNMAPPED}}**

{{LATHE_UNMAPPED}}

## Generic drills (`drills-inch*.camtools`, `drills-metric*.camtools`)

- **Sources:**
  - inch series: ANSI/ASME B94.11M, with fractional 1/64–1/2 by 64ths, number drills
    #80–#1 and letter drills A–Z;
  - metric: the ISO 235 jobber series, 1.0–3.0 mm by 0.1 mm, then 0.5 mm steps to
    13.0 mm, plus tap-drill sizes 3.3, 4.2, 6.8, 8.8 and 10.2 mm.
- **Files:** {{DRILL_FILES}}.
- **Geometry:** shank = D, 2 flutes, centre cutting; 118° for HSS, 135° for carbide.
  Names carry both labels, e.g. `#7 (0.2010") jobber drill 118° HSS …`.
- **Inch jobber lengths:** {{DRILL_SRC}}.
  - The B94.11M fractional anchors (flute/OAL at each 64th) were checked against every
    Tormach jobber page that shows a fractional size, and all match.
  - Number and letter sizes between anchors don't follow a rule I can derive (e.g. X
    takes the 25/64 lengths but Y takes 13/32's). So each uses the length a public
    Tormach page states where one exists, and otherwise the **shorter** neighbouring
    anchor. Under-claiming flute reach is the safe side. **A human with the B94.11M table
    should confirm those sizes.**
- **Metric:** ISO 235 ranges; 8.6, 9.8, 11.2 and 11.7 mm match Tormach's pages exactly.
  **One disagreement:** for 1.1 mm, ISO 235 gives 14/36 (range 1.06–1.18), but
  Tormach/YG-1's page says 12 × 34. The library keeps the standard.
- **Carbide drills** in jobber length are uncommon (carbide is usually stub or screw
  machine). The carbide variant was written as asked, with jobber lengths.

## Spot-check (by hand)

Sampled per vendor and stratified by kind. Each tool's page dimensions were re-read from
the cached HTML (title, part number and spec fields only) and compared by eye with the
written numbers converted back to inches.

{{SPOT_RESULT}}

{{SPOTCHECK}}

## Decisions a human should make

{{DECISIONS}}

## CamCraft gaps (to file)

{{GAPS}}
'''

DECISIONS = r'''1. **Almar metric line.** None exists on the HTML store. Is there one (PDF catalog only?),
   and may it be used?
2. **Partial-profile threading inserts.** `width` is set from the *largest* pitch in the
   insert's range (0.866 × P). Should a thread tool instead be written per pitch you
   actually cut?
3. **Lathe orientation codes** (2/1/6/3/4, and 2 for grooving blades) assume a
   front-tool-post PathPilot mounting. Check them for your 8L/15L/mill-turn setup.
4. **Lathe defaults:**
   - `flute_len` = insert IC on turning and boring tools;
   - groove depth = 2 × width;
   - grooving holders have no shank band (tool length not published).
   Measure and adjust.
5. **Stick-out in the BT30/TTS variants:** LOC + 5 mm. Measure your real gauge
   lengths.
6. **Inch number/letter jobber lengths** that use the shorter-neighbour rule. Confirm
   them against the B94.11M table. The **1.1 mm metric jobber** disagreement (ISO 235
   14/36 vs Tormach page 12/34) also needs a look.
7. **Flute count not published:** {{FLUTELESS}} LSC tools have `flutes` unset: the
   option-page carbide drills (twist drills, almost surely 2), roughers and pre-ream
   end mills. Their `flutes` stay unset, so CamCraft's suggestion refuses them and the
   variants feed them at z = 1. Add the count if you know it.
8. **Shank not published:**
   - Almar's Ball Nosed AM-2300 and its point chamfers (shank written = cutting
     diameter);
   - LSC drills, spot drills and drill mills, and end mills ≥ 1/4" (same rule; each is
     flagged in `reports/lsc.json` notes, {{N:lsc:shank not published}} tools).
   Confirm or measure them.
9. **LSC corner-radius ranges** (".005-.007 corner radius" on the variable-flute
   aluminium line) are written at the range's low end as a bull nose
   ({{N:lsc:range}} tools).
10. **LSC necked/long-reach tools** are written with the shank drawn from the top of the
   flutes, a bigger and conservative envelope ({{N:lsc:necked}} tools). CamCraft has no
   neck field (see gaps).
11. **Drill mills** (LSC, Tormach) are written as CamCraft `taper` (cone + land), so
    they work in chamfer ops. If you use them as spot drills in drilling cycles, the
    `drill` kind may suit better.
12. **Flat-tip chamfers and V-engravers** (stated tip diameter or point radius) are
    unmapped, not written as sharp cones. Writing them sharp would put the modelled tip
    below the real one.
13. **Almar AM-3239-REV-2** is listed as "Ball Nosed" with Radius "SQ.", a contradiction
    on the page. It was left out.
14. **Carbide jobber drills** were written as asked, but true carbide drills are mostly
    stub or screw-machine length. Check before trusting the reach.
'''
GAPS = r'''Facts are from upstream main `4c3f7565`. Counts come from these libraries.
Anything marked *guess* is a guess.

1. **`.camtools` cannot carry a tool's holder body / drawn holder profile**
   - Missing: `parse_tool_library` (`crates/app/src/tool_library.rs:109`) calls
     `project::tool_from_json`, which calls `ToolDto::to_tool`
     (`crates/app/src/project/file.rs:462`). That returns a `Tool`, which has no body
     field (`crates/tools/src/tools.rs:137`). Export writes `body: None`
     (`file.rs:456`). A library tool can only carry the `holder_d`/`holder_len`
     cylinder.
   - Examples: all 107 tools in each of `tormach-bt30.camtools` and
     `tormach-tts.camtools` carry an envelope cylinder (Ø46 × 60 for BT30) instead of
     the built-in drawn BT30/TTS profile. It over-reports, e.g. an ER20 nut Ø35 under
     a Ø46 flange.
   - Suggested: P2, effort:high (collision/holder judgement), area:tools,
     area:project-file.

2. **No MCP tool to land a built-in holder (`holder_library`) on a tool**
   - Missing: nothing under `crates/app/src/mcp/` lists or lands a
     `holder_library::find(...)` entry. The only holder reference is the `holder_hit`
     warning in `mcp/job.rs:179`.
   - Examples: the 214 BT30/TTS tools above can't get their real holder headlessly.
   - Suggested: P1 (MCP rule in AGENTS.md), effort:medium, area:mcp.

3. **A tool holds one work material's rpm/feed**
   - Missing: `Tool` has a single `material_group`/`rpm`/`feed`
     (`crates/tools/src/tools.rs:175-179`). Per-material cutting data needs a separate
     library file per material.
   - Examples: this build wrote 5 variant files × 7 base libraries = 35 extra files
     (e.g. `tormach-stainless.camtools`).
   - The `tool_material` + `flutes` suggestion (`app/src/cutting.rs`) covers the
     interactive case, so this is P2, effort:high (feeds reach the posted program),
     area:tools.

4. **Turning has no surface-speed / feed-per-rev model or cutting rows**
   - Missing: `cutting.rs` `TABLE` has milling windows only, and `tabulated()`
     (`crates/app/src/cutting.rs:41`) excludes every lathe kind. A lathe tool's
     `rpm`/`feed` are a fixed spindle rpm and mm/min.
   - Examples: all 78 tools in `tormach-lathe.camtools` carry a placeholder (rpm 500,
     25 mm/min). The real starting values are in a doc table instead.
   - Suggested: P1 for mill-turn users, effort:high (posted S/F words), area:lathe,
     area:tools.

5. **Turning insert model is the nose circle only (no insert shape, approach angle,
   sharp nose)**
   - Missing: the `Turning` kind reads only `nose_radius`, and `is_sane` demands
     `nose_radius > 0` (`crates/tools/src/tools.rs:268`).
   - Examples:
     - {{C:lathe:sharp}} sharp-nose DCMT 2(1.5)0 pairs were refused;
     - 52 turning tools collapse shape and approach angle, e.g. VNMG 35° vs CNMG 80°,
       and MVJNL 93° vs MVVNN 72.5° neutral;
     - flank clearance is not judged (*guess*: back-turning and profiling a
       shoulder could rub unseen).
   - Suggested: P2, effort:max (geometry + collision), area:lathe.

6. **Threading insert = one V width; no pitch range / partial-profile model**
   - Missing: `Thread` takes one `width` + `tip_angle` (`crates/tools/src/tools.rs`,
     the Thread arm of `is_sane`).
   - Examples: 6 Tormach threading tools (16ERAG60 covers 48–8 TPI) are written at the
     largest pitch's width.
   - Suggested: P2, effort:high, area:lathe.

7. **No thread-mill kind**
   - Missing: `ToolKind` (`crates/tools/src/tools.rs:23`) has `Tap` and the lathe
     `Thread` insert, but no single- or multi-form thread mill.
   - Examples: {{C:lsc:thread mill}} LSC thread mills and {{C:tormach:thread mill}}
     Tormach single-form thread mills (#8–1/2 in) are unmapped.
   - Suggested: P1 (thread milling is a common job on these mills), effort:max (new
     kind + helical op + sim), area:tools, area:toolpath.

8. **Chamfer/taper kind is a sharp cone only (no tip diameter / tip radius; no tapered
   flank above a tip)**
   - Missing: `Taper` is "a cone widening upward from its virtual sharp tip"
     (`crates/tools/src/tools.rs`, Taper doc; `is_sane` `:305`).
   - Examples:
     - Almar {{C:almar:flat tip}} flat-tip chamfers (0.06" tip);
     - LSC {{C:lsc:flat tip}} chamfer tools with a tip diameter;
     - Tormach {{C:tormach:V-engraver}} V-engravers (.010" point radius);
     - LSC {{C:lsc:tapered-wall}} tapered-wall cutters and engravers (ball/flat tip +
       taper);
     - LSC {{C:lsc:countersink}} countersinks and combined center drills (tip
       diameter, no sharp cone).
   - Suggested: P2, effort:max (geometry), area:tools.

9. **Undercut / form cutters have no kind**
   - Missing: no lollipop, back-chamfer, dovetail, corner-rounding (concave),
     slitting saw, keyseat or rotary broach in `ToolKind` (`tools.rs:23`). The spun
     cutter outline (`cutter`, #93) is display-only: "nothing a generator or law reads
     changes" (`project/file.rs`, `ToolDto::cutter` doc).
   - Examples:
     - LSC: {{C:lsc:back-chamfer}} back-chamfer tools, {{C:lsc:corner-rounding}}
       corner rounders, {{C:lsc:broach}} hex broaches, {{C:lsc:form cutter}} form
       cutters, {{C:lsc:double-angle}} double-angle cutter,
       {{C:lsc:corner-chamfered}} corner-chamfered end mills, {{C:lsc:high-feed}}
       high-feed mills, {{C:lsc:carbide bur}} carbide burs;
     - Almar: {{C:almar:lollipop}} lollipop cutters;
     - Tormach: {{C:tormach:slitting saw}} slitting saws.
   - Suggested: P2, effort:max, area:tools.

10. **No necked / reduced-neck (LOC vs reach) field**
    - Missing: the stack is flute → shank → holder (`ToolGeom`,
      `crates/tools/src/tools.rs`). There is no neck diameter or reach length.
    - Examples: {{N:lsc:necked}} LSC long-reach/necked tools are written with a
      full-diameter shank from the top of the flutes. It is conservative but blocks
      legal deep cuts.
    - Suggested: P2, effort:high (shank-reach law), area:tools.

11. **No reamer, spot-drill, countersink or combined center-drill kinds; drills not in
    the cutting table**
    - Missing: `ToolKind` has `Drill` only, and `tabulated()` (`app/src/cutting.rs:41`)
      excludes `Drill`, so CamCraft suggests no feeds for any drill.
    - Examples:
      - LSC: {{C:lsc:reamer}} chucking reamers (sizes and lengths published, but no
        reamer kind);
      - the 368 drills in `drills-{inch,metric}-{hss,carbide}.camtools`, plus the
     LSC and Tormach drills, get no suggestion (this build used a
        one-lip fz reading instead);
      - spot drills are written as `drill` (exact geometry, but no spot-drill
        semantics).
    - Suggested: P2, effort:high, area:tools.

12. **No part number / vendor / coating / helix / notes on a tool**
    - Missing: `ToolDto` (`crates/app/src/project/file.rs:292`) has no free-text or
      vendor fields.
    - Examples: every one of the libraries' tools carries part number, coating and
      corner-radius text inside its name, e.g. `LSC LC206014X 1/4" 4FL flat Altin LOC
      3/4 OAL 2-1/2`.
    - Suggested: P2, effort:medium (additive DTO field, no geometry), area:tools,
      area:project-file.

13. **Library import cannot merge/replace by part number**
    - Missing: `ImportTools` (`crates/app/src/commands/tool_import.rs:81-86`) skips an
      identical tool and **renames** a same-named different one (`A (2)`). There is no
      replace or update mode and no key but the name.
    - Examples: re-importing an updated `tormach.camtools` after a feeds change would
      add 107 renamed duplicates (*guess* at the exact count; the code path is as
      read).
    - Suggested: P2, effort:medium, area:tools, area:mcp.

14. **Taps without published lengths can't be built** (not a CamCraft gap, listed to
    reject it)
    - The `Tap` kind exists. The vendor pages ({{C:tormach:tap}} Tormach,
      {{C:lsc:tap:}} LSC) give no thread length or OAL. **Rejected** as a CamCraft gap.
'''
