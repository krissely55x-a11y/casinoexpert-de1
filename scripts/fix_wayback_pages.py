#!/usr/bin/env python3
"""Re-download pages that still contain Wayback Machine HTML."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import download_pages_crawl as crawl

SITE = Path(__file__).resolve().parent.parent / "mirror"


def page_to_url(rel: str) -> str:
    if rel == "index.html":
        return f"https://{crawl.DOMAIN}/"
    path = rel.replace("\\", "/").removesuffix("/index.html")
    return f"https://{crawl.DOMAIN}/{path}/"


def main():
    crawl.load_timestamp_map()

    bad = []
    for p in SITE.rglob("*.html"):
        head = p.read_bytes()[:3000].decode("utf-8", errors="ignore").lower()
        if "<title>wayback machine</title>" in head:
            bad.append(page_to_url(p.relative_to(SITE).as_posix()))

    print(f"Fixing {len(bad)} Wayback pages...")
    ok = fail = 0
    for url in bad:
        _, success = crawl.download_page(url)
        print(("OK" if success else "FAIL"), url)
        ok += int(success)
        fail += int(not success)
    print(f"Done: ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
