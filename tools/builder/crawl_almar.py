"""Crawl Almar Tools' public WooCommerce product pages (from its sitemap).

Writes ../cache/almar-products.json: url, title, sku, attributes table,
and the short "Description" text (Almar's own part code, e.g.
4VX01250500A000). Run: python3 -I crawl_almar.py
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch  # noqa: E402

SITEMAP = "https://www.almartool.com/product-sitemap.xml"


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def parse(url, h):
    attrs = {}
    for m in re.finditer(r'(?is)<th class="woocommerce-product-attributes-item__label"[^>]*>(.*?)</th>\s*'
                         r'<td class="woocommerce-product-attributes-item__value">(.*?)</td>', h):
        attrs[clean(m.group(1))] = clean(m.group(2))
    title = ""
    tm = re.search(r'(?is)<h1[^>]*product_title[^>]*>(.*?)</h1>', h) or re.search(r"(?is)<h1[^>]*>(.*?)</h1>", h)
    if tm:
        title = clean(tm.group(1))
    sku = ""
    sm = re.search(r'(?is)class="sku"[^>]*>(.*?)<', h)
    if sm:
        sku = clean(sm.group(1))
    if not sku:
        sku = url.rstrip("/").rsplit("/", 1)[-1].upper()
    desc = ""
    dm = re.search(r'(?is)id="tab-description"[^>]*>(.*?)</div>', h)
    if dm:
        desc = clean(dm.group(1)).replace("Description", "").strip()
    return {"url": url, "title": title, "sku": sku, "attrs": attrs, "desc": desc}


def main():
    sm = fetch.fetch(SITEMAP)
    urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", sm) if "/product/" in u]
    out = []
    for u in urls:
        try:
            out.append(parse(u, fetch.fetch(u)))
        except Exception as e:  # noqa: BLE001
            print("ERR", u, e, file=sys.stderr)
    p = os.path.join(fetch.CACHE, "almar-products.json")
    with open(p, "w") as f:
        json.dump({"products": out, "stats": fetch.STATS}, f, indent=1)
    print(len(out), "products", fetch.STATS)


if __name__ == "__main__":
    main()
