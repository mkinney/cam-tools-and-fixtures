"""Map Lake Shore Carbide products to CamCraft tools.

Run: python3 -I map_lsc.py   (reads ../cache/lsc-products.json)
Writes ../lakeshore-carbide.camtools and ../reports/lsc.json.

Dimensions come from each product page's spec table; when a page has no
table, from the dimension list in its title/description text
("3/16 DIA., .030 CORNER RADIUS, 7/32 LOC, 3/16 SHANK, 2.0 OAL"). Only
dimensions are taken - no marketing text is copied; names are generated.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import INCH, fmt_in, frac, sane, tool, write_library  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# A number standing alone: never glued to a letter or another number
# ("H6 SHANK TOLERANCE" is a fit class, not a 6" shank).
NUM = r"(?<![A-Z0-9./])(\d+-\d+/\d+|\d+ \d+/\d+|\d+/\d+|\d*\.\d+|\d+)"

# Product types CamCraft has no exact kind for (checked in order).
UNMAPPED = [
    (r"THREAD ?MILL|THREADMILL|ACME", "thread mill: no CamCraft thread-mill kind (Thread is a lathe insert)"),
    (r"\bTAPS?\b", "tap: no thread length / OAL on the page"),
    (r"BROACH", "rotary broach: no CamCraft kind"),
    (r"BACK ?CHAMFER", "back-chamfer tool: no CamCraft kind (undercut cone above a neck)"),
    (r"CORNER ROUND", "corner-rounding (concave radius) cutter: no CamCraft kind"),
    (r"COUNTERSINK", "countersink: tip and flute length not published as a sharp cone"),
    (r"CENTER DRILL|COMBINED DRILL", "combined center drill (stepped pilot + cone): no CamCraft kind"),
    (r"\bBURR?\b|BURR\b", "carbide bur (shaped rotary file): no CamCraft kind"),
    (r"DOVETAIL|KEYSEAT|KEY SEAT|T-SLOT|SLITTING|\bSAW\b", "undercut/side cutter: no CamCraft kind"),
    (r"LOLLIPOP|SPHERICAL|UNDERCUT", "lollipop/undercut cutter: no CamCraft kind"),
    (r"DOUBLE ANGLE|DBL ANGLE", "double-angle cutter: no CamCraft kind"),
    (r"PER SIDE|TAPERED|TAPER END|TAPER MILL|FLARE TOOL", "tapered-wall cutter: CamCraft's taper is a sharp cone, not a tapered flank with a tip diameter/ball"),
    (r"HIGH FEED|HI-FEED|HIGH-FEED", "high-feed end profile: no CamCraft kind"),
    (r"CORNER CHAMFER|CHAMFER(ED)? CORNERS?|DEGREE C(OR)?NR|DEG CORNER", "corner-chamfered end mill: no CamCraft kind (not flat, ball or bull)"),
    (r"SKIMMER|REFRACTOMETER|AERATOR|OXYGENATOR|JAW|COOLANT|WAY COVER|\bGIFT\b|SHIRT|\bHAT\b", "not a cutting tool"),
    (r"INSERT|INDEXABLE", "insert tool: no supported insert-cutter model"),
    (r"ENGRAVER\b|ENGRAVING (TOOL|CUTTER|BIT)|V-?BIT", "engraver: tip geometry not a CamCraft kind"),
    (r"NOT COUNTING", "flute length stated excluding the point: the cone + land length is ambiguous"),
    (r"DEBURR", "deburring tool: no CamCraft kind"),
    (r"EXTENSION", "tool extension: not a cutting tool"),
    (r"FORM TOOL|CONVEX|CONCAVE|RADIUS PAC", "form cutter: no CamCraft kind"),
]


def length(v):
    """A dimension text -> mm. Inch by default; 'mm' marks millimetres."""
    if v is None:
        return None
    s = v.strip().upper().replace("''", '"').replace("Ø", "").strip()
    is_mm = "MM" in s
    s = s.replace("MM", "").replace('"', "").replace("IN.", "").replace("IN", "").strip()
    x = frac(s)
    if x is None:
        return None
    return round(x, 6) if is_mm else round(x * INCH, 6)


def grab(text, pat):
    m = re.search(pat, text)
    return m.group(1) + (" MM" if m and m.lastindex and m.lastindex >= 2 and m.group(2) else "") if m else None


def fields(r):
    s = {k.strip().rstrip(":").upper(): v for k, v in r["spec"].items()}
    t = (r["title"] + " | " + r["desc"]).upper().replace("''", '"')
    f = {}
    # Option-table cells: "#7 (.2010)" / "A (.2340)" / "1/32 (.0312)" carry
    # the decimal size in brackets; "1/4\" STUB" a size with a word.
    dz = s.get("DIAMETER") or s.get("LETTER") or ""
    paren = re.search(r"\((\.\d+)\)", dz)
    size = re.match(r"\s*(\d+-\d+/\d+|\d+/\d+|\d*\.\d+)", (s.get("SIZE") or "").replace('"', ""))
    f["d"] = (length(paren.group(1)) if paren else None) or \
        (length(size.group(1)) if size else None) or \
        length(s.get("DIAMETER") or s.get("CUT DIA") or s.get("CUT DIA,")) or \
        length(grab(t, NUM + r'"\s*\(\s*[\d.]+\s*\)\s*(?:DIA|DIAMETER)')) or \
        length(grab(t, NUM + r'\)?\s*(MM)?\s*"?\s*\)?\s*(?:DIA\b|DIA\.|DIAMETER|Ø)'))
    if f["d"] is None:
        f["d"] = length(grab(r["title"].upper(), r'^' + NUM + r'\s*(MM)?"'))
    f["loc"] = length(s.get("FLUTE LENGTH") or s.get("LOC") or s.get("LENGTH OF CUT")) or \
        length(grab(t, NUM + r'\s*(MM)?\s*"?\s*(?:LOC|FLUTE LENGTH)'))
    f["shank"] = length(s.get("SHANK DIAMETER") or s.get("SHANK DIA.") or s.get("SHANK")) or \
        length(grab(t, NUM + r'\s*(MM)?\s*"?\s*(?:SHANK|SHK)'))
    f["oal"] = length(s.get("OVERALL LENGTH") or s.get("OAL")) or \
        length(grab(t, NUM + r'\s*(MM)?\s*"?\s*OAL'))
    # "4 FLUTE" / "3FL" / "4 VARI FLUTE", never the "1.250 FLUTE LENGTH" form.
    z = s.get("NUMBER OF FLUTES") or s.get("FLUTES") or \
        grab(t, r"(?<![\d./-])(\d{1,2})\s*-?\s*(?:VARIABLE\s+|VARI\s+)?(?:FLUTES?|FL)\b(?!\s*LENGTH)")
    f["z"] = int(re.match(r"\d+", z).group(0)) if z and re.match(r"\d+", z) else None
    cr = s.get("RAD") or s.get("RADIUS") or s.get("CORNER RADIUS")
    f["cr"] = length(cr) if cr else length(grab(t, NUM + r'\s*(MM)?\s*"?\s*(?:CORNER RAD|CR\b|RAD\b|RADIUS)'))
    f["cr_range"] = re.search(r"\.(\d+)\s*-\s*\.(\d+)\s*CORNER RAD", t)
    pa = s.get("POINT ANGLE") or grab(t, r"(\d{2,3})\s*(?:DEG|°|DEGREE)")
    f["angle"] = float(pa) if pa and re.fullmatch(r"\d+(\.\d+)?", pa.strip()) else None
    coats = ["ALTIN", "TIALN", "ZRN", "TICN", "TIN", "NACO", "NANO/3", "NANO", "DLC", "HARDEDGE", "AMORPHOUS", "UNCOATED"]
    f["coat"] = next((c for c in coats if re.search(r"\b" + re.escape(c) + r"\b", t)), "")
    f["mat"] = "hss" if re.search(r"\bHSS\b|COBALT|HIGH SPEED STEEL|\bM42\b", t) else "carbide"
    return f, t


def classify(r, t):
    for pat, why in UNMAPPED:
        if re.search(pat, t):
            return None, why
    # A set/package is named so in its TITLE (single tools' text may
    # mention the package they also come in).
    if re.search(r"\bPACKAGE\b|\bSET\b|\d-PC\b", r["title"].upper()):
        return None, "multi-tool package/set: map the single tools"
    # A reamer is one by its title; a PRE-REAM end mill is a plain
    # (undersized) end mill whose text mentions the reamer it precedes.
    if re.search(r"\bREAMERS?\b", (r["title"] + "|" + r["crumb"]).upper()) and "PRE-REAM" not in r["title"].upper():
        return None, "reamer: no CamCraft reamer kind"
    # The kind is read from the TITLE first; the description only when the
    # title names no type (descriptions mention chamfers, drills, ...).
    for txt in (r["title"].upper(), t):
        if "SPOT DRILL" in txt or "SPOTTING DRILL" in txt:
            return "spot", None
        if "DRILL MILL" in txt or "DRILLMILL" in txt:
            return "drillmill", None
        if "CHAMFER" in txt:
            return "chamfer", None
        if re.search(r"\bDRILL\b|\bDRILLS\b", txt):
            return "drill", None
        if re.search(r"BALL", txt):
            return "ball", None
        if re.search(r"END ?MILL|ENDMILL|ROUGH|FLUTE|CUTTER", txt):
            return "flat", None
    return None, "not recognised as a cutting tool type"


def map_one(r):
    f, t = fields(r)
    kind, why = classify(r, t)
    if why:
        return None, why
    d, loc, shank, oal, z = f["d"], f["loc"], f["shank"], f["oal"], f["z"]
    notes = []
    if d is None or oal is None:
        return None, "diameter or overall length not published"
    if shank is None:
        # A drill, spot drill or drill mill is a straight round body: its
        # shank is its cutting diameter. An end mill of 1/4" and up is
        # taken the same way (smaller ones often carry a larger shank,
        # so those stay refused). Flagged for review.
        if kind in ("drill", "spot", "drillmill") or (kind in ("flat", "ball") and d >= 6.35 - 1e-9):
            shank = d
            notes.append("shank not published; shank = cutting diameter")
        else:
            return None, "shank diameter not published"
    pn = r["part"] or "?"
    tm = re.match(r'\s*(\d+-\d+/\d+|\d+/\d+|\d*\.\d+|\d+)\s*(MM)?\s*("|DIA|MM)', r["title"].upper().replace("''", '"'))
    if tm and frac(tm.group(1)) is not None:
        v = frac(tm.group(1))
        tmm = v if (tm.group(2) or tm.group(3) == "MM") else v * INCH
        if abs(tmm - d) > 0.01:
            return None, f"page contradicts itself: title size {tm.group(1)} vs dimension {d / INCH:.4f}in"
    inch_d = d / INCH
    dtxt = f'{fmt_in(inch_d)}"' if not re.search(r"\d\s*MM", t.split("|")[0]) else f"{d:g}mm"
    coat = f["coat"]
    if any("COAT" in o.upper() for o in r.get("options", [])):
        coat = "coating-option"  # the page sells it coated or uncoated
    if kind in ("flat", "ball"):
        if loc is None:
            return None, "flute length not published"
        if kind == "ball":
            tdef = tool("ball_nose", d, loc, shank, oal, z, corner_r=d / 2, tool_mat=f["mat"])
            k = "ball"
        else:
            cr = f["cr"]
            if f["cr_range"]:
                lo = float("." + f["cr_range"].group(1)) * INCH
                cr = lo
                notes.append(f"page states a corner-radius RANGE ({f['cr_range'].group(0).lower()}); written at its low end")
            if cr and cr > 0:
                if cr > d / 2 + 1e-9:
                    return None, f"corner radius {cr} mm exceeds half the diameter"
                tdef = tool("bull_nose", d, loc, shank, oal, z, corner_r=cr, tool_mat=f["mat"])
                k = f"CR {fmt_in(cr / INCH)}" if "MM CORNER" not in t else f"CR {cr:g}mm"
            else:
                tdef = tool("end_mill", d, loc, shank, oal, z, tool_mat=f["mat"])
                k = "flat"
        if "NECK" in t or "REACH" in t:
            notes.append("necked/long-reach: neck not modelled; shank drawn from the top of the flutes (conservative envelope)")
    elif kind in ("spot", "drill", "drillmill", "chamfer"):
        a = f["angle"]
        if not a:
            return None, "point angle not published"
        if kind == "chamfer":
            # Only a sharp-point chamfer is CamCraft's taper; a stated tip
            # diameter means a flat tip.
            if any(k.upper().startswith("TIP") for k in r["spec"]) or "TIP" in t:
                return None, "chamfer tool with a flat tip diameter; CamCraft's chamfer mill is a cone from a sharp tip"
            if loc is None:
                return None, "chamfer: cone length / tip not published"
        if loc is None:
            return None, "flute length not published"
        if kind == "drillmill" or kind == "chamfer":
            tdef = tool("taper", d, loc, shank, oal, z, tip_angle=a, tool_mat=f["mat"])
            k = f"{a:g}deg drill mill" if kind == "drillmill" else f"{a:g}deg chamfer"
            notes.append("drill mill written as CamCraft taper (cone + straight land) for chamfer/spot use")
        else:
            tdef = tool("drill", d, loc, shank, oal, z, tip_angle=a, tool_mat=f["mat"])
            k = f"{a:g}deg spot drill" if kind == "spot" else f"{a:g}deg drill"
    if z is None:
        notes.append("flute count not published; flutes left unset")
    metric = dtxt.endswith("mm")
    L = (lambda v: f"{v:g}mm") if metric else (lambda v: fmt_in(v / INCH))
    loc_txt = f" LOC {L(round(tdef['flute_len'], 3))}" if tdef["flute_len"] else ""
    name = f"LSC {pn} {dtxt} {str(z) + 'FL ' if z else ''}{k} {(coat if coat == 'coating-option' else coat.title()) if coat else ''}{loc_txt} OAL {L(round(oal, 3))}"
    name = " ".join(name.split())
    if not sane(tdef):
        return None, f"fails sanity check: {tdef}"
    return (name, tdef, notes), None


HEADS = {"LETTER", "DIAMETER", "SIZE", "FLUTE LENGTH", "SHANK DIAMETER", "SHANK DIA.", "OVERALL LENGTH", "RADIUS",
         "NUMBER OF FLUTES", "LOC", "OAL", "POINT ANGLE", "CORNER RADIUS", "TIP DIAMETER", "FLUTES"}


def option_records(cat_urls):
    """LSC sells some products as ONE page with a drop-down (coating, corner
    radius, size) and no part number; the crawler saw them as categories.
    Expand each into one record per row of its dimension table (one row:
    a coating choice only). Part number: none on the page - the URL slug
    stands in. Pages with options but no dimension table (e.g. drill size
    lists) are returned for the unmapped list."""
    import html as _h
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import crawl_lsc
    import fetch
    recs, bare = [], []
    for u in cat_urls:
        url = "https://www.lakeshorecarbide.com" + u
        p = fetch.cache_path(url)
        if not os.path.exists(p):
            continue
        h = open(p, encoding="utf-8", errors="replace").read()
        if "Product Options" not in h:
            continue
        t = crawl_lsc.text_of(h)
        title = ""
        tm = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", h)
        if tm:
            title = re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", "", tm.group(1)))).strip()
        bc = re.search(r"Screen Share\|Home\|>\|(.*?)\|Next in", t)
        crumb = bc.group(1) if bc else ""
        opts = re.findall(r"\|([A-Za-z -]+):\|Select [^|]+\|", t)
        i = t.find("Email this page to a friend|")
        j = t.find("|Product Reviews", i)
        toks = t[i + 28:j].split("|") if i >= 0 else []
        k = next((n for n, x in enumerate(toks) if x.strip().upper().rstrip(":") in HEADS), None)
        if k is None:
            bare.append({"url": url, "part": "", "title": title or crumb.split("|")[-1],
                         "reason": f"option page ({', '.join(opts) or 'options'}) lists sizes without a dimension table"})
            continue
        desc = "|".join(toks[:k])
        hdr = []
        n = k
        while n < len(toks) and toks[n].strip().upper().rstrip(":") in HEADS:
            hdr.append(toks[n].strip())
            n += 1
        vals = [v.replace("*", "").strip() for v in toks[n:]]
        rows = [vals[a:a + len(hdr)] for a in range(0, len(vals) - len(hdr) + 1, len(hdr))]
        slug = u.strip("/").replace(".aspx", "")
        for ri, row in enumerate(rows):
            spec = dict(zip(hdr, row))
            lab = spec.get("Radius") or (spec.get("Diameter") or spec.get("Letter") or str(ri + 1)).split(" ")[0]
            lab = re.sub(r"\s*\(.*", "", lab).strip().lstrip("#")
            part = slug + (f"#{lab}" if len(rows) > 1 else "")
            recs.append({"url": url, "crumb": crumb, "title": title, "part": part, "spec": spec,
                         "desc": desc, "options": opts})
    return recs, bare


def main():
    data = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "cache", "lsc-products.json")))
    entries, unmapped, kinds, notes, seen = [], [], {}, [], set()
    opt_recs, opt_bare = option_records(data["categories"])
    unmapped += opt_bare
    for r in data["products"] + opt_recs:
        key = r["part"] or r["url"]
        if key in seen:  # same product reached from two categories
            continue
        seen.add(key)
        res, why = map_one(r)
        if why:
            unmapped.append({"url": r["url"], "part": r["part"], "title": r["title"], "reason": why})
            continue
        name, t, n = res
        entries.append((name, t, r["url"]))
        kinds[t["kind"]] = kinds.get(t["kind"], 0) + 1
        if n:
            notes.append({"name": name, "url": r["url"], "notes": n})
    n = write_library(os.path.join(ROOT, "lakeshore-carbide.camtools"), [(a, b) for a, b, _ in entries])
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    json.dump({"category_pages": len(data["categories"]) - len({r["url"] for r in opt_recs}) - len(opt_bare),
               "option_pages": len({r["url"] for r in opt_recs}) + len(opt_bare), "option_rows": len(opt_recs),
               "products": len(seen) + len(opt_bare), "written": n,
               "kinds": kinds, "unmapped": unmapped, "notes": notes, "fetch_stats": data["stats"],
               "source": {a: c for a, _, c in entries}},
              open(os.path.join(ROOT, "reports", "lsc.json"), "w"), indent=1)
    print("option pages:", len({r["url"] for r in opt_recs}), "rows", len(opt_recs), "bare", len(opt_bare))
    print("lsc:", len(seen), "products,", n, "written", kinds, len(unmapped), "unmapped")


if __name__ == "__main__":
    main()
