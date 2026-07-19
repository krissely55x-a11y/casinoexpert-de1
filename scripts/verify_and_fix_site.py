#!/usr/bin/env python3
"""Verify and fix missing images/assets across the local site mirror."""

import json
import os
import re
import sys
import time
import warnings
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from proxy_config import apply_proxy

TARGET_TS = "20260419042735"
DOMAIN = "onlinecasinoexperte.org"
ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "mirror"
REPORT = ROOT / "reports" / "site_verify_report.json"
WAYBACK = "https://web.archive.org/web"

ASSET_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico", ".css", ".js",
              ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".webm", ".pdf"}

SESSION = apply_proxy(requests.Session())
SESSION.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TS_MAP: dict[str, str] = {}


def load_ts_map() -> None:
    for cdx in [ROOT / "cdx_data.json", ROOT / "cdx_20260419.json"]:
        if not cdx.exists():
            continue
        for row in json.loads(cdx.read_text(encoding="utf-8"))[1:]:
            u = clean_url(row[1])
            if u and row[0] > TS_MAP.get(u, ""):
                TS_MAP[u] = row[0]


def clean_url(url: str, base: str = f"https://{DOMAIN}/") -> str | None:
    if not url:
        return None
    url = url.strip().strip("'\"")
    if url.startswith(("data:", "mailto:", "tel:", "javascript:", "#", "blob:")):
        return None
    if "location.href" in url or "client_data/" in url:
        return None

    # Resolve relative ../ paths
    if url.startswith("../") or url.startswith("./"):
        url = urllib.parse.urljoin(base, url)

    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = f"https://{DOMAIN}{url}"
    elif not url.startswith("http"):
        url = urllib.parse.urljoin(base, url)

    # Extract wp-content/wp-includes from messy paths
    if "/wp-content/" in url or "/wp-includes/" in url:
        m = re.search(r"(/wp-(?:content|includes)/.+)", url)
        if m:
            path = m.group(1).split('"')[0].split("'")[0].rstrip(".,;)\\")
            path = re.sub(r"\\/", "/", path)
            parts = []
            for seg in path.split("/"):
                if seg == "..":
                    if parts:
                        parts.pop()
                elif seg and seg != ".":
                    parts.append(seg)
            path = "/" + "/".join(parts)
            url = f"https://{DOMAIN}{path}"

    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower().replace("www.", "")
    if host != DOMAIN:
        return None

    path = parsed.path or "/"
    path = re.sub(r"/+", "/", path)
    # Fix common wrong prefixes
    path = path.replace("/plugins/", "/wp-content/plugins/")
    path = path.replace("/themes/", "/wp-content/themes/")

    if any(c in path for c in '<>:"|?*') or "%3C" in path:
        return None

    # Drop query for asset identity
    return f"https://{DOMAIN}{path}"


def is_asset(url: str) -> bool:
    if not url:
        return False
    path = urllib.parse.urlparse(url).path.lower()
    ext = Path(path).suffix
    if ext in ASSET_EXTS:
        return True
    return "/wp-content/" in path or "/wp-includes/" in path or "/css/" in path or "/images/" in path


def local_path(url: str) -> Path:
    path = urllib.parse.urlparse(clean_url(url) or url).path.lstrip("/")
    return SITE_DIR / path


def extract_from_text(text: str, base: str) -> set[str]:
    refs: set[str] = set()

    patterns = [
        r'(?:src|href|data-src|data-lazy-src|data-rocket-src|poster)\s*=\s*["\']([^"\']+)["\']',
        r'url\s*\(\s*["\']?([^"\')\s]+)["\']?\s*\)',
        r'srcset\s*=\s*["\']([^"\']+)["\']',
        rf'//(?:www\.)?{re.escape(DOMAIN)}/[^\s"\'<>\)]+',
        rf'https?://(?:www\.)?{re.escape(DOMAIN)}/[^\s"\'<>\)]+',
        r'/wp-content/[^\s"\'<>\)]+\.(?:jpg|jpeg|png|gif|webp|svg|css|js|woff2?|ico)',
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.I):
            raw = m.group(1) if m.lastindex else m.group(0)
            if "," in raw and "srcset" in pat:
                for part in raw.split(","):
                    u = clean_url(part.strip().split(" ")[0], base)
                    if u and is_asset(u):
                        refs.add(u)
            else:
                u = clean_url(raw.rstrip(".,;)"), base)
                if u and is_asset(u):
                    refs.add(u)
    return refs


def scan_missing() -> set[str]:
    missing: set[str] = set()
    for f in SITE_DIR.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in (".html", ".htm", ".css", ".js", ".php", ".xml"):
            continue
        base = f"https://{DOMAIN}/" + str(f.parent.relative_to(SITE_DIR)).replace("\\", "/").rstrip("/") + "/"
        if base.endswith("/./"):
            base = f"https://{DOMAIN}/"
        try:
            refs = extract_from_text(f.read_text(encoding="utf-8", errors="ignore"), base)
        except Exception:
            continue
        for ref in refs:
            lp = local_path(ref)
            if not lp.exists() or lp.stat().st_size == 0:
                missing.add(ref)
    return missing


def fetch_wpcontent_cdx() -> set[str]:
    urls: set[str] = set()
    for prefix in [f"{DOMAIN}/wp-content/*", f"{DOMAIN}/wp-includes/*"]:
        api = (
            "https://web.archive.org/cdx/search/cdx"
            f"?url={prefix}&output=json&fl=original&filter=statuscode:200"
            "&collapse=urlkey&limit=10000"
        )
        try:
            for row in SESSION.get(api, timeout=120).json()[1:]:
                u = clean_url(row[0])
                if u and is_asset(u):
                    urls.add(u)
        except Exception:
            pass
    return urls


def download(url: str) -> bool:
    u = clean_url(url)
    if not u:
        return False
    dest = local_path(u)
    dest.parent.mkdir(parents=True, exist_ok=True)
    ts = TS_MAP.get(u, TARGET_TS)
    wb = f"{WAYBACK}/{ts}id_/{u}"
    for attempt in range(4):
        try:
            r = SESSION.get(wb, timeout=60)
            if r.status_code in (429, 503):
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 200 and r.content and len(r.content) > 20:
                dest.write_bytes(r.content)
                return True
            break
        except Exception:
            time.sleep(1)
    return False


def download_batch(urls: set[str], workers: int = 3) -> tuple[int, int]:
    ok = fail = 0
    items = sorted(urls)
    for i, url in enumerate(items, 1):
        if download(url):
            ok += 1
        else:
            fail += 1
        if i % 50 == 0 or i == len(items):
            print(f"  {i}/{len(items)} ok={ok} fail={fail}")
        time.sleep(0.12)
    return ok, fail


def fix_html_links() -> int:
    changed = 0
    for f in SITE_DIR.rglob("*.html"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        orig = text
        base = f"https://{DOMAIN}/" + str(f.parent.relative_to(SITE_DIR)).replace("\\", "/").rstrip("/") + "/"

        def fix_attr(m):
            attr, val = m.group(1), m.group(2)
            u = clean_url(val, base)
            if not u or not is_asset(u):
                return m.group(0)
            lp = local_path(u)
            if lp.exists():
                rel = os.path.relpath(lp, f.parent).replace("\\", "/")
                return f'{attr}="{rel}"'
            return m.group(0)

        text = re.sub(
            r'(src|href|data-src|data-lazy-src|data-rocket-src|poster)\s*=\s*["\']([^"\']+)["\']',
            fix_attr, text, flags=re.I
        )

        def fix_css_url(m):
            u = clean_url(m.group(1), base)
            if u and is_asset(u):
                lp = local_path(u)
                if lp.exists():
                    rel = os.path.relpath(lp, f.parent).replace("\\", "/")
                    return f"url({rel})"
            return m.group(0)

        text = re.sub(r'url\s*\(\s*["\']?([^"\')\s]+)["\']?\s*\)', fix_css_url, text, flags=re.I)

        if text != orig:
            f.write_text(text, encoding="utf-8", errors="ignore")
            changed += 1
    return changed


def main():
    load_ts_map()
    print("=== Scan HTML/CSS for missing assets ===")
    missing = scan_missing()
    print(f"Missing from pages: {len(missing)}")

    print("=== Fetch wp-content list from CDX ===")
    cdx_assets = fetch_wpcontent_cdx()
    cdx_missing = {u for u in cdx_assets if not local_path(u).exists()}
    print(f"CDX wp-content total: {len(cdx_assets)}, not local: {len(cdx_missing)}")

    to_get = missing | cdx_missing
    ok = fail = 0
    if to_get:
        print(f"\n=== Downloading {len(to_get)} assets ===")
        ok, fail = download_batch(to_get)

        extra = scan_missing() - to_get
        if extra:
            print(f"\n=== Pass 2: {len(extra)} ===")
            o2, f2 = download_batch(extra)
            ok += o2
            fail += f2

    print("\n=== Fix links in HTML ===")
    fixed = fix_html_links()

    still_missing = scan_missing()
    report = {
        "missing": len(still_missing),
        "downloaded_ok": ok,
        "downloaded_fail": fail,
        "html_fixed": fixed,
        "total_files": sum(1 for p in SITE_DIR.rglob("*") if p.is_file()),
        "missing_samples": sorted(still_missing)[:30],
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n=== FINAL ===")
    print(f"Files: {report['total_files']}")
    print(f"Downloaded ok={ok} fail={fail}")
    print(f"Still missing: {len(still_missing)}")
    print(f"HTML fixed: {fixed}")


if __name__ == "__main__":
    main()
