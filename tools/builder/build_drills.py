"""Vendor-neutral jobber drill libraries from the public size standards.

Inch: ANSI/ASME B94.11M series - fractional 1/64-1/2 by 64ths, number
#80-#1, letter A-Z (drill_sizes.py). Jobber flute/OAL: the B94.11M
fractional anchors; a number/letter size takes the length a public
Tormach jobber-drill page states for it when one exists (the same
standard series, cross-checked: all fractional anchors on those pages
match), else the SHORTER neighbouring anchor's (conservative reach).
Metric: ISO 235 jobber series, 1.0-3.0 mm by 0.1, then 0.5 mm steps to
13.0, plus common tap-drill sizes.

Geometry: shank = diameter, 2 flutes, centre cutting; 118 deg point for
HSS, 135 deg for carbide. Feeds/speeds: common.py (CamCraft cutting.rs).
Writes ../drills-{inch,metric}{,-hss,-carbide}.camtools and
../reports/drills.json. Run: python3 -I build_drills.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import INCH, fmt_in, frac, sane, tool, write_library  # noqa: E402
from drill_sizes import LETTER, NUMBER, gauge_to_inch, jobber_inch, jobber_metric  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POINT = {"hss": 118.0, "carbide": 135.0}
TAP_DRILLS = [2.5, 3.3, 4.2, 5.0, 6.8, 8.5, 8.8, 10.2]


def tormach_lengths():
    """Inch number/letter jobber lengths stated on Tormach's public pages."""
    p = os.path.join(ROOT, "cache", "tormach-products.json")
    out = {}
    if not os.path.exists(p):
        return out
    for r in json.load(open(p))["products"]:
        a = r.get("attrs", {})
        if "Point Angle" not in a or "Jobber" != (a.get("Style") or ""):
            continue
        m = re.match(r"\s*(?:\d+ Pk\.-\s*)?(#\d+|[A-Z])\s*x\s*(.+?)\s*x\s*([^x]+?)\s*(?:\d+-Pack|Drills|$)", r["name"])
        if not m:
            continue
        l2 = frac(m.group(2).replace("in.", "").strip())
        l1 = frac(m.group(3).replace("in.", "").strip())
        if l2 and l1:
            out[m.group(1)] = (l2, l1, r["url"])
    return out


def inch_sizes(tm):
    rows = []
    for n in range(1, 33):
        d = n / 64
        l2, l1, how = jobber_inch(d)
        rows.append((f'{fmt_in(d)}" ({d:.4f}")', d, l2, l1, how))
    for k in sorted(NUMBER, reverse=True):
        d = NUMBER[k]
        lab = f"#{k}"
        if lab in tm:
            l2, l1, url = tm[lab]
            how = f"Tormach page {url}"
        else:
            l2, l1, how = jobber_inch(d)
        rows.append((f'{lab} ({d:.4f}")', d, l2, l1, how))
    for k in sorted(LETTER):
        d = LETTER[k]
        if k in tm:
            l2, l1, url = tm[k]
            how = f"Tormach page {url}"
        else:
            l2, l1, how = jobber_inch(d)
        rows.append((f'{k} ({d:.4f}")', d, l2, l1, how))
    return rows


def metric_sizes():
    ds = [round(1.0 + i / 10, 1) for i in range(21)] + [3.5 + i * 0.5 for i in range(20)]
    ds = sorted(set(ds + TAP_DRILLS))
    rows = []
    for d in ds:
        r = jobber_metric(d)
        if r:
            rows.append((f"{d:g}mm", d, r[0], r[1], "ISO 235"))
    return rows


def make(rows, inch, tm_mat):
    ents = []
    for label, d, l2, l1, _ in rows:
        dm, f, o = (d * INCH, l2 * INCH, l1 * INCH) if inch else (d, l2, l1)
        t = tool("drill", dm, f, dm, o, 2, tip_angle=POINT[tm_mat], tool_mat=tm_mat)
        ln = f'LOC {fmt_in(l2)} OAL {fmt_in(l1)}' if inch else f"LOC {l2:g} OAL {l1:g}"
        name = f"{label} jobber drill {POINT[tm_mat]:g}° {'HSS' if tm_mat == 'hss' else 'carbide'} {ln}"
        if not sane(t):
            raise SystemExit(f"insane drill {name}: {t}")
        ents.append((name, t))
    return ents


def main():
    tm = tormach_lengths()
    inch, metric = inch_sizes(tm), metric_sizes()
    rep = {"inch_sizes": len(inch), "metric_sizes": len(metric), "files": {},
           "inch_length_source": [{"size": r[0], "flute_in": r[2], "oal_in": r[3], "source": r[4]} for r in inch]}
    for unit, rows, is_inch in (("inch", inch, True), ("metric", metric, False)):
        both = []
        for m in ("hss", "carbide"):
            e = make(rows, is_inch, m)
            both += e
            rep["files"][f"drills-{unit}-{m}"] = write_library(os.path.join(ROOT, f"drills-{unit}-{m}.camtools"), e)
        rep["files"][f"drills-{unit}"] = write_library(os.path.join(ROOT, f"drills-{unit}.camtools"), both)
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    json.dump(rep, open(os.path.join(ROOT, "reports", "drills.json"), "w"), indent=1)
    print(rep["files"], "inch sizes", len(inch), "metric sizes", len(metric))
    print("inch lengths from Tormach pages:", sum(1 for r in inch if r[4].startswith("Tormach")),
          "shorter-neighbour:", sum(1 for r in inch if r[4].startswith("shorter")))


if __name__ == "__main__":
    main()
