#!/usr/bin/env python3
"""Check all image/asset refs resolve to local files; report and fix."""

import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "mirror"
REPORT = ROOT / "reports" / "site_verify_report.json"


def resolve_ref(ref: str, page: Path) -> Path | None:
    ref = ref.strip().strip("'\"")
    if not ref or ref.startswith(("data:", "mailto:", "tel:", "javascript:", "#", "blob:", "http://", "https://", "//")):
        if ref.startswith(("http://", "https://")) and "onlinecasinoexperte.org" in ref:
            path = urllib.parse.urlparse(ref).path.lstrip("/")
            return SITE / path if path else None
        return None
    if ref.startswith("/"):
        return SITE / ref.lstrip("/")
    return (page.parent / ref).resolve()


def is_image_ref(ref: str) -> bool:
    ref = ref.lower().split("?")[0]
    return any(ref.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico"))


def scan_pages() -> dict:
    broken = []
    ok_count = 0
    img_total = 0

    for html in SITE.rglob("*.html"):
        try:
            text = html.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        refs = set()
        for m in re.finditer(r'(?:src|data-src|data-lazy-src|srcset|href)\s*=\s*["\']([^"\']+)["\']', text, re.I):
            val = m.group(1)
            if "srcset" in m.group(0):
                for part in val.split(","):
                    refs.add(part.strip().split(" ")[0])
            else:
                refs.add(val)

        for ref in refs:
            if not is_image_ref(ref):
                continue
            img_total += 1
            target = resolve_ref(ref, html)
            if target and target.exists() and target.stat().st_size > 0:
                ok_count += 1
            else:
                broken.append({
                    "page": str(html.relative_to(SITE)),
                    "ref": ref,
                    "expected": str(target.relative_to(SITE)) if target else None,
                })

    return {"images_total": img_total, "images_ok": ok_count, "broken": broken}


def fix_root_relative_paths() -> int:
    """Ensure subpages use correct relative paths to wp-content."""
    changed = 0
    for html in SITE.rglob("*.html"):
        if html.parent == SITE:
            continue
        try:
            text = html.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        orig = text

        def fix(m):
            attr, val = m.group(1), m.group(2)
            if val.startswith(("http", "data:", "//", "/")):
                return m.group(0)
            target = resolve_ref(val, html)
            if target and target.exists():
                return m.group(0)
            # try as site-root relative
            root_target = SITE / val
            if root_target.exists():
                rel = os.path.relpath(root_target, html.parent).replace("\\", "/")
                return f'{attr}="{rel}"'
            return m.group(0)

        text = re.sub(
            r'(src|data-src|data-lazy-src|href)\s*=\s*["\']([^"\']+)["\']',
            fix, text, flags=re.I
        )
        if text != orig:
            html.write_text(text, encoding="utf-8", errors="ignore")
            changed += 1
    return changed


def main():
    print("Fixing root-relative image paths on subpages...")
    fixed = fix_root_relative_paths()
    print(f"Fixed {fixed} pages")

    print("Scanning image references...")
    result = scan_pages()
    broken = result["broken"]
    print(f"Images: {result['images_ok']}/{result['images_total']} OK")
    print(f"Broken: {len(broken)}")

    report = {
        "images_total": result["images_total"],
        "images_ok": result["images_ok"],
        "images_broken": len(broken),
        "pages_fixed": fixed,
        "total_files": sum(1 for p in SITE.rglob("*") if p.is_file()),
        "broken_samples": broken[:50],
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Report: {REPORT}")

    if broken:
        print("\nSample broken:")
        for b in broken[:10]:
            print(f"  {b['page']} -> {b['ref']}")


if __name__ == "__main__":
    main()
