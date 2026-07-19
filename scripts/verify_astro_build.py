#!/usr/bin/env python3
"""Verify Astro build output against site_structure.json."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
STRUCTURE = ROOT / "reports" / "site_structure.json"


def dist_url(path: Path) -> str:
    rel = path.relative_to(DIST).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[:-10].rstrip("/") + "/"
    return "/" + rel


def urls_from_site_mirror() -> set[str]:
    expected: set[str] = set()
    for p in (ROOT / "mirror").rglob("index.html"):
        rel = p.relative_to(ROOT / "mirror").as_posix()
        if rel.startswith("wp-json/"):
            continue
        head = p.read_bytes()[:3000].decode("utf-8", errors="ignore").lower()
        if "<title>wayback machine</title>" in head:
            continue
        if rel == "index.html":
            expected.add("/")
        else:
            expected.add("/" + rel[:-10].rstrip("/") + "/")
    return expected


def main() -> None:
    if not DIST.exists():
        raise SystemExit(f"Missing dist folder: {DIST}")

    built = set()
    for p in DIST.rglob("*.html"):
        if "404" in p.name:
            continue
        built.add(dist_url(p))

    expected = urls_from_site_mirror()

    missing = sorted(expected - built)
    extra = sorted(built - expected - {"/404/"})

    print(f"Built pages: {len(built)}")
    print(f"Expected (site mirror): {len(expected)}")
    print(f"Missing from dist: {len(missing)}")
    print(f"Extra in dist: {len(extra)}")
    if missing:
        print("Sample missing:", missing[:15])
    if extra:
        print("Sample extra:", extra[:15])

    report = {
        "built": len(built),
        "expected": len(expected),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "missing": missing[:100],
        "extra": extra[:100],
    }
    out = ROOT / "reports" / "astro_build_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Report: {out}")


if __name__ == "__main__":
    main()
