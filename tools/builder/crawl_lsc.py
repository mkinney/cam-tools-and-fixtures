"""Crawl Lake Shore Carbide's public category and product pages.

Writes ../cache/lsc-products.json: one record per product page with its
breadcrumb, title, part number and the spec table (header -> value).
Run: python3 -I crawl_lsc.py
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch  # noqa: E402

BASE = "https://www.lakeshorecarbide.com"
# Non-cutting-tool categories (workholding, accessories, bundles).
SKIP = {"/aluminumsoftjaws.aspx", "/lmdcoolantring.aspx", "/toolingpackages.aspx",
        "/6standardaluminumvisejaws.aspx"}
NOT_CONTENT = re.compile(r"(cart|login|register|history|password|checkout|about-us|contact-us|index|"
                         r"screenshare|testimonials|toolselector|needacustomtool|return-policy|"
                         r"technicalresources|videos|NYC-CNC|custom\.css)", re.I)


def text_of(h):
    t = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", "", h)
    t = re.sub(r"<[^>]+>", "|", t)
    t = html.unescape(t)
    return re.sub(r"\s*\|[\s|]*", "|", t)


def links(h):
    out = []
    for m in re.finditer(r'href="([^"]+\.aspx(?:\?page=\d+)?)"', h):
        u = m.group(1)
        u = re.sub(r"^https?://www\.lakeshorecarbide\.com", "", u)
        if not u.startswith("/"):
            u = "/" + u
        out.append(u)
    return out


def tables(h):
    """Every <table> as rows of cell text."""
    res = []
    for tm in re.finditer(r"(?is)<table.*?</table>", h):
        rows = []
        for rm in re.finditer(r"(?is)<tr.*?</tr>", tm.group(0)):
            cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip()
                     for c in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", rm.group(0))]
            if any(cells):
                rows.append(cells)
        if rows:
            res.append(rows)
    return res


def parse_product(url, h):
    t = text_of(h)
    pn = re.search(r"\|Part Number:\|([^|]+)\|", t)
    crumb = ""
    m = re.search(r"\|Home\|>\|(.*?)\|(?=[^>|][^|]*\|[^>])", t)
    bc = re.search(r"Screen Share\|Home\|>\|(.*?)\|Next in|Screen Share\|Home\|>\|(.*?)\|Your Price", t)
    if bc:
        crumb = (bc.group(1) or bc.group(2) or "")
    title = ""
    tm = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", h)
    if tm:
        title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", tm.group(1)))).strip()
    spec = {}
    for rows in tables(h):
        # The spec table: a header row of names, then one value row.
        if len(rows) >= 2 and len(rows[0]) == len(rows[1]) and len(rows[0]) >= 2 \
                and any("Diameter" in c or "Dia" in c or "Length" in c for c in rows[0]):
            spec = dict(zip(rows[0], rows[1]))
            break
    # Fallback: the pipe text "Diameter|Flute Length|...|v1|v2|..."
    if not spec:
        sm = re.search(r"\|((?:[A-Za-z][A-Za-z .#/()]*\|){2,10})((?:[^|]{1,20}\|){2,10})Product Reviews", t)
        if sm:
            ks = sm.group(1).strip("|").split("|")
            vs = sm.group(2).strip("|").split("|")
            if len(ks) == len(vs):
                spec = dict(zip(ks, vs))
    desc = ""
    dm = re.search(r"Email this page to a friend\|(.*?)\|(?:Diameter|Product Reviews)", t)
    if dm:
        desc = dm.group(1)
    return {"url": BASE + url, "crumb": crumb, "title": title,
            "part": pn.group(1).strip() if pn else "", "spec": spec, "desc": desc}


def main():
    home = fetch.fetch(BASE + "/")
    nav = set(links(home))
    start = [u for u in sorted(nav) if not NOT_CONTENT.search(u) and u not in SKIP]
    seen, queue, products, cats = set(), list(start), [], []
    while queue:
        u = queue.pop(0)
        if u in seen or u in SKIP or NOT_CONTENT.search(u):
            continue
        seen.add(u)
        try:
            h = fetch.fetch(BASE + u)
        except Exception as e:  # noqa: BLE001
            print("ERR", u, e, file=sys.stderr)
            continue
        if "Part Number:" in h and "Displaying products" not in h:
            products.append(parse_product(u, h))
            continue
        cats.append(u)
        for v in links(h):
            if v not in nav and v not in seen and not NOT_CONTENT.search(v):
                queue.append(v)
    out = os.path.join(fetch.CACHE, "lsc-products.json")
    with open(out, "w") as f:
        json.dump({"categories": cats, "products": products, "stats": fetch.STATS}, f, indent=1)
    print(len(cats), "category pages,", len(products), "products", fetch.STATS)


if __name__ == "__main__":
    main()
