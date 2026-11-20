"""Crawl Tormach's public product pages that look like cutting tools.

Tormach's category pages list only kits/featured items, so the SKUs are
enumerated from the public sitemap and pre-filtered by URL slug
(../cache/tormach-candidates.txt, built by the README's grep). Each page's
"Key: Value" spec lines are parsed. Writes ../cache/tormach-products.json.
Run: python3 -I crawl_tormach.py
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch  # noqa: E402


def text_of(h):
    t = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", "", h)
    t = re.sub(r"<[^>]+>", "|", t)
    t = html.unescape(t)
    return re.sub(r"\s*\|[\s|]*", "|", t)


def parse(url, h):
    t = text_of(h)
    ptitle = ""
    m = re.search(r"(?is)<title>(.*?)</title>", h)
    if m:
        ptitle = html.unescape(m.group(1)).strip()
    pn = re.search(r"\|PN:\|([^|]+)\|", t)
    name = ""
    nm = re.search(r'(?is)<h1[^>]*class="page-title"[^>]*>(.*?)</h1>', h)
    if nm:
        name = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", nm.group(1)))).strip()
    attrs = {}
    # The spec block: "Heading: size|Key: v|Key: v|...|Details|"
    sm = re.search(r"Add to Wishlist\|(.*?)\|Details\|", t)
    head = ""
    if sm:
        parts = sm.group(1).split("|")
        if parts:
            head = parts[0]
        for p in parts[1:]:
            if ":" in p:
                k, v = p.split(":", 1)
                attrs[k.strip()] = v.strip()
    crumb = ""
    cm = re.search(r"\|Account\|Home\|(.*?)\|0 -->", t)
    if cm:
        crumb = cm.group(1)
    return {"url": url, "page_title": ptitle, "name": name, "head": head,
            "pn": pn.group(1).strip() if pn else "", "attrs": attrs, "crumb": crumb}


def main():
    cand = os.path.join(fetch.CACHE, "tormach-candidates.txt")
    urls = [u.strip() for u in open(cand) if u.strip()]
    out = []
    for u in urls:
        try:
            out.append(parse(u, fetch.fetch(u)))
        except Exception as e:  # noqa: BLE001
            print("ERR", u, e, file=sys.stderr)
            out.append({"url": u, "error": str(e)})
    p = os.path.join(fetch.CACHE, "tormach-products.json")
    with open(p, "w") as f:
        json.dump({"products": out, "stats": fetch.STATS}, f, indent=1)
    print(len(out), "pages", fetch.STATS)


if __name__ == "__main__":
    main()
