#!/usr/bin/env python3
"""Restore valid mirrored HTML pages over Wayback placeholder responses."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent
BACKUP = ROOT / "archive" / "wayback-versiya-vp.zip"
MIRROR = ROOT / "mirror"
CDX_DATA = ROOT / "reports" / "cdx_data.json"
SKIP_PREFIXES = (
    "wp-admin/",
    "wp-content/",
    "wp-includes/",
    "wp-json/",
)


def is_wayback_junk(data: bytes) -> bool:
    return b"<title>wayback machine</title>" in data[:5000].lower()


def route_for_file(path: Path) -> str:
    relative = path.relative_to(MIRROR).as_posix()
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return f"/{relative[:-10].rstrip('/')}/"
    return f"/{relative}"


def download_remaining_placeholders() -> tuple[int, int]:
    if not CDX_DATA.is_file():
        return 0, 0

    rows = json.loads(CDX_DATA.read_text(encoding="utf-8"))[1:]
    snapshots: dict[str, tuple[str, str]] = {}
    for timestamp, original, status, mime in rows:
        if status != "200" or mime != "text/html":
            continue
        parsed = urlparse(original)
        route = parsed.path or "/"
        if not route.endswith("/") and "." not in route.rsplit("/", 1)[-1]:
            route += "/"
        current = snapshots.get(route)
        if current is None or timestamp > current[0]:
            snapshots[route] = (timestamp, original)

    downloaded = failed = 0
    for destination in MIRROR.rglob("*.html"):
        if not is_wayback_junk(destination.read_bytes()):
            continue
        snapshot = snapshots.get(route_for_file(destination))
        if snapshot is None:
            failed += 1
            continue
        timestamp, original = snapshot
        archive_url = f"https://web.archive.org/web/{timestamp}id_/{original}"
        try:
            request = Request(archive_url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=45) as response:
                data = response.read()
            if is_wayback_junk(data) or b"<main" not in data.lower():
                failed += 1
                continue
            destination.write_bytes(data)
            downloaded += 1
        except Exception:
            failed += 1
    return downloaded, failed


def main() -> None:
    if not BACKUP.is_file():
        raise SystemExit(f"Backup not found: {BACKUP}")

    restored = 0
    added = 0
    with ZipFile(BACKUP) as archive:
        for member in archive.infolist():
            name = member.filename.replace("\\", "/")
            if not name.startswith("site/") or not name.endswith(".html"):
                continue
            relative = PurePosixPath(name).relative_to("site")
            relative_text = relative.as_posix()
            if relative_text.startswith(SKIP_PREFIXES):
                continue

            backup_data = archive.read(member)
            if is_wayback_junk(backup_data):
                continue

            destination = MIRROR.joinpath(*relative.parts)
            if destination.is_file():
                current_data = destination.read_bytes()
                if not is_wayback_junk(current_data):
                    continue
                restored += 1
            else:
                added += 1

            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(backup_data)

    downloaded, failed = download_remaining_placeholders()
    print(
        "restore_wayback_pages: "
        f"restored {restored}, added {added}, downloaded {downloaded}, unresolved {failed}"
    )


if __name__ == "__main__":
    main()
