"""Tormach mill libraries with a Tormach holder: tormach-bt30.camtools
(770MX/1100MX/1500MX) and tormach-tts.camtools (R8 770M/1100M/PCNC).

The .camtools reader (app tool_library.rs -> project::tool_from_json ->
ToolDto::to_tool) keeps no tool `body`: a drawn holder profile cannot ride
a library file. So each tool carries the holder as CamCraft's
holder_d/holder_len CYLINDER, sized as a conservative envelope of the
built-in holder entry (crates/tools/src/holder_library.rs and
holder_library_tts.rs on upstream main) - its LARGEST drawn diameter
(flange/collar, nut, or Weldon body + clamp-screw allowance) over its
whole gauge length. The holder's name is in the tool name so the user
can land the real drawn profile from the editor's holder picker.

Stick-out (holder nose to tip) defaults to flute length + 5 mm, capped
at OAL: a default to MEASURE, not a fact. shank_len is set to that
stick-out minus the flute length, so the holder cylinder starts where
the holder's nose really is.

Run: python3 -I build_holders.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STICK = 5.0

# Built-in entries, numbers as holder_library*.rs states them (mm).
ER = {"ER16": (0.5, 10.0, 32.0), "ER20": (1.0, 13.0, 35.0), "ER25": (1.0, 16.0, 42.0), "ER32": (2.0, 20.0, 50.0)}
BT30 = {"flange_d": 46.0, "gauge": 60.0}
TTS = {"collar_d": 38.1, "body_d": 38.1, "er_gauge": {"ER20": 52.0, "ER16": 49.0}, "ss_gauge": 60.0}
WELDON_SCREW = 1.0
BT30_WELDON = [("6 mm", 6.0, 25.0), ("8 mm", 8.0, 28.0), ("10 mm", 10.0, 35.0), ("12 mm", 12.0, 42.0),
               ("16 mm", 16.0, 48.0), ("1/4 in", 6.35, 25.4), ("3/8 in", 9.525, 31.75), ("1/2 in", 12.7, 34.925)]
TTS_SS = [("1/4 in", 6.35), ("5/16 in", 7.9375), ("3/8 in", 9.525), ("1/2 in", 12.7), ("6 mm", 6.0),
          ("10 mm", 10.0), ("12 mm", 12.0)]
SLACK = 0.02


def bt30(shank):
    """(holder name, envelope d, envelope len) or None."""
    for er in ("ER16", "ER20"):
        lo, hi, nut = ER[er]
        if shank <= (10.0 if er == "ER16" else 13.0) + 1e-9 and lo <= shank:
            return f"BT30 {er}", max(BT30["flange_d"], nut), BT30["gauge"]
    for label, bore, body in BT30_WELDON:
        if abs(shank - bore) <= SLACK:
            return f"BT30 Weldon {label}", max(BT30["flange_d"], body + 2 * WELDON_SCREW), BT30["gauge"]
    for er in ("ER25", "ER32"):
        lo, hi, nut = ER[er]
        if lo <= shank <= hi + 1e-9:
            return f"BT30 {er}", max(BT30["flange_d"], nut), BT30["gauge"]
    return None


def tts(shank):
    for er in ("ER16", "ER20"):
        lo, hi, nut = ER[er]
        if lo <= shank <= hi + 1e-9:
            return f"TTS {er}", max(TTS["collar_d"], nut), TTS["er_gauge"][er]
    for label, bore in TTS_SS:
        if abs(shank - bore) <= SLACK:
            return f"TTS Weldon {label}", max(TTS["collar_d"], TTS["body_d"] + 2 * WELDON_SCREW), TTS["ss_gauge"]
    return None


def build(base, pick, out, tag):
    lib = json.load(open(os.path.join(ROOT, base + ".camtools")))
    tools, missing = [], []
    for e in lib["tools"]:
        t = dict(e["definition"])
        h = pick(t["shank_d"])
        if not h:
            missing.append({"name": e["name"], "shank_mm": t["shank_d"], "reason": f"no built-in {tag} holder takes this shank"})
            continue
        hn, hd, hl = h
        oal = t["flute_len"] + t["shank_len"]
        stick = min(t["flute_len"] + STICK, oal)
        t.update(shank_len=round(stick - t["flute_len"], 6), holder_d=hd, holder_len=hl)
        tools.append({"name": f"{e['name']} [{hn}]", "definition": t})
    json.dump(dict(lib, tools=tools), open(os.path.join(ROOT, out), "w"), indent=1)
    return len(tools), missing


def main():
    rep = {}
    for base, pick, out, tag in [("tormach", bt30, "tormach-bt30.camtools", "BT30"),
                                 ("tormach", tts, "tormach-tts.camtools", "TTS")]:
        n, miss = build(base, pick, out, tag)
        rep[out] = {"written": n, "no_holder": miss}
        print(out, n, "written,", len(miss), "without a holder")
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    json.dump(rep, open(os.path.join(ROOT, "reports", "holders.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
