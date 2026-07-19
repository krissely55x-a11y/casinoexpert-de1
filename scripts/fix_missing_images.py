#!/usr/bin/env python3
"""Download missing images and rewrite absolute URLs to local relative paths."""

import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from proxy_config import apply_proxy

TARGET_TS = "20260419042735"
DOMAIN = "onlinecasinoexperte.org"
WAYBACK = "https://web.archive.org/web"
ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "mirror"
REPORT = ROOT / "reports" / "site_verify_report.json"

SESSION = apply_proxy(__import__("requests").Session())
SESSION.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TS_MAP: dict[str, str] = {}


def load_ts():
    for cdx in [ROOT / "cdx_data.json", ROOT / "cdx_20260419.json"]:
        if not cdx.exists():
            continue
        for row in json.loads(cdx.read_text(encoding="utf-8"))[1:]:
            u = row[1].replace("http://", "https://").replace("www.", "")
            if row[0] > TS_MAP.get(u, ""):
                TS_MAP[u] = row[0]


def url_to_path(url: str) -> Path:
    path = urllib.parse.urlparse(url).path.lstrip("/")
    return SITE / path


def download(url: str) -> bool:
    dest = url_to_path(url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    ts = TS_MAP.get(url, TARGET_TS)
    wb = f"{WAYBACK}/{ts}id_/{url}"
    for attempt in range(4):
        try:
            r = SESSION.get(wb, timeout=60)
            if r.status_code in (429, 503):
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 200 and r.content and len(r.content) > 100:
                dest.write_bytes(r.content)
                return True
            break
        except Exception:
            time.sleep(1)
    return False


def collect_missing_images() -> set[str]:
    missing: set[str] = set()
    for html in SITE.rglob("*.html"):
        try:
            text = html.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in re.finditer(
            rf'(?:src|data-src|data-lazy-src|href|srcset)\s*=\s*["\']([^"\']+)["\']',
            text, re.I
        ):
            for part in m.group(1).split(","):
                ref = part.strip().split(" ")[0]
                if "onlinecasinoexperte.org/wp-content/uploads/" in ref or ref.startswith("/wp-content/uploads/"):
                    if ref.startswith("/"):
                        url = f"https://{DOMAIN}{ref.split('?')[0]}"
                    elif ref.startswith("http"):
                        url = ref.split("?")[0]
                    else:
                        continue
                    if not url_to_path(url).exists():
                        missing.add(url)
    return missing


def rewrite_absolute_urls() -> int:
    changed = 0
    for html in SITE.rglob("*.html"):
        try:
            text = html.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        orig = text

        def repl(m):
            url = m.group(0).split("?")[0]
            path = urllib.parse.urlparse(url).path.lstrip("/")
            target = SITE / path
            if target.exists():
                rel = os.path.relpath(target, html.parent).replace("\\", "/")
                return rel
            return m.group(0)

        text = re.sub(
            rf'https?://(?:www\.)?{re.escape(DOMAIN)}/wp-content/uploads/[^\s"\'<>\)]+',
            repl, text, flags=re.I
        )
        if text != orig:
            html.write_text(text, encoding="utf-8", errors="ignore")
            changed += 1
    return changed


def main():
    load_ts()
    missing = collect_missing_images()
    print(f"Missing upload images: {len(missing)}")

    ok = fail = 0
    for i, url in enumerate(sorted(missing), 1):
        if download(url):
            ok += 1
        else:
            fail += 1
        if i % 25 == 0 or i == len(missing):
            print(f"  {i}/{len(missing)} ok={ok} fail={fail}")
        time.sleep(0.1)

    print(f"\nRewriting absolute URLs...")
    fixed = rewrite_absolute_urls()
    print(f"Fixed {fixed} HTML files")

    still = collect_missing_images()
    report = {
        "missing_uploads_downloaded_ok": ok,
        "missing_uploads_failed": fail,
        "still_missing": len(still),
        "html_rewritten": fixed,
        "still_missing_samples": sorted(still)[:30],
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nStill missing: {len(still)}")


if __name__ == "__main__":
    main()
