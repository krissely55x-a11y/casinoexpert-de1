#!/usr/bin/env python3
"""Discover and download missing pages via sitemap + internal link crawl."""

import json
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from proxy_config import apply_proxy

TARGET_TS = "20260419042735"
DOMAIN = "onlinecasinoexperte.org"
WAYBACK = "https://web.archive.org/web"
ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "mirror"

SESSION = apply_proxy(requests.Session())
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})


def normalize_url(url: str) -> str:
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    parsed = urllib.parse.urlparse(url)
    host = (parsed.netloc or DOMAIN).lower().replace("www.", "")
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return f"https://{host}{path}"


def is_wayback_page(content: bytes) -> bool:
    text = content[:4000].decode("utf-8", errors="ignore").lower()
    return "<title>wayback machine</title>" in text


def url_to_local(url: str) -> Path:
    path = urllib.parse.urlparse(normalize_url(url)).path or "/"
    if path.endswith("/") or not Path(path).suffix:
        return SITE_DIR / path.lstrip("/") / "index.html"
    return SITE_DIR / path.lstrip("/")


def is_page(url: str) -> bool:
    ext = Path(urllib.parse.urlparse(normalize_url(url)).path).suffix.lower()
    return ext in ("", ".html", ".htm", ".php")


def needs_download(url: str) -> bool:
    dest = url_to_local(url)
    if not dest.exists():
        return True
    try:
        return is_wayback_page(dest.read_bytes())
    except Exception:
        return True


def load_timestamp_map() -> dict[str, str]:
    ts_map: dict[str, str] = {}
    for cdx in [ROOT / "cdx_data.json", ROOT / "cdx_20260419.json"]:
        if not cdx.exists():
            continue
        data = json.loads(cdx.read_text(encoding="utf-8"))
        for row in data[1:]:
            ts, original = row[0], row[1]
            u = normalize_url(original)
            if ts > ts_map.get(u, ""):
                ts_map[u] = ts
    return ts_map


TIMESTAMP_MAP = {}


def get_timestamp(url: str) -> str:
    u = normalize_url(url)
    return TIMESTAMP_MAP.get(u, TARGET_TS)


def is_valid_page_url(url: str) -> bool:
    if not is_page(url):
        return False
    parsed = urllib.parse.urlparse(normalize_url(url))
    path = parsed.path or "/"
    if "//" in path:
        return False
    if any(x in path.lower() for x in (".googleapis.", "archive.org", "gravatar.com", "wp-json")):
        return False
    return True


def url_variants(url: str) -> list[str]:
    u = normalize_url(url)
    parsed = urllib.parse.urlparse(u)
    path = parsed.path or "/"
    variants = [u]
    if path != "/" and not path.endswith("/"):
        variants.append(f"https://{DOMAIN}{path}/")
    elif path.endswith("/") and path != "/":
        variants.append(f"https://{DOMAIN}{path.rstrip('/')}")
    return variants


def timestamps_for(url: str) -> list[str]:
    u = normalize_url(url)
    ts = sorted({TIMESTAMP_MAP.get(v, "") for v in url_variants(u) if TIMESTAMP_MAP.get(v)}, reverse=True)
    if TARGET_TS not in ts:
        ts.insert(0, TARGET_TS)
    return ts or [TARGET_TS]


def download_page(url: str, timestamp: str | None = None) -> tuple[str, bool]:
    if not is_valid_page_url(url):
        return url, False

    dest = url_to_local(url)
    dest.parent.mkdir(parents=True, exist_ok=True)

    ts_list = [timestamp] if timestamp else timestamps_for(url)
    for ts in ts_list:
        for variant in url_variants(url):
            wb = f"{WAYBACK}/{ts}id_/{variant}"
            for attempt in range(4):
                try:
                    r = SESSION.get(wb, timeout=90)
                    if r.status_code in (429, 503):
                        time.sleep(2 ** attempt)
                        continue
                    if r.status_code == 200 and r.content and not is_wayback_page(r.content):
                        dest.write_bytes(r.content)
                        TIMESTAMP_MAP[normalize_url(url)] = ts
                        return url, True
                    break
                except Exception:
                    time.sleep(1)
    return url, False


def parse_sitemap(path: Path) -> set[str]:
    urls: set[str] = set()
    try:
        root = ET.fromstring(path.read_bytes())
    except Exception:
        return urls
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    for loc in root.findall(".//sm:loc", ns):
        if loc.text and DOMAIN in loc.text:
            urls.add(normalize_url(loc.text))
    for loc in root.findall(".//loc"):
        if loc.text and DOMAIN in loc.text:
            urls.add(normalize_url(loc.text))
    return urls


def extract_links(path: Path) -> set[str]:
    urls: set[str] = set()
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return urls
    for m in re.finditer(rf'https?://(?:www\.)?{re.escape(DOMAIN)}/[^\s"\'<>\)]+', text, re.I):
        u = normalize_url(m.group(0).rstrip(".,;"))
        if is_valid_page_url(u):
            urls.add(u)
    for m in re.finditer(r'href=["\'](/[^"\']+)["\']', text):
        u = normalize_url(f"https://{DOMAIN}{m.group(1)}")
        if is_valid_page_url(u):
            urls.add(u)
    return urls


def fetch_cdx_pages() -> set[str]:
    urls: set[str] = set()
    api = (
        "https://web.archive.org/cdx/search/cdx"
        f"?url={DOMAIN}/*&matchType=domain&output=json"
        "&fl=original&filter=statuscode:200&collapse=urlkey&limit=10000"
    )
    try:
        data = SESSION.get(api, timeout=120).json()
        for row in data[1:]:
            u = normalize_url(row[0])
            if is_page(u):
                urls.add(u)
    except Exception:
        pass
    return urls


def discover_all() -> set[str]:
    found: set[str] = set()
    found.update(fetch_cdx_pages())
    for sm in SITE_DIR.rglob("*sitemap*.xml"):
        found.update(parse_sitemap(sm))
    for html in SITE_DIR.rglob("*.html"):
        found.update(extract_links(html))
    return {u for u in found if is_valid_page_url(u)}


def main():
    global TIMESTAMP_MAP
    TIMESTAMP_MAP = load_timestamp_map()

    shard = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    shards = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    all_urls = sorted(discover_all())
    pending = [u for u in all_urls if needs_download(u) and is_valid_page_url(u)]
    pending = pending[shard::shards]

    print(f"[crawl shard {shard+1}/{shards}] discovered={len(all_urls)} pending={len(pending)}")

    ok = fail = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(download_page, u): u for u in pending}
        for i, fut in enumerate(as_completed(futures), 1):
            _, success = fut.result()
            ok += 1 if success else 0
            fail += 0 if success else 1
            if i % 20 == 0 or i == len(pending):
                print(f"  {i}/{len(pending)} ok={ok} fail={fail}")
            time.sleep(0.15)

    print(f"[crawl shard {shard+1}/{shards}] done ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
