#!/usr/bin/env python3
"""Download HTML pages only from Wayback Machine (parallel worker)."""

import json
import re
import sys
import time
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from proxy_config import apply_proxy

TARGET_TS = "20260419042735"
DOMAIN = "onlinecasinoexperte.org"
WAYBACK = "https://web.archive.org/web"
ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "mirror"
CDX_FILES = [ROOT / "cdx_data.json", ROOT / "cdx_20260419.json"]

SESSION = apply_proxy(requests.Session())
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
    return f"https://{host}{path}" + (f"?{parsed.query}" if parsed.query else "")


def is_wayback_page(content: bytes) -> bool:
    text = content[:4000].decode("utf-8", errors="ignore").lower()
    return "<title>wayback machine</title>" in text or "web-static.archive.org" in text


def url_to_local_path(url: str) -> Path:
    parsed = urllib.parse.urlparse(normalize_url(url))
    path = parsed.path or "/"
    if path.endswith("/") or not Path(path).suffix:
        return SITE_DIR / path.lstrip("/") / "index.html"
    return SITE_DIR / path.lstrip("/")


def wayback_raw(timestamp: str, original: str) -> str:
    return f"{WAYBACK}/{timestamp}id_/{normalize_url(original)}"


def is_html_url(url: str) -> bool:
    path = urllib.parse.urlparse(normalize_url(url)).path.lower()
    if path.endswith((".css", ".js", ".jpg", ".jpeg", ".png", ".gif", ".webp",
                      ".svg", ".woff", ".woff2", ".ttf", ".ico", ".xml", ".pdf",
                      ".mp4", ".webm", ".zip")):
        return False
    return True


def load_url_map() -> dict[str, str]:
    url_map: dict[str, str] = {}
    for cdx in CDX_FILES:
        if not cdx.exists():
            continue
        data = json.loads(cdx.read_text(encoding="utf-8"))
        for row in data[1:]:
            ts, original = row[0], row[1]
            u = normalize_url(original)
            if not is_html_url(u):
                continue
            if ts > url_map.get(u, ""):
                url_map[u] = ts

    # Prefer target snapshot for main sections
    for path in ["/"]:
        url_map[f"https://{DOMAIN}{path}"] = TARGET_TS

    return url_map


def needs_download(url: str) -> bool:
    dest = url_to_local_path(url)
    if not dest.exists():
        return True
    try:
        return is_wayback_page(dest.read_bytes())
    except Exception:
        return True


def download_page(url: str, timestamp: str) -> tuple[str, bool, str]:
    dest = url_to_local_path(url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    wb_url = wayback_raw(timestamp, url)

    for attempt in range(5):
        try:
            r = SESSION.get(wb_url, timeout=90)
            if r.status_code in (429, 503):
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 200 and r.content and not is_wayback_page(r.content):
                dest.write_bytes(r.content)
                return url, True, str(dest.relative_to(ROOT))
            break
        except Exception as exc:
            if attempt == 4:
                return url, False, str(exc)
            time.sleep(1)
    return url, False, "failed"


def main():
    shard = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    shards = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 6

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    url_map = load_url_map()
    pending = [(u, ts) for u, ts in sorted(url_map.items()) if needs_download(u)]

    # Split work across parallel agents
    pending = pending[shard::shards]

    print(f"[pages shard {shard+1}/{shards}] pending={len(pending)} workers={workers}")

    ok = fail = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(download_page, u, ts): u for u, ts in pending}
        for i, fut in enumerate(as_completed(futures), 1):
            url, success, info = fut.result()
            if success:
                ok += 1
            else:
                fail += 1
            if i % 25 == 0 or i == len(pending):
                print(f"  progress {i}/{len(pending)} ok={ok} fail={fail}")
            time.sleep(0.03)

    print(f"[pages shard {shard+1}/{shards}] done ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
