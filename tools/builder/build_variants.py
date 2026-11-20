"""From each base library, write the 5 per-material variants and the
feeds-and-speeds tables.

Run: python3 -I build_variants.py lakeshore-carbide almar-inch tormach
(each name is a base file ../<name>.camtools). Writes
../<name>-<material>.camtools for aluminum, mild-steel, stainless, brass,
acetal, plus ../FEEDS-AND-SPEEDS.csv and ../FEEDS-AND-SPEEDS.md.

All numbers: CamCraft's own cutting table + formulas (cutting.rs), low
end of each window, rpm capped at 10 000 - see common.py. Engagement
rules are the user's conservative starting points (listed in the .md).
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MATERIALS, RPM_CAP, TABLE, speeds  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABEL = {"aluminum": "aluminum", "mild-steel": "mild steel", "stainless": "stainless",
         "brass": "brass", "acetal": "acetal (Delrin/POM)"}
MILLS = {"end_mill", "ball_nose", "bull_nose", "taper"}


def engagement(t, mat):
    """Conservative engagement (mm) per the rules in the .md."""
    d, loc, kind = t["diameter"], t["flute_len"], t["kind"]
    hard = mat in ("mild-steel", "stainless")
    small = 0.5 if d < 3.0 else 1.0
    if kind == "drill":
        return {"peck": round((0.5 if mat == "stainless" else 1.0) * d * small, 3)}
    if kind == "taper":
        # A chamfer cone cuts on its flank: one pass, no stated
        # slot/side/adaptive engagement beyond the chamfer width.
        return {}
    slot = (0.25 if hard else 0.5) * d * small
    side_ap = min(loc, 1.5 * d) * small
    return {"slot_doc": round(min(slot, loc), 3),
            "side_woc": round(0.1 * d * small, 3), "side_doc": round(side_ap, 3),
            "adapt_woc": round(0.08 * d * small, 3), "adapt_doc": round(loc * small, 3)}


def main():
    rows = []
    for base in sys.argv[1:]:
        lib = json.load(open(os.path.join(ROOT, base + ".camtools")))
        for slug, word in MATERIALS.items():
            tools = []
            for e in lib["tools"]:
                t = dict(e["definition"])
                rpm, feed, fz = speeds(t["diameter"], t.get("flutes"), t.get("tool_material"), t["kind"], word)
                t.update(material_group=word, rpm=rpm, feed=feed)
                tools.append({"name": f'{e["name"]} - {LABEL[slug]}', "definition": t})
                eng = engagement(t, slug)
                rows.append({"library": base, "tool": e["name"], "material": LABEL[slug],
                             "kind": t["kind"], "dia_mm": t["diameter"],
                             "flutes": t.get("flutes", ""), "tool_material": t.get("tool_material", ""),
                             "rpm": rpm, "feed_mm_min": feed, "feed_in_min": round(feed / 25.4, 2),
                             "fz_mm": fz, **eng})
            doc = dict(lib, tools=tools)
            json.dump(doc, open(os.path.join(ROOT, f"{base}-{slug}.camtools"), "w"), indent=1)
        print(base, len(lib["tools"]), "tools x", len(MATERIALS), "materials")
    keys = ["library", "tool", "material", "kind", "dia_mm", "flutes", "tool_material", "rpm",
            "feed_mm_min", "feed_in_min", "fz_mm", "slot_doc", "side_woc", "side_doc",
            "adapt_woc", "adapt_doc", "peck"]
    with open(os.path.join(ROOT, "FEEDS-AND-SPEEDS.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    write_md(rows, keys)


def write_md(rows, keys):
    L = ["# Feeds and speeds - conservative starting points", "",
         "**Starting points to adjust by ear and by chip, not limits.** Every number is computed",
         "with CamCraft's own cutting table and formulas (`crates/tools/src/cutting.rs`:",
         "n = Vc*1000/(pi*D), vf = fz*z*n, fz scaled by CamCraft's diameter bands), taking the",
         "**low end** of each table window - at or below CamCraft's own suggestion, which uses the",
         "window midpoint. No vendor feeds/speeds chart was used.", "",
         f"- **Spindle cap:** rpm is capped at {RPM_CAP:.0f} (Tormach 770MX/1100MX spindle max). Small",
         "  tools hit the cap; their feed is computed at the capped rpm, so the chip load stays at the",
         "  table's fz.",
         "- **Tool material:** carbide unless the product page says HSS or cobalt (cobalt uses the HSS",
         "  column). Unknown flute counts use z = 1 in the feed (conservative).",
         "- **Drills** are not tabulated by cutting.rs; feed per rev = one lip's fz (half the two-lip",
         "  value) at the material's low Vc.",
         "- **Ball/bull noses:** rpm and feed at the nominal diameter (no effective-diameter rpm boost);",
         "  engagement factors applied at the nominal diameter.",
         "- **Chamfer mills (taper):** one pass along the chamfer; no slot/side/adaptive engagement given.",
         "", "## Material table used (CamCraft cutting.rs, low end taken)", "",
         "| Material | CamCraft group | Carbide Vc m/min | Carbide fz@10mm | HSS Vc | HSS fz@10mm |",
         "|---|---|---|---|---|---|"]
    for slug, word in MATERIALS.items():
        c, h = TABLE[word]["carbide"], TABLE[word]["hss"]
        L.append(f"| {LABEL[slug]} | `{word}` | {c[0][0]} (of {c[0][0]}-{c[0][1]}) | {c[1][0]} | "
                 f"{h[0][0]} (of {h[0][0]}-{h[0][1]}) | {h[1][0]} |")
    L += ["", "## Engagement rules (mm in the tables)", "",
          "- **Slotting** (`slot_doc`): axial DOC 0.5 x D; 0.25 x D in mild steel and stainless; never above LOC.",
          "- **Side milling / profiling** (`side_woc`, `side_doc`): radial WOC 0.1 x D, axial DOC up to",
          "  1 x LOC, capped at 1.5 x D.",
          "- **Adaptive / HSM** (`adapt_woc`, `adapt_doc`): WOC 0.08 x D, full LOC.",
          "- **Drills** (`peck`): peck 1 x D; 0.5 x D in stainless.",
          "- **Tools under 3 mm:** every engagement factor above is halved.",
          "", "Full rows (every tool x material) are in `FEEDS-AND-SPEEDS.csv`; the tables below are the",
          "same data, one per library and material.", ""]
    L += turning_section()
    cols = ["tool", "rpm", "feed_mm_min", "feed_in_min", "fz_mm", "slot_doc", "side_woc", "side_doc",
            "adapt_woc", "adapt_doc", "peck"]
    groups = {}
    for r in rows:
        groups.setdefault((r["library"], r["material"]), []).append(r)
    for (lib, mat), rs in groups.items():
        L += [f"### {lib} - {mat}", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        for r in rs:
            L.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
        L.append("")
    open(os.path.join(ROOT, "FEEDS-AND-SPEEDS.md"), "w").write("\n".join(L))


# Turning (tormach-lathe.camtools). cutting.rs has no turning rows: Vc is
# the same material/tool-material row's LOW end (it is a cutting-edge
# surface speed either way); feed per rev and depth of cut are our own
# conservative starting values, not from any vendor chart.
TURN_F = [("OD/ID turning, roughing", 0.10, "1.0 (0.5 in stainless and mild steel)"),
          ("OD/ID turning, finishing", 0.05, "0.25"),
          ("Boring bar", 0.05, "0.5 (0.25 in stainless)"),
          ("Grooving / parting", 0.03, "plunge; peck 0.5 x width in stainless"),
          ("Threading", None, "spring passes; 60 deg infeed per the thread op")]
LATHE_MAX = {"8L": 5000, "15L Slant-PRO": 2500, "15LX Slant-PRO": 3500}


def turning_section():
    from math import pi
    L = ["## Turning (tormach-lathe.camtools)", "",
         "CamCraft's `cutting.rs` has **no turning rows** and a lathe tool's `rpm`/`feed` fields are a",
         "milling-style spindle speed and mm/min, so every lathe tool in `tormach-lathe.camtools` carries",
         "the safest placeholder (rpm 500, feed 25 mm/min = 0.05 mm/rev) and no per-material variant",
         "files are written for it: a turning rpm depends on the WORK diameter, which the tool cannot",
         "know. Use these starting points per job instead.", "",
         "- **Vc:** the low end of the same material row in `cutting.rs` (carbide inserts / HSS).",
         "- **rpm:** n = Vc*1000/(pi*D_work), capped at the machine's spindle max (CamCraft machine",
         "  files: " + ", ".join(f"{k} {v}" for k, v in LATHE_MAX.items()) + " rpm).",
         "- **Feed per rev / DOC:** our own conservative values (below), not from a vendor chart.", "",
         "| Material | Carbide Vc m/min | HSS Vc m/min | rpm @ D25 carbide (8L cap) | rpm @ D50 carbide |",
         "|---|---|---|---|---|"]
    for slug, word in MATERIALS.items():
        vc_c = TABLE[word]["carbide"][0][0]
        vc_h = TABLE[word]["hss"][0][0]
        n25 = min(vc_c * 1000 / (pi * 25), LATHE_MAX["8L"])
        n50 = min(vc_c * 1000 / (pi * 50), LATHE_MAX["8L"])
        L.append(f"| {LABEL[slug]} | {vc_c} | {vc_h} | {n25:.0f} | {n50:.0f} |")
    L += ["", "| Operation | Feed mm/rev | Radial DOC mm |", "|---|---|---|"]
    for op, f, doc in TURN_F:
        L.append(f"| {op} | {f if f else '= thread pitch'} | {doc} |")
    L += ["", "Starting points to adjust by ear and chip, not limits.", ""]
    return L


if __name__ == "__main__":
    main()
