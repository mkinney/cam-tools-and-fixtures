#!/usr/bin/env python3
"""Download vendor fixture CAD files to your own machine, from the vendor's own site.

The files are the vendors' copyright and are NOT stored in this repository. This
script reads the URLs in <vendor>/SOURCES.md (lines "- <path> <- <url> ...") and
fetches each one once, politely (1 request/s), into ./downloads/<vendor>/<path>.

Usage: python3 -I fetch.py fireball [--out DIR]
Then import each STEP into CamCraft as a fixture (Model > Import as fixture, or the
MCP `import_model` + `add_fixture` tools) and save it to your fixture library.
"""
import argparse, os, re, sys, time, urllib.request

UA = "cam-tools-and-fixtures fetch.py (personal use)"
LINE = re.compile(r"^- (\S.*?) <- (https://\S+)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vendor")
    ap.add_argument("--out", default="downloads")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, a.vendor, "SOURCES.md")
    rows = [m.groups() for m in map(LINE.match, open(src, encoding="utf-8")) if m]
    if not rows:
        sys.exit(f"no URLs found in {src}")
    for path, url in rows:
        dest = os.path.join(a.out, a.vendor, path)
        if os.path.exists(dest):
            print("have", dest); continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r, open(dest + ".part", "wb") as f:
            f.write(r.read())
        os.replace(dest + ".part", dest)
        print("got ", dest)
        time.sleep(1)

if __name__ == "__main__":
    main()
