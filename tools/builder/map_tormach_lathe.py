"""Tormach lathe tooling -> CamCraft lathe tools (tormach-lathe.camtools).

A lathe tool in CamCraft is one holder WITH its insert: the Turning/Bore
kinds need the insert's nose radius, Groove the blade width, Thread the
V. So each Tormach holder page is paired with every Tormach insert page
it takes, matched by the ANSI/ISO code letters the pages print
(ISO 1832 / ANSI B212.4 insert code: shape letter, clearance letter,
IC size digit; ISO 5608 / ANSI holder code: the same three in the holder
designation). Grooving holders carry the insert their page names;
threading holders take the inserts of the same size, application (E
external, I/N internal) and hand.

Model (as the shipped catalog assets/tools/catalog.json lays out lathe
tools): diameter = holder shank / bar size; nose_radius = the insert's
corner radius (round insert: IC/2); width = blade width (Groove) or the
thread V's crest opening (Thread); flute_len = the insert's exposed
length, taken as its IC (a default); shank_len = tool length - that.
Orientation (LinuxCNC 1-9, crates/tools/src/orientation.rs): RH OD tool
2, LH OD tool 1, neutral tool 6 (points -X), RH boring bar 3, LH boring
bar 4, grooving blade 2 (the -Z corner, CamCraft's default) - how a
PathPilot user mounts them on the 8L/15L front tool post; an assumption
to check per setup.

rpm/feed: cutting.rs has no turning rows and a turning rpm depends on the
WORK diameter, so every lathe tool carries the safest placeholder the
format allows (rpm 500, feed 25 mm/min = 0.05 mm/rev); the per-material
starting Vc and f/rev are in FEEDS-AND-SPEEDS.md's turning section.

Run: python3 -I map_tormach_lathe.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import INCH  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RPM, FEED = 500, 25.0
TPI_MAX_PITCH = {"A": 25.4 / 16, "AG": 25.4 / 8, "G": 25.4 / 8}  # partial-profile range codes


def num(s):
    m = re.search(r"(\d*\.\d+|\d+)", s or "")
    return float(m.group(1)) if m else None


def inch_mm(s):
    """'0.750 in. (12)' / '3/8 in. (3)' / '6mm (2)' -> mm."""
    if not s:
        return None
    s = s.split("(")[0].strip()
    if "mm" in s:
        return num(s)
    m = re.match(r"\s*(\d+)/(\d+)", s)
    if m:
        return int(m.group(1)) / int(m.group(2)) * INCH
    v = num(s)
    return None if v is None else v * INCH


def code_digit(s):
    m = re.search(r"\(([\d.]+)\)", s or "")
    return m.group(1) if m else None


def insert_code(p):
    a = p["attrs"]
    for k in ("Designation", "Designation (ANSI/ISO)", "ANSI Code"):
        v = a.get(k)
        if v and v != "NA":
            return v.split("/")[0].strip()
    return p["name"]


def lathe_def(kind, d, nose=0.0, width=0.0, tip=0.0, flute=0.0, length=0.0, orient=None):
    t = {"kind": kind, "diameter": round(d, 6), "corner_r": 0.0, "tip_angle": tip, "pitch": 0.0,
         "nose_radius": round(nose, 6), "width": round(width, 6), "flute_len": round(flute, 6),
         "shank_d": round(d, 6), "shank_len": round(max(length - flute, 0.0), 6), "holder_d": 0.0,
         "holder_len": 0.0, "material_group": "turning - see FEEDS-AND-SPEEDS.md", "rpm": RPM,
         "feed": FEED, "tool_material": "carbide"}
    if orient is not None:
        t["orientation"] = orient
    return t


def sane(t):
    d = t["diameter"]
    if not (d > 0 and t["flute_len"] > 0 and t["rpm"] > 0 and t["feed"] > 0):
        return False
    k = t["kind"]
    if k in ("turning",):
        return 0 < t["nose_radius"] <= d / 2
    if k == "bore":
        return t["nose_radius"] >= 0
    if k == "groove":
        return 0 < t["width"] < d
    if k == "thread":
        return 0 < t["width"] < d and 0 < t["tip_angle"] < 180
    return True


def main():
    data = json.load(open(os.path.join(ROOT, "cache", "tormach-products.json")))
    ps = [p for p in data["products"] if "error" not in p]
    inserts, thread_ins, grooves, holders, bars, gholders, tholders, other = [], [], {}, [], [], [], [], []
    for p in ps:
        a, n = p["attrs"], p["name"]
        if re.search(r"(?i)screw|shim|\bkit\b|\bset\b|starter|wrench", n):
            if re.search(r"(?i)lathe|turning|boring|parting|insert screw|shim", n + p["head"]):
                other.append((p, "lathe set/kit or spare part: map the single tools"))
            continue
        if "Shape" in a and "Corner Radius" in a:
            inserts.append(p)
        elif re.match(r"\d\d[EIN][RL]", a.get("Designation", "") or n):
            thread_ins.append(p)
        elif re.match(r"GTN-\d", a.get("Designation", "")):
            grooves[a["Designation"]] = p
        elif "Bar Diameter" in a and "Insert Shape" in a:
            bars.append(p)
        elif "Insert Size" in a and ("Shank Size" in a or "Bar Diameter" in a):
            tholders.append(p)
        elif "Insert" in a and "Shank Size" in a:
            gholders.append(p)
        elif "Insert Shape" in a and "Shank Size" in a:
            holders.append(p)
        elif re.search(r"(?i)cut-off blade|parting|JCQ|JCL", n + json.dumps(a)):
            other.append((p, "parting/threading blade or insert with no published width/holder pairing"))

    def ins_key(p):
        a = p["attrs"]
        code = insert_code(p).replace(" ", "")
        return code[0], code[1], code_digit(a.get("Insert I.C.")) or ""

    entries, unmapped, used = [], [], set()
    for h in holders + bars:
        a = h["attrs"]
        des = a["Designation"]
        is_bar = h in bars
        shape = (re.search(r"\(([A-Z])\)", a["Insert Shape"]) or [None, None])[1]
        clear = (re.search(r"\(([A-Z])\)", a["Clearance Angle"]) or [None, None])[1]
        icd = code_digit(a.get("Insert I.C."))
        hand = (re.search(r"\(([RLN])\)", a.get("Hand", "")) or [None, None])[1]
        d = inch_mm(a.get("Bar Diameter") if is_bar else a.get("Shank Size"))
        length = inch_mm(a.get("Tool Length"))
        matches = [i for i in inserts if ins_key(i) == (shape, clear, icd)]
        if not matches:
            unmapped.append({"url": h["url"], "name": h["name"], "reason": f"no Tormach insert page matches its pocket ({shape}?{clear} IC code {icd})"})
            continue
        for i in matches:
            ia = i["attrs"]
            ic = inch_mm(ia.get("Insert I.C."))
            cr = ia.get("Corner Radius", "")
            if "Round" in cr or shape == "R":
                nose = ic / 2
            elif "Sharp" in cr:
                unmapped.append({"url": h["url"] + " + " + i["url"], "name": f"{des} + {insert_code(i)}",
                                 "reason": "sharp (0) nose: CamCraft's turning insert needs a nose radius > 0"})
                used.add(i["url"])
                continue
            else:
                nose = inch_mm(cr)
            if is_bar:
                orient = 3 if hand == "R" else 4
                t = lathe_def("bore", d, nose=nose, flute=ic, length=length, orient=orient)
            else:
                orient = 2 if hand == "R" else 1 if hand == "L" else 6
                t = lathe_def("turning", d, nose=nose, flute=ic, length=length, orient=orient)
            used.add(i["url"])
            name = (f"Tormach {h['pn']} {des} + {i['pn']} {insert_code(i)} "
                    f"{'boring bar' if is_bar else 'turning'} {('RH' if hand == 'R' else 'LH' if hand == 'L' else 'NH')} "
                    f"R{nose:.2f}mm orient {orient}")
            if sane(t):
                entries.append((name, t, [h["url"], i["url"]]))
            else:
                unmapped.append({"url": h["url"], "name": name, "reason": f"fails sanity: {t}"})
    for g in gholders:
        a = g["attrs"]
        ins = grooves.get(a.get("Insert", ""))
        hand = (re.search(r"\(([RL])\)", a.get("Hand", "")) or [None, None])[1]
        d = inch_mm(a.get("Shank Size"))
        if not ins:
            unmapped.append({"url": g["url"], "name": g["name"], "reason": f"its insert {a.get('Insert')} has no page with a width"})
            continue
        used.add(ins["url"])
        w = inch_mm(ins["attrs"].get("Thickness", "").replace('"', " in."))
        # Tool length is not published for these holders: no shank band is
        # claimed (shank_len 0); flute_len = 2 x width, a default depth.
        t = lathe_def("groove", d, width=w, flute=w * 2, length=w * 2, orient=2)
        name = f"Tormach {g['pn']} {g['name'].split(':')[-1].strip()} + {ins['pn']} {a['Insert']} groove {('RH' if hand == 'R' else 'LH')} W{w:.3f}mm orient 2"
        if sane(t):
            entries.append((name, t, [g["url"], ins["url"]]))
        else:
            unmapped.append({"url": g["url"], "name": name, "reason": f"fails sanity: {t}"})
    for th in tholders:
        a = th["attrs"]
        des = a["Designation"]
        m = re.match(r"([A-Z])([EIN])([RL])(\d{4})([A-Z])(\d\d)", des)
        if not m:
            unmapped.append({"url": th["url"], "name": th["name"], "reason": "designation did not parse"})
            continue
        app = "E" if m.group(2) == "E" else "I"
        hand, size = m.group(3), m.group(6)
        d = int(m.group(4)) / 1000 * INCH
        length = inch_mm(a.get("Tool Length"))
        hit = False
        for ti in thread_ins:
            # The product NAME's code first: one page's Designation field
            # contradicts its own name (16ILAG60 page lists 16IRAG60).
            tm = (re.search(r"(\d\d)([EIN])([RL])(AG|A|G)(\d\d)", ti["name"].replace(" ", ""))
                  or re.match(r"(\d\d)([EIN])([RL])(AG|A|G)(\d\d)", (ti["attrs"].get("Designation") or "").replace(" ", "")))
            if not tm:
                continue
            tapp = "E" if tm.group(2) == "E" else "I"
            if (tm.group(1), tapp, tm.group(3)) != (size, app, hand):
                continue
            hit = True
            used.add(ti["url"])
            pmax = TPI_MAX_PITCH[tm.group(4)]
            w = 0.866 * pmax
            t = lathe_def("thread", d, width=w, tip=float(tm.group(5)), flute=w * 2, length=length)
            name = (f"Tormach {th['pn']} {des} + {ti['pn']} {tm.group(0)} thread {'OD' if app == 'E' else 'ID'} "
                    f"{'RH' if hand == 'R' else 'LH'} {tm.group(5)}deg up to {pmax:.3f}mm pitch")
            if sane(t):
                entries.append((name, t, [th["url"], ti["url"]]))
        if not hit:
            unmapped.append({"url": th["url"], "name": th["name"], "reason": "no matching threading-insert page"})
    for i in inserts + thread_ins + list(grooves.values()):
        if i["url"] not in used:
            unmapped.append({"url": i["url"], "name": i["name"], "reason": "insert with no Tormach holder page that takes it (shape/clearance/IC) - a lathe tool needs both"})
    for p, why in other:
        unmapped.append({"url": p["url"], "name": p["name"], "reason": why})
    tools = []
    seen = set()
    for n, t, _ in entries:
        if n in seen:
            continue
        seen.add(n)
        tools.append({"name": n, "definition": t})
    json.dump({"format": "camcraft-tools", "version": 1, "units": "mm", "tools": tools},
              open(os.path.join(ROOT, "tormach-lathe.camtools"), "w"), indent=1)
    kinds = {}
    for t in tools:
        kinds[t["definition"]["kind"]] = kinds.get(t["definition"]["kind"], 0) + 1
    json.dump({"holders": len(holders), "boring_bars": len(bars), "grooving_holders": len(gholders),
               "threading_holders": len(tholders), "inserts": len(inserts), "thread_inserts": len(thread_ins),
               "groove_inserts": len(grooves), "written": len(tools), "kinds": kinds, "unmapped": unmapped,
               "source": {n: s for n, _, s in entries}},
              open(os.path.join(ROOT, "reports", "tormach-lathe.json"), "w"), indent=1)
    print("tormach-lathe:", len(tools), "tools", kinds, len(unmapped), "unmapped")


if __name__ == "__main__":
    main()
