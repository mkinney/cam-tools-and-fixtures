"""Shared helpers: inch-fraction parsing, CamCraft tool definitions, writing
a `camcraft-tools/1` library, and conservative feeds/speeds.

Speeds/feeds: CamCraft requires rpm > 0 and feed > 0 on every tool. No
vendor feeds/speeds chart is used. Every value comes from CamCraft's OWN
cutting table and formulas (crates/tools/src/cutting.rs), reimplemented
below, at the LOW end of each window, rpm capped at 10 000 (Tormach
770MX/1100MX spindle max). Base libraries carry the aluminium row.
"""
import json
import math
import re

INCH = 25.4
RPM_CAP = 10000.0
MATERIAL_GROUP = "aluminium_6061"


def frac(s):
    """'1/4' -> 0.25, '2 1/2' / '2-1/2' -> 2.5, '.750' -> 0.75, '1.5' -> 1.5.
    Returns None when the text is not a clean number."""
    if s is None:
        return None
    s = s.strip().replace('"', "").replace("in.", "").replace("in", "").replace("″", "").strip()
    s = s.rstrip(".").strip()
    m = re.fullmatch(r"(\d+)[ -](\d+)/(\d+)", s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / int(m.group(3))
    m = re.fullmatch(r"(\d+)/(\d+)", s)
    if m and int(m.group(2)):
        return int(m.group(1)) / int(m.group(2))
    m = re.fullmatch(r"\d*\.\d+|\d+(?:\.\d*)?", s)
    if m:
        return float(s)
    return None


def mm(inches):
    return None if inches is None else round(inches * INCH, 6)


def fmt_in(x):
    """0.25 -> '1/4', 2.5 -> '2-1/2', 0.093 -> '.093' (fractions to 1/64)."""
    whole = int(math.floor(x + 1e-9))
    rem = x - whole
    for den in (2, 4, 8, 16, 32, 64):
        num = rem * den
        if abs(num - round(num)) < 1e-6:
            num = int(round(num))
            if num == 0:
                return str(whole)
            if num == den:
                return str(whole + 1)
            g = math.gcd(num, den)
            f = f"{num // g}/{den // g}"
            return f"{whole}-{f}" if whole else f
    return f"{x:.4f}".rstrip("0").lstrip("0") if x < 1 else f"{x:.4f}".rstrip("0")


# CamCraft's own cutting table (crates/tools/src/cutting.rs TABLE),
# reimplemented: (Vc low, Vc high) m/min and (fz low, fz high) mm at a
# 10 mm cutter, per tool material. We take the LOW end of each window -
# at or below CamCraft's own suggestion (crates/app/src/cutting.rs
# `compute` uses the window midpoint) - for conservative starting values.
TABLE = {
    "aluminium_6061": {"hss": ((100, 250), (0.04, 0.08)), "carbide": ((250, 600), (0.05, 0.10))},
    "mild_steel":     {"hss": ((20, 35), (0.03, 0.06)),   "carbide": ((120, 250), (0.04, 0.08))},
    "stainless_304":  {"hss": ((10, 20), (0.02, 0.04)),   "carbide": ((60, 120), (0.03, 0.06))},
    "brass":          {"hss": ((60, 100), (0.04, 0.08)),  "carbide": ((150, 300), (0.05, 0.10))},
    "plastics_pom":   {"hss": ((100, 250), (0.05, 0.12)), "carbide": ((200, 500), (0.06, 0.15))},
}
# Library file slug -> CamCraft work-material word.
MATERIALS = {"aluminum": "aluminium_6061", "mild-steel": "mild_steel", "stainless": "stainless_304",
             "brass": "brass", "acetal": "plastics_pom"}


def fz_scale(d):
    """cutting.rs fz_scale: five diameter bands around the 10 mm reference."""
    return 0.25 if d <= 3 else 0.5 if d <= 6 else 1.0 if d <= 12 else 1.4 if d <= 20 else 1.8


def speeds(d_mm, flutes, tool_mat, kind, material="aluminium_6061"):
    """Conservative CamCraft-table rpm (n = Vc*1000/(pi*D), capped at
    RPM_CAP) and feed (vf = fz*z*n). Returns (rpm, feed, fz).
    Drills: feed per rev taken as ONE lip's fz (half the two-lip value),
    a deliberately conservative reading - cutting.rs does not tabulate
    drills. Tool material unknown or cobalt -> the HSS column."""
    col = "carbide" if tool_mat == "carbide" else "hss"
    (vc, _), (fz10, _) = TABLE[material][col]
    fz = fz10 * fz_scale(d_mm)
    rpm = min(vc * 1000.0 / (math.pi * max(d_mm, 0.1)), RPM_CAP)
    z = 1 if kind == "drill" else (flutes or 1)
    rpm = math.floor(rpm)
    feed = math.floor(fz * z * rpm * 10) / 10
    return rpm, max(feed, 1.0), round(fz, 5)


def tool(kind, d, flute_len, shank_d, oal, flutes=None, corner_r=0.0, tip_angle=0.0,
         pitch=0.0, tool_mat="carbide", center_cutting=True):
    """A CamCraft ToolDto (mm). shank_len = OAL - flute length (the plain
    shank stack above the flutes); holder left 0 (the setup's holder)."""
    shank_len = max(oal - flute_len, 0.0) if oal else 0.0
    rpm, feed, _ = speeds(d, flutes, tool_mat, kind)
    if kind == "tap" and pitch > 0:
        rpm = min(rpm, 500)
        feed = round(rpm * pitch, 2)
    d = round(d, 6)
    # Never let rounding push the corner past half the diameter (a ball's
    # corner IS d/2): floor to the micron.
    corner_r = min(math.floor(corner_r * 1e6) / 1e6, math.floor(d / 2 * 1e6) / 1e6)
    t = {"kind": kind, "diameter": d, "corner_r": corner_r,
         "tip_angle": tip_angle, "pitch": round(pitch, 6), "flute_len": round(flute_len, 6),
         "shank_d": round(shank_d or 0.0, 6), "shank_len": round(shank_len, 6),
         "holder_d": 0.0, "holder_len": 0.0, "material_group": MATERIAL_GROUP,
         "rpm": rpm, "feed": feed}
    if tool_mat:
        t["tool_material"] = tool_mat
    if flutes:
        t["flutes"] = int(flutes)
    if not center_cutting:
        t["center_cutting"] = False
    return t


def sane(t):
    """The same law Tool::is_sane applies, checked before writing so a
    refusal at import means a real disagreement, not a typo."""
    d = t["diameter"]
    ok = (d > 0 and d <= 500 and 0 <= t["corner_r"] <= d / 2 and t["tip_angle"] < 180
          and t["flute_len"] > 0 and t["shank_d"] >= 0 and t["shank_len"] >= 0
          and t["rpm"] > 0 and t["feed"] > 0 and (t.get("flutes") is None or 1 <= t["flutes"] <= 32))
    k = t["kind"]
    if k == "drill":
        ok = ok and t["tip_angle"] > 60
    if k == "taper":
        ok = ok and t["tip_angle"] > 0
    if k == "tap":
        ok = ok and t["pitch"] > 0
    return ok


def write_library(path, entries):
    """entries: list of (name, definition). Names made unique."""
    seen = {}
    tools = []
    for name, d in entries:
        n = name
        if n in seen:
            seen[n] += 1
            n = f"{name} #{seen[name]}"
        else:
            seen[n] = 1
        tools.append({"name": n, "definition": d})
    doc = {"format": "camcraft-tools", "version": 1, "units": "mm", "tools": tools}
    with open(path, "w") as f:
        json.dump(doc, f, indent=1)
    return len(tools)
