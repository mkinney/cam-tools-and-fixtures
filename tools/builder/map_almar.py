"""Map Almar Tools products to CamCraft tools.

Run: python3 -I map_almar.py   (reads ../cache/almar-products.json)
Writes ../almar-inch.camtools and ../reports/almar.json.
Almar's public HTML store lists only inch products; no metric line is
published as HTML pages (see REPORT.md), so no almar-metric file is made.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import fmt_in, frac, mm, sane, tool, write_library  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def map_one(p):
    a = p["attrs"]
    model = a.get("Model", "")
    sku = p["sku"]
    code = a.get("Description", "")
    d_in = frac(a.get("Diameter"))
    oal_in = frac(a.get("Overall Length"))
    loc_in = frac(a.get("Length of Cut"))
    shank_in = frac(a.get("Shank"))
    z = int(a["Number of Flutes"]) if a.get("Number of Flutes", "").isdigit() else None
    coat = a.get("Coating", "")
    coat = "" if coat in ("N/A", "") else coat
    notes = []
    if d_in is None or oal_in is None:
        return None, "diameter or overall length not published"
    pre = f"Almar {sku}" + (f" ({code})" if code else "")
    if model.startswith("Endurance") and "Chamfer" not in model or model.startswith("Aluminex"):
        if loc_in is None or shank_in is None:
            return None, "length of cut or shank not published"
        r = a.get("Radius", "")
        if r == "SQ.":
            kind, cr, kn = "end_mill", 0.0, "flat"
        else:
            rv = frac(r)
            if rv is None or rv <= 0:
                return None, f"corner radius '{r}' not a size"
            kind, cr, kn = "bull_nose", rv, f"CR {fmt_in(rv)}"
        t = tool(kind, mm(d_in), mm(loc_in), mm(shank_in), mm(oal_in), z, corner_r=mm(cr) if cr else 0.0)
        name = f'{pre} {fmt_in(d_in)}" {z}FL {kn} {coat} LOC {fmt_in(loc_in)} OAL {fmt_in(oal_in)}'
    elif model == "Ball Nosed":
        if a.get("Radius") == "SQ.":
            return None, "page lists model 'Ball Nosed' but Radius 'SQ.' (contradictory)"
        if loc_in is None:
            return None, "length of cut not published"
        shank = shank_in if shank_in else d_in
        if not shank_in:
            notes.append("shank not published; shank = cutting diameter")
        t = tool("ball_nose", mm(d_in), mm(loc_in), mm(shank), mm(oal_in), z, corner_r=mm(d_in) / 2)
        name = f'{pre} {fmt_in(d_in)}" {z}FL ball LOC {fmt_in(loc_in)} OAL {fmt_in(oal_in)}'
    elif model == "Endurance Chamfers":
        ang = frac(a.get("Degrees", "").replace("°", ""))
        tipd = a.get("Tip Dia.", "")
        if tipd != "Point":
            return None, f"flat tip ({tipd}\" tip dia.); CamCraft's chamfer mill is a cone from a sharp tip"
        if not ang:
            return None, "angle not published"
        # Sharp cone: its flute height is set by the diameter and the
        # included angle exactly: h = (D/2) / tan(A/2).
        h = (d_in / 2) / math.tan(math.radians(ang / 2))
        notes.append("cone height derived from diameter + included angle; shank = body diameter")
        de = a.get("Single or Double End", "")
        t = tool("taper", mm(d_in), mm(h), mm(d_in), mm(oal_in), z, tip_angle=ang)
        name = f'{pre} {fmt_in(d_in)}" {z}FL {ang:g}deg chamfer {coat} {"DE " if de.startswith("Double") else ""}OAL {fmt_in(oal_in)}'
    elif model == "Spherical End Mill":
        return None, "lollipop (270 deg spherical) cutter: no CamCraft kind (a ball nose has no undercut neck)"
    else:
        return None, f"unknown model '{model}'"
    name = " ".join(name.split())
    if not sane(t):
        return None, f"fails sanity: {t}"
    return (name, t, notes), None


def main():
    data = json.load(open(os.path.join(ROOT, "cache", "almar-products.json")))
    entries, unmapped, kinds, notes = [], [], {}, []
    for p in data["products"]:
        res, why = map_one(p)
        if why:
            unmapped.append({"url": p["url"], "sku": p["sku"], "model": p["attrs"].get("Model"), "reason": why})
            continue
        name, t, n = res
        entries.append((name, t))
        kinds[t["kind"]] = kinds.get(t["kind"], 0) + 1
        if n:
            notes.append({"name": name, "notes": n})
    n = write_library(os.path.join(ROOT, "almar-inch.camtools"), entries)
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    json.dump({"products": len(data["products"]), "written": n, "kinds": kinds, "unmapped": unmapped,
               "notes": notes, "fetch_stats": data["stats"],
               "source": {p["sku"]: p["url"] for p in data["products"]}},
              open(os.path.join(ROOT, "reports", "almar.json"), "w"), indent=1)
    print("almar:", len(data["products"]), "products,", n, "written", kinds, len(unmapped), "unmapped")


if __name__ == "__main__":
    main()
