"""Write ../REPORT.md from reports/*.json, import-results.json and the
hand-written sections in report_notes.md. Run: python3 -I make_report.py"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda n: json.load(open(os.path.join(ROOT, "reports", n)))  # noqa: E731


def unmapped_table(rows, key="name"):
    by = collections.defaultdict(list)
    for u in rows:
        by[u["reason"]].append(u)
    out = ["| Reason | Count | Products (link) |", "|---|---|---|"]
    for reason, us in sorted(by.items(), key=lambda kv: -len(kv[1])):
        links = ", ".join(f"[{(u.get(key) or u.get('title') or u.get('part') or u.get('sku') or '?')[:48]}]({u['url'].split(' + ')[0]})" for u in us)
        out.append(f"| {reason} | {len(us)} | {links} |")
    return "\n".join(out)


def imports():
    p = os.path.join(ROOT, "import-results.json")
    d = json.load(open(p))
    out = ["| File | Imported | Tools in document | Refused tools |", "|---|---|---|---|"]
    for k in sorted(d):
        v = d[k]
        out.append(f"| `{k}` | {'yes' if v['ok'] else '**REFUSED**'} | {v.get('tools_in_document', '-')} | "
                   f"{len(v['refused_tools'])} |")
    refused = [f"- `{k}` / {r['name']}: {r['message']}" for k, v in d.items() for r in v["refused_tools"]]
    return "\n".join(out), refused, d


def kinds(k):
    return ", ".join(f"{n} {kind}" for kind, n in sorted(k.items(), key=lambda kv: -kv[1]))


SPOT_RESULT = """**Result: all 30 sampled tools match their pages**, checked on diameter, LOC, shank, OAL,
corner radius, point angle and flute count. Notes from the check:

- LSC 360038XRF and 360516X carry `CR .003`. The pages state ".003-.005 corner radius",
  and the library takes the low end (decision 9).
- Almar point chamfers have no published LOC. Their LOC is the derived cone height,
  e.g. 3/8" × 90° gives .1875".
- Tormach metric jobber lengths match ISO 235 (8.6 mm → 81/125).

A whole-library check also compared every LSC title's leading size with the written
diameter. It found 1 mismatch out of 980 (250-5201502B: title .045", text .015 DIA), and
that tool was moved to unmapped as self-contradictory."""


def main():
    lsc, alm, tor, lat, dr, hol = (R("lsc.json"), R("almar.json"), R("tormach.json"), R("tormach-lathe.json"),
                                   R("drills.json"), R("holders.json"))
    itable, refused, idata = imports()
    from report_template import TEMPLATE, DECISIONS, GAPS
    notes = TEMPLATE.replace("{{DECISIONS}}", DECISIONS).replace("{{GAPS}}", GAPS)
    spot = open(os.path.join(ROOT, "reports", "spotcheck.md")).read()
    s = notes
    s = s.replace("{{IMPORTS}}", itable)
    s = s.replace("{{REFUSED}}", "\n".join(refused) if refused else "None: every file and every tool imported cleanly.")
    s = s.replace("{{N_FILES}}", str(len(idata)))
    lt = json.load(open(os.path.join(ROOT, "lakeshore-carbide.camtools")))["tools"]
    s = s.replace("{{FLUTELESS}}", str(sum(1 for x in lt if "flutes" not in x["definition"])))
    s = s.replace("{{SPOTCHECK}}", spot)
    for tag, rep in (("LSC", lsc), ("ALMAR", alm), ("TOR", tor), ("LATHE", lat)):
        s = s.replace(f"{{{{{tag}_UNMAPPED}}}}", unmapped_table(rep["unmapped"]))
        s = s.replace(f"{{{{{tag}_KINDS}}}}", kinds(rep["kinds"]))
        s = s.replace(f"{{{{{tag}_WRITTEN}}}}", str(rep["written"]))
        s = s.replace(f"{{{{{tag}_NUNMAPPED}}}}", str(len(rep["unmapped"])))
    s = s.replace("{{LSC_OPT_PAGES}}", str(lsc["option_pages"])).replace("{{LSC_OPT_ROWS}}", str(lsc["option_rows"]))
    s = s.replace("{{LSC_PRODUCTS}}", str(lsc["products"])).replace("{{LSC_CATS}}", str(lsc["category_pages"]))
    s = s.replace("{{LSC_FETCH}}", "1 804 pages fetched over two runs (first 1 766, then 38 for the page-2 listings), 1 error (HTTP 404 on /smittyseyeglasswax.aspx, a non-tool page), 0 blocked by robots.txt")
    s = s.replace("{{SPOT_RESULT}}", SPOT_RESULT)
    s = s.replace("{{ALMAR_PRODUCTS}}", str(alm["products"])).replace("{{ALMAR_FETCH}}", json.dumps(alm["fetch_stats"]))
    for k in ("pages", "non_cutting_skipped", "category_pages", "lathe_pages_routed", "products"):
        s = s.replace(f"{{{{TOR_{k}}}}}", str(tor[k]))
    s = s.replace("{{TOR_FETCH}}", json.dumps(tor["fetch_stats"]))
    for k in ("holders", "boring_bars", "grooving_holders", "threading_holders", "inserts", "thread_inserts", "groove_inserts"):
        s = s.replace(f"{{{{LATHE_{k}}}}}", str(lat[k]))
    s = s.replace("{{DRILL_FILES}}", ", ".join(f"`{k}.camtools` {v}" for k, v in dr["files"].items()))
    src = collections.Counter(("Tormach page" if r["source"].startswith("Tormach") else
                               "shorter neighbour" if r["source"].startswith("shorter") else "B94.11M anchor")
                              for r in dr["inch_length_source"])
    s = s.replace("{{DRILL_SRC}}", ", ".join(f"{v} from {k}" for k, v in src.items()))
    s = s.replace("{{HOLDERS}}", "\n".join(f"- `{k}`: {v['written']} tools, {len(v['no_holder'])} with no built-in holder for their shank"
                                          + "".join(f"\n  - {m['name']} (shank {m['shank_mm']} mm)" for m in v["no_holder"])
                                          for k, v in hol.items()))
    import re as _re
    reps = {"lsc": lsc, "almar": alm, "tormach": tor, "lathe": lat}

    def count(m):
        rep, sub = m.group(1), m.group(2).lower()
        return str(sum(1 for u in reps[rep]["unmapped"] if sub in u["reason"].lower()))
    s = _re.sub(r"\{\{C:(\w+):([^}]+)\}\}", count, s)

    def notes(m):
        rep, sub = m.group(1), m.group(2).lower()
        return str(sum(1 for n in reps[rep].get("notes", []) if any(sub in x.lower() for x in n["notes"])))
    s = _re.sub(r"\{\{N:(\w+):([^}]+)\}\}", notes, s)
    open(os.path.join(ROOT, "REPORT.md"), "w").write(s)
    print("REPORT.md written;", len(refused), "refused tools")


if __name__ == "__main__":
    main()
