#!/usr/bin/env python3
"""Download and localize onlinecasinoexperte.org from Wayback Machine."""

import json
import os
import re
import time
import warnings
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from proxy_config import apply_proxy

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

TARGET_TS = "20260419042735"
DOMAIN = "onlinecasinoexperte.org"
WAYBACK = "https://web.archive.org/web"
ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "mirror"

SESSION = apply_proxy(requests.Session())
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

DOWNLOADED: set[str] = set()
FAILED: list[tuple[str, str]] = []
URL_TO_LOCAL: dict[str, Path] = {}


def normalize_url(url: str) -> str:
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    parsed = urllib.parse.urlparse(url)
    host = (parsed.netloc or DOMAIN).lower().replace("www.", "")
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    scheme = parsed.scheme or "https"
    return f"{scheme}://{host}{path}" + (f"?{parsed.query}" if parsed.query else "")


def is_internal(url: str) -> bool:
    if not url or url.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return False
    if "%3C" in url or "<svg" in url.lower():
        return False
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{DOMAIN}{url}")
    host = (parsed.netloc or DOMAIN).lower().replace("www.", "")
    if host != DOMAIN:
        return False
    path = parsed.path or "/"
    if any(c in path for c in '<>:"|?*'):
        return False
    return True


def strip_wayback(url: str) -> str:
    m = re.search(r"web\.archive\.org/web/\d+(?:id_)?/(.+)", url, re.I)
    return urllib.parse.unquote(m.group(1)) if m else url


def is_wayback_page(content: bytes) -> bool:
    text = content[:4000].decode("utf-8", errors="ignore").lower()
    return "<title>wayback machine</title>" in text or "web-static.archive.org" in text


def url_to_local_path(url: str) -> Path:
    url = normalize_url(strip_wayback(url))
    parsed = urllib.parse.urlparse(url)
    path = parsed.path or "/"
    if path.endswith("/"):
        return SITE_DIR / path.lstrip("/") / "index.html"
    if not Path(path).suffix:
        return SITE_DIR / path.lstrip("/") / "index.html"
    return SITE_DIR / path.lstrip("/")


def wayback_raw(timestamp: str, original: str) -> str:
    original = normalize_url(original)
    return f"{WAYBACK}/{timestamp}id_/{original}"


def download_one(original: str, timestamp: str = TARGET_TS, force: bool = False) -> Path | None:
    original = normalize_url(original)
    dest = url_to_local_path(original)
    if original in DOWNLOADED and dest.exists() and not force:
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    url = wayback_raw(timestamp, original)

    for attempt in range(5):
        try:
            r = SESSION.get(url, timeout=90)
            if r.status_code in (429, 503):
                time.sleep(2 ** attempt)
                continue
            if r.status_code != 200 or not r.content:
                break
            if is_wayback_page(r.content):
                break
            dest.write_bytes(r.content)
            DOWNLOADED.add(original)
            URL_TO_LOCAL[original] = dest
            return dest
        except Exception as exc:
            if attempt == 4:
                FAILED.append((original, str(exc)))
            time.sleep(1)
    FAILED.append((original, "download failed"))
    return None


def fetch_cdx(prefix: str, closest: str | None = None) -> list[tuple[str, str]]:
    params = (
        f"url={urllib.parse.quote(prefix, safe='')}"
        "&output=json&fl=timestamp,original&filter=statuscode:200&collapse=urlkey&limit=10000"
    )
    if closest:
        params += f"&closest={closest}"
    else:
        params += "&matchType=domain"
    try:
        r = SESSION.get(f"https://web.archive.org/cdx/search/cdx?{params}", timeout=120)
        data = r.json()
        return [(row[0], row[1]) for row in data[1:]]
    except Exception:
        return []


def collect_page_urls() -> dict[str, str]:
    url_map: dict[str, str] = {}

    for ts, original in fetch_cdx(f"{DOMAIN}/*"):
        u = normalize_url(original)
        if ts > url_map.get(u, ""):
            url_map[u] = ts

    # Force homepage and key pages to target snapshot
    for path in ["/", "/bonus/", "/casinos/", "/slots/", "/ratgeber/", "/kontakt/",
                 "/impressum/", "/datenschutz/", "/haftungsausschluss/"]:
        url_map[f"https://{DOMAIN}{path}"] = TARGET_TS

    return url_map


def extract_assets(content: bytes, base_url: str) -> set[str]:
    assets: set[str] = set()
    text = content.decode("utf-8", errors="ignore")

    for match in re.finditer(r"""url\s*\(\s*['"]?([^'")\s]+)['"]?\s*\)""", text):
        u = urllib.parse.urljoin(base_url, match.group(1))
        if is_internal(u):
            assets.add(normalize_url(strip_wayback(u)))

    soup = BeautifulSoup(content, "lxml")
    for tag, attr in [
        ("link", "href"), ("script", "src"), ("img", "src"),
        ("img", "data-src"), ("img", "data-lazy-src"), ("source", "srcset"),
        ("source", "src"), ("video", "poster"), ("a", "href"),
    ]:
        for el in soup.find_all(tag):
            val = el.get(attr)
            if not val:
                continue
            for part in val.split(","):
                u = part.strip().split(" ")[0]
                u = urllib.parse.urljoin(base_url, u)
                if is_internal(u):
                    assets.add(normalize_url(strip_wayback(u)))

    for match in re.finditer(
        rf'https?://(?:www\.)?{re.escape(DOMAIN)}/[^\s"\'<>\)]+', text, re.I
    ):
        u = normalize_url(match.group(0).rstrip(".,;"))
        if is_internal(u):
            assets.add(u)

    return assets


def download_pages(url_map: dict[str, str]) -> None:
    print(f"Phase 1: downloading {len(url_map)} pages...")
    items = sorted(url_map.items())
    done = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(download_one, url, ts): url
            for url, ts in items
        }
        for fut in as_completed(futures):
            done += 1
            if done % 100 == 0:
                print(f"  pages: {done}/{len(items)}")
            time.sleep(0.05)


def download_assets(max_rounds: int = 3) -> None:
    for round_num in range(1, max_rounds + 1):
        pending: set[str] = set()
        for path in SITE_DIR.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in (".html", ".htm", ".css", ".js", ".php", ".xml", ""):
                continue
            try:
                content = path.read_bytes()
            except Exception:
                continue
            if is_wayback_page(content):
                continue
            rel = "/" + str(path.relative_to(SITE_DIR)).replace("\\", "/")
            if rel.endswith("/index.html"):
                base = f"https://{DOMAIN}{rel[:-10]}/"
            else:
                base = f"https://{DOMAIN}{rel}"
            for asset in extract_assets(content, base):
                dest = url_to_local_path(asset)
                if not dest.exists():
                    pending.add(asset)

        if not pending:
            print(f"Phase 2 round {round_num}: no new assets")
            break

        pending = {a for a in pending if is_internal(a) and not a.endswith("/")}
        print(f"Phase 2 round {round_num}: downloading {len(pending)} assets...")
        done = 0
        for asset in sorted(pending):
            if not is_internal(asset):
                continue
            download_one(asset, TARGET_TS)
            done += 1
            if done % 50 == 0:
                print(f"  assets: {done}/{len(pending)}")
            time.sleep(0.08)


def rel_link(from_file: Path, target: Path) -> str:
    rel = os.path.relpath(target, from_file.parent).replace("\\", "/")
    return rel


def rewrite_file(path: Path) -> None:
    try:
        raw = path.read_bytes()
    except Exception:
        return
    if is_wayback_page(raw):
        return

    text = raw.decode("utf-8", errors="ignore")
    original = text

    # Remove wayback injections
    text = re.sub(r'<script[^>]*archive\.org[^>]*>.*?</script>', '', text, flags=re.S | re.I)
    text = re.sub(r'<link[^>]*archive\.org[^>]*/?>', '', text, flags=re.I)
    text = re.sub(r'<!-- BEGIN WAYBACK.*?END WAYBACK -->', '', text, flags=re.S | re.I)
    text = re.sub(r'<div[^>]*id="wm-[^"]*"[^>]*>.*?</div>', '', text, flags=re.S | re.I)

    def to_local(full_url: str) -> str:
        full_url = strip_wayback(full_url)
        if not is_internal(full_url):
            return full_url
        target = url_to_local_path(full_url)
        if target.exists():
            return rel_link(path, target)
        # fallback root-relative
        rel = "/" + str(target.relative_to(SITE_DIR)).replace("\\", "/")
        if rel.endswith("/index.html"):
            rel = rel[:-10] or "/"
        return rel

    text = re.sub(
        r'(?:https?:)?//web\.archive\.org/web/\d+(?:id_)?/((?:https?://)?[^"\')\s]+)',
        lambda m: to_local(m.group(1)),
        text,
        flags=re.I,
    )

    text = re.sub(
        rf'https?://(?:www\.)?{re.escape(DOMAIN)}([^"\')\s>]*)',
        lambda m: to_local(f"https://{DOMAIN}{m.group(1)}"),
        text,
        flags=re.I,
    )

    text = re.sub(
        rf'//(?:www\.)?{re.escape(DOMAIN)}([^"\')\s>]*)',
        lambda m: to_local(f"https://{DOMAIN}{m.group(1)}"),
        text,
        flags=re.I,
    )

    if text != original:
        path.write_text(text, encoding="utf-8", errors="ignore")


def rewrite_all() -> None:
    print("Phase 3: rewriting links...")
    exts = {".html", ".htm", ".css", ".js", ".php", ".xml", ".svg"}
    n = 0
    for path in SITE_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in exts:
            rewrite_file(path)
            n += 1
    print(f"  processed {n} files")


def rebuild_url_map_from_disk() -> None:
    for path in SITE_DIR.rglob("*"):
        if path.is_file():
            rel = "/" + str(path.relative_to(SITE_DIR)).replace("\\", "/")
            if rel.endswith("/index.html"):
                url = f"https://{DOMAIN}{rel[:-10]}/"
            else:
                url = f"https://{DOMAIN}{rel}"
            URL_TO_LOCAL[normalize_url(url)] = path


def main():
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    rebuild_url_map_from_disk()

    # Always re-fetch homepage with correct snapshot
    print("Re-downloading homepage from target snapshot...")
    download_one(f"https://{DOMAIN}/", TARGET_TS, force=True)

    url_map = collect_page_urls()
    # Skip already downloaded pages unless wayback junk
    filtered = {}
    for url, ts in url_map.items():
        dest = url_to_local_path(url)
        if dest.exists():
            try:
                if not is_wayback_page(dest.read_bytes()):
                    continue
            except Exception:
                pass
        filtered[url] = ts

    if filtered:
        download_pages(filtered)

    download_assets(max_rounds=4)
    rebuild_url_map_from_disk()
    rewrite_all()

    manifest = {
        "downloaded_count": len(list(SITE_DIR.rglob('*'))),
        "failed": len(FAILED),
        "target_snapshot": TARGET_TS,
    }
    (ROOT / "reports" / "download_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if FAILED:
        (ROOT / "download_failed.json").write_text(
            json.dumps(FAILED[:300], indent=2, ensure_ascii=False), encoding="utf-8"
        )
    print(f"\nDone. Files: {manifest['downloaded_count']}, Failed: {len(FAILED)}")


if __name__ == "__main__":
    main()
