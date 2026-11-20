"""Map Tormach cutting-tool product pages to CamCraft tools.

Run: python3 -I map_tormach.py   (reads ../cache/tormach-products.json)
Writes ../tormach.camtools and ../reports/tormach.json.

Only pages Tormach files under cutting tools (page title / breadcrumb) are
products; the rest of the slug-filtered sitemap pages (machine parts,
holders, accessories) are counted as skipped. Holders are CamCraft's
built-in libraries (BT30/ER, TTS) and are not taken from these pages.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import INCH, fmt_in, frac, sane, tool, write_library  # noqa: E402
from drill_sizes import gauge_to_inch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def L(v):
    """'1/8 in.' / '2-1/2 in.' / '16 mm' -> mm."""
    if not v:
        return None
    s = v.replace("in.", "").replace("in", "").replace('"', "").strip()
    if "mm" in s:
        x = frac(s.replace("mm", ""))
        return x
    x = frac(s)
    return None if x is None else round(x * INCH, 6)


def mat(a):
    m = (a.get("Material") or "").upper()
    return "hss" if ("HSS" in m or "COBALT" in m or "HIGH SPEED" in m) else "carbide" if "CARBIDE" in m else None


def zf(a):
    m = re.match(r"\d+", a.get("Flutes") or "")
    return int(m.group(0)) if m else None


UNMAPPED = [
    (r"(?i)precision cutter|toroidal|indexable|modular|face mill|fly cutter|shear hog|superfly|high feed", "indexable/insert cutter: no supported insert-cutter model"),
    (r"(?i)\bset\b|\bkit\b|piece|starter", "multi-tool set/kit: map the single-tool pages instead"),
    (r"(?i)insert|screw|shim", "insert/spare part, or an insert tool with no supported model"),
    (r"(?i)turning|facing|boring bar|grooving|parting|threading tool|profile tool|chamfer tool:|cut-off|tool holder", "lathe tool holder: CamCraft lathe tools need insert/nose data the page does not give as one tool"),
    (r"(?i)\btap\b", "tap: no thread length / OAL on the page"),
    (r"(?i)thread mill", "thread mill: no CamCraft thread-mill kind"),
    (r"(?i)slitting saw", "slitting saw: no CamCraft kind"),
    (r"(?i)drag|engraver|haimer|tip for", "engraver/drag knife/probe part: not a CamCraft mill kind"),
    (r"(?i)gauge|chart|router bit", "not a single metal-cutting tool"),
]


def map_one(p):
    a = p["attrs"]
    nm = p["name"]
    pn = p["pn"] or "?"
    coat = (a.get("Coating") or "").replace("TIALN", "TiAlN").replace("TIN", "TiN")
    notes = []
    if a.get("End Style") == "V":
        return None, f"V-engraver with a {a.get('Point Radius', '?')} point radius; CamCraft's chamfer mill is a cone from a sharp tip"
    if "Cutting Diameter" in a and ("Flute Length" in a) and ("Total Length" in a or "Overall Length" in a):
        d, loc = L(a["Cutting Diameter"]), L(a["Flute Length"])
        oal = L(a.get("Total Length") or a.get("Overall Length"))
        sh = L(a.get("Shank Size"))
        if None in (d, loc, oal, sh):
            return None, "a dimension did not parse"
        z, tm = zf(a), mat(a) or "carbide"
        es = a.get("End Style") or ""
        if "Point Angle" in a:
            ang = float(re.match(r"[\d.]+", a["Point Angle"]).group(0))
            t = tool("taper", d, loc, sh, oal, z, tip_angle=ang, tool_mat=tm)
            k = f"{ang:g}deg drill mill"
            notes.append("drill mill written as CamCraft taper (cone + straight land)")
        elif re.search(r"(?i)ball", es + nm):
            t = tool("ball_nose", d, loc, sh, oal, z, corner_r=d / 2, tool_mat=tm)
            k = "ball"
        elif "Radius" in es:
            cr = L(re.search(r"[\d.]+", es).group(0))
            t = tool("bull_nose", d, loc, sh, oal, z, corner_r=cr, tool_mat=tm)
            k = f"CR {fmt_in(cr / INCH)}"
        elif es in ("Single", "Square", "Double", ""):
            t = tool("end_mill", d, loc, sh, oal, z, tool_mat=tm)
            k = "flat" + (" DE" if es == "Double" else "")
            if es == "Double":
                notes.append("double-ended: flute length is one end; the other end is modelled as shank")
        else:
            return None, f"end style '{es}' not a CamCraft kind"
        name = f'Tormach {pn} {fmt_in(d / INCH)}" {str(z) + "FL " if z else ""}{k} {coat} LOC {fmt_in(loc / INCH)} OAL {fmt_in(oal / INCH)}'
    elif "Point Angle" in a and re.search(r" x ", nm):
        m = re.match(r"\s*(?:\d+ Pk\.-\s*)?(.+?)\s*x\s*(.+?)\s*x\s*([^x]+?)\s*(?:\d+-Pack|Drills|$)", nm)
        if not m:
            return None, "drill size text did not parse"
        D, Lf, O = m.groups()
        metric = "mm" in D
        if metric:
            d = frac(D.replace("mm", "").strip())
            label = f"{d:g}mm"
        else:
            di = gauge_to_inch(D.replace("in.", "").strip())
            if di is None:
                return None, f"drill size '{D}' unknown"
            d = round(di * INCH, 6)
            lab = D.replace("in.", "").strip()
            label = f'{lab} ({di:.4f}")' if (lab.startswith("#") or lab.isalpha()) else f'{lab}"'
        loc, oal = L(Lf), L(O)
        ang_m = re.match(r"[\d.]+", a["Point Angle"])
        if None in (d, loc, oal) or not ang_m or ";" in a["Point Angle"]:
            return None, "drill dimension or single point angle missing"
        ang = float(ang_m.group(0))
        tm = mat(a) or "hss"
        t = tool("drill", d, loc, d, oal, 2, tip_angle=ang, tool_mat=tm)
        notes.append("straight-shank jobber: shank = drill diameter; 2 flutes (twist drill)")
        style = (a.get("Style") or "jobber").lower()
        name = f"Tormach {pn} {label} {style} drill {ang:g}deg {(a.get('Material') or '').replace('5% COBALT HSS', 'HSS-Co5')} {coat}"
    else:
        for pat, why in UNMAPPED:
            if re.search(pat, nm + " " + p["head"]):
                return None, why
        return None, "no tool dimensions on the page"
    name = " ".join(name.split())
    if not sane(t):
        return None, f"fails sanity: {t}"
    return (name, t, notes), None


def is_cutting(p):
    return "error" not in p and (p["page_title"].startswith("Tormach Cutting") or "Cutting" in p["crumb"]
                                 or "cutting tools" in p["page_title"].lower()
                                 or bool(re.search(r"(?i)drill|end mill|tap\b|thread mill|insert|saw|engraver", p["name"]))
                                 or any(k in p["attrs"] for k in ("Point Angle", "Cutting Diameter", "Flute Length")))


def main():
    data = json.load(open(os.path.join(ROOT, "cache", "tormach-products.json")))
    entries, unmapped, kinds, notes, skipped = [], [], {}, [], 0
    lathe_src = set()
    lp = os.path.join(ROOT, "reports", "tormach-lathe.json")
    if os.path.exists(lp):
        for v in json.load(open(lp))["source"].values():
            lathe_src.update(v)
        lathe_src.update(u["url"] for u in json.load(open(lp))["unmapped"])
    categories = 0
    for p in data["products"]:
        if not is_cutting(p):
            skipped += 1
            continue
        if not p["pn"]:
            categories += 1  # a category/listing page, not a product
            continue
        if p["url"] in lathe_src:
            continue  # lathe tooling: reported in tormach-lathe
        res, why = map_one(p)
        if why:
            unmapped.append({"url": p["url"], "pn": p["pn"], "name": p["name"], "reason": why})
            continue
        name, t, n = res
        entries.append((name, t, p["url"]))
        kinds[t["kind"]] = kinds.get(t["kind"], 0) + 1
        if n:
            notes.append({"name": name, "notes": n})
    n = write_library(os.path.join(ROOT, "tormach.camtools"), [(a, b) for a, b, _ in entries])
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    json.dump({"pages": len(data["products"]), "non_cutting_skipped": skipped, "category_pages": categories,
               "lathe_pages_routed": len(data["products"]) - skipped - categories - n - len(unmapped),
               "products": n + len(unmapped), "written": n, "kinds": kinds,
               "unmapped": unmapped, "notes": notes, "fetch_stats": data["stats"],
               "source": {a: c for a, _, c in entries}},
              open(os.path.join(ROOT, "reports", "tormach.json"), "w"), indent=1)
    print("tormach:", len(data["products"]) - skipped, "cutting-tool pages,", n, "written", kinds,
          len(unmapped), "unmapped;", skipped, "non-cutting pages skipped")


if __name__ == "__main__":
    main()
