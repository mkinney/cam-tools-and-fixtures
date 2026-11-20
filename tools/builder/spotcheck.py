"""Spot-check: for ~10 tools per vendor, put the product page's own
dimension text (re-read from the cached HTML) beside the written tool's
numbers converted back to inches. The human-readable table goes into
REPORT.md; each row was then read by eye.

Run: python3 -I spotcheck.py  -> ../reports/spotcheck.md
"""
import html
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def page_text(url):
    h = open(fetch.cache_path(url), encoding="utf-8", errors="replace").read()
    t = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", "", h)
    t = html.unescape(re.sub(r"<[^>]+>", "|", t))
    return re.sub(r"\s*\|[\s|]*", "|", t)


_OPT = {}


def option_row(part):
    """The exact table row of an LSC option page (map_lsc.option_records)."""
    if not _OPT:
        import map_lsc
        cats = json.load(open(os.path.join(ROOT, "cache", "lsc-products.json")))["categories"]
        for r in map_lsc.option_records(cats)[0]:
            _OPT[r["part"]] = r
    r = _OPT.get(part)
    return None if r is None else f"{r['title']} · row {part.split('#')[-1]} · " + "; ".join(f"{k} {v}" for k, v in r["spec"].items())


def dims_from_page(vendor, url, part=""):
    if vendor == "lsc" and "#" in part:
        row = option_row(part)
        if row:
            return row
    """Only the page's title/part number and its dimension fields - no
    descriptive prose is reproduced."""
    h = open(fetch.cache_path(url), encoding="utf-8", errors="replace").read()
    if vendor == "lsc":
        import crawl_lsc
        r = crawl_lsc.parse_product(url, h)
        dims = "; ".join(f"{k} {v}" for k, v in r["spec"].items())
        if not dims:  # dimension list in the text: keep only size tokens
            dims = " ".join(re.findall(r"[\d./-]+\s*(?:MM)?\s*\"?\s*(?:DIA\.?|DIAMETER|LOC|SHANK|SHK|OAL|CORNER RAD\w*|DEG\w*|FLUTES?|FL\b)",
                                       r["desc"].upper().replace("''", '"')))
        return f"{r['title']} · PN {r['part']} · {dims}"
    if vendor == "almar":
        import crawl_almar
        r = crawl_almar.parse(url, h)
        keep = ("Diameter", "Shank", "Length of Cut", "Overall Length", "Radius", "Number of Flutes", "Degrees", "Tip Dia.", "Model")
        return "; ".join(f"{k} {r['attrs'][k]}" for k in keep if k in r["attrs"])
    import crawl_tormach
    r = crawl_tormach.parse(url, h)
    keep = ("Cutting Diameter", "Shank Size", "Flute Length", "Total Length", "Overall Length", "End Style",
            "Flutes", "Point Angle", "Material", "Style")
    return f"{r['name']} · PN {r['pn']} · " + "; ".join(f"{k} {r['attrs'][k]}" for k in keep if k in r["attrs"])


def written(d):
    f = lambda v: f"{v / 25.4:.4f}"  # noqa: E731
    s = f"D {f(d['diameter'])} LOC {f(d['flute_len'])} Sh {f(d['shank_d'])} OAL {f(d['flute_len'] + d['shank_len'])}"
    if d["kind"] == "bull_nose":
        s += f" CR {f(d['corner_r'])}"
    if d["kind"] in ("drill", "taper"):
        s += f" A {d['tip_angle']:g}"
    return s + f" z {d.get('flutes', '-')} {d['kind']}"


def main():
    random.seed(11)
    out = ["| Vendor | Tool | Page (its own text) | Written (inch) | Check |", "|---|---|---|---|---|"]
    for vendor, lib, rep in (("lsc", "lakeshore-carbide", "lsc"), ("almar", "almar-inch", "almar"),
                             ("tormach", "tormach", "tormach")):
        p = os.path.join(ROOT, lib + ".camtools")
        if not os.path.exists(p):
            continue
        tools = json.load(open(p))["tools"]
        src = json.load(open(os.path.join(ROOT, "reports", rep + ".json")))["source"]
        if vendor == "almar":
            src = {t["name"]: src[t["name"].split()[1]] for t in tools}
        # stratify by kind so every kind shows up
        bykind = {}
        for t in tools:
            bykind.setdefault(t["definition"]["kind"], []).append(t)
        pick = []
        for k, v in bykind.items():
            pick += random.sample(v, min(len(v), 2))
        rest = [t for t in tools if t not in pick]
        pick += random.sample(rest, max(0, min(len(rest), 10 - len(pick))))
        for t in pick[:12]:
            url = src[t["name"]]
            if ".." in url:
                continue
            out.append(f"| {vendor} | {t['name']} | {dims_from_page(vendor, url, t['name'].split()[1]).replace('|', ' / ')} "
                       f"([page]({url})) | {written(t['definition'])} | |")
    open(os.path.join(ROOT, "reports", "spotcheck.md"), "w").write("\n".join(out) + "\n")
    print(len(out) - 2, "rows")


if __name__ == "__main__":
    main()
