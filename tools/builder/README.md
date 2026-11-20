# Tool-library builder: how to re-run

Everything here is a local, personal-use side project. Sources are the vendors'
public HTML product pages only. No vendor CAM library file (Fusion `.json`/`.tools`,
`.hsmlib`, Vectric, CSV, …) is ever downloaded or read, per the clean-room rule of
CamCraft #300.

Layout:

- `src/` holds these scripts.
- `cache/` holds the fetched HTML (one directory per host) and the crawl JSON. It is
  kept apart from the scripts.
- `reports/` holds per-step JSON.
- The libraries go in the parent directory.

Run every script with `python3 -I` (isolated mode), from `src/`.

## 1. Crawl (polite: robots.txt obeyed, <= 1 request/s, cached)

```
python3 -I crawl_lsc.py        # Lake Shore Carbide: category -> product pages (slow site; ~1 h)
python3 -I crawl_almar.py      # Almar: product-sitemap.xml -> product pages
# Tormach: the category pages list only kits, so SKUs come from the public sitemap,
# pre-filtered by URL slug into cache/tormach-candidates.txt:
python3 -I fetch.py https://tormach.com/sitemaps/us_sitemap.xml   # then the grep below
python3 -I crawl_tormach.py
```

The Tormach slug filter that made `cache/tormach-candidates.txt`:

```
grep -o '<loc>[^<]*' <sitemap cache file> | sed 's/<loc>//' > cache/tormach-urls.txt
grep "\.html$" cache/tormach-urls.txt \
 | grep -iE "mill|drill|tap-|taps|reamer|chamfer|cutter|countersink|thread|boring|spot|engrav|saw|bit|router|burr|insert|tool|end-|ball|radius|carbide|hss|cobalt|v-bit|deburr|graver|counterbore|keyseat|dovetail|fly" \
 | grep -viE "holder|collet|vise|chuck|arbor|fixture|ball-screw|spindle|motor|bearing|cover|plate|stand|cabinet|enclosure|tts-|probe|lamp|coolant|bundle|pcnc|(1100|770|440|1500)(m|mx|-mill|-series|l)|warranty|upgrade|kit-for|wrench|rack|tray|sticker|shirt|drawbar|gang-block|tool-post|toolpost|post-size|qc-" \
 > cache/tormach-candidates.txt
```

`fetch.py` caches each page under `cache/<host>/`. A re-run reads the cache and does
not fetch again. To refresh, delete the cache files.

## 2. Map to CamCraft tools (`camcraft-tools/1`, mm)

```
python3 -I map_tormach_lathe.py  # tormach-lathe.camtools (run before map_tormach: it claims the lathe pages)
python3 -I map_tormach.py        # tormach.camtools
python3 -I map_almar.py          # almar-inch.camtools
python3 -I map_lsc.py            # lakeshore-carbide.camtools
python3 -I build_drills.py       # drills-{inch,metric}{,-hss,-carbide}.camtools
python3 -I build_holders.py      # tormach-bt30.camtools, tormach-tts.camtools
python3 -I build_variants.py lakeshore-carbide almar-inch tormach \
    drills-inch-hss drills-inch-carbide drills-metric-hss drills-metric-carbide
                                 # per-material variants + FEEDS-AND-SPEEDS.{md,csv}
```

Shared code:

- `common.py`: fraction parsing, tool dict, sanity mirror of `Tool::is_sane`,
  feeds/speeds from CamCraft's own `cutting.rs` table.
- `drill_sizes.py`: the standard drill series (B94.11M, ISO 235).

## 3. Import-check with CamCraft itself

Build `camcraft-cli` from upstream main in a private worktree with its own
`CARGO_TARGET_DIR`, then:

```
python3 -I mcp_import.py <path>/camcraft-cli ../*.camtools
```

Each file is imported through MCP `import_tool_library` in a fresh session, and
`get_job` counts the tools. On a refusal, every tool is re-imported alone to list each
refused tool with its message. Results go to `../import-results.json`.

## 4. Spot-check and report

`python3 -I spotcheck.py` writes `reports/spotcheck.md`. It puts each sampled tool's
page dimensions (title, part number and spec fields only, no prose) beside the written
numbers in inches, for checking by eye. `REPORT.md` is written from
`reports/*.json`, plus the human notes.

## 5. Report

```
python3 -I make_report.py      # REPORT.md from reports/*.json, import-results.json,
                               # reports/spotcheck.md and report_template.py
```

Note for Lake Shore Carbide: some products are one page with a size, radius or coating
drop-down and no part number. `map_lsc.py` (`option_records`) expands those pages into
one record per dimension-table row.
