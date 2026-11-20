"""Polite cached fetcher: obeys robots.txt, <= 1 request/second, plain UA.

Usage as a module: fetch(url) -> str (HTML), cached under ../cache/<host>/.
Usage as a script:  python3 -I fetch.py URL [URL...]   (prints cache paths)
"""
import hashlib
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.robotparser

UA = "camcraft-tool-library-builder (personal use)"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.path.dirname(HERE), "cache")
_robots = {}
_last = [0.0]
STATS = {"fetched": 0, "cached": 0, "blocked": 0, "errors": 0}


def _rp(host):
    if host not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"https://{host}/robots.txt")
        _throttle()
        rp.read()
        _robots[host] = rp
    return _robots[host]


def _throttle():
    dt = time.time() - _last[0]
    if dt < 1.1:
        time.sleep(1.1 - dt)
    _last[0] = time.time()


def cache_path(url):
    u = urllib.parse.urlsplit(url)
    h = hashlib.sha1(url.encode()).hexdigest()[:16]
    slug = "".join(c if c.isalnum() else "_" for c in (u.path + "_" + u.query))[-80:]
    return os.path.join(CACHE, u.netloc, f"{slug}_{h}.html")


def fetch(url, refetch=False):
    p = cache_path(url)
    if os.path.exists(p) and not refetch:
        STATS["cached"] += 1
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    host = urllib.parse.urlsplit(url).netloc
    if not _rp(host).can_fetch(UA, url):
        STATS["blocked"] += 1
        raise PermissionError(f"robots.txt disallows {url}")
    _throttle()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", errors="replace")
    except Exception:
        STATS["errors"] += 1
        raise
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(body)
    STATS["fetched"] += 1
    return body


if __name__ == "__main__":
    for a in sys.argv[1:]:
        fetch(a)
        print(cache_path(a))
