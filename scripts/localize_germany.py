#!/usr/bin/env python3
"""Apply the German locale and current editorial dates to generated sources."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRESH_DATE = "2026-07-20"
FRESH_TIMESTAMP = "2026-07-20T00:00:00+02:00"
VISIBLE_DATE = "20/07/2026"

REPLACEMENTS = (
    ("Österreicherinnen und Österreicher", "deutsche Spielerinnen und Spieler"),
    ("österreichischen Spielerinnen und Spielern", "deutschen Spielerinnen und Spielern"),
    ("Österreichischen Spielerinnen und Spielern", "Deutschen Spielerinnen und Spielern"),
    ("österreichischen Spielern", "deutschen Spielern"),
    ("Österreichischen Spielern", "Deutschen Spielern"),
    ("für Österreicher", "für deutsche Spieler"),
    ("Österreicher", "deutsche Spieler"),
    ("Österreichische", "Deutsche"),
    ("österreichische", "deutsche"),
    ("Österreichischen", "Deutschen"),
    ("österreichischen", "deutschen"),
    ("Österreichischer", "Deutscher"),
    ("österreichischer", "deutscher"),
    ("Österreichisches", "Deutsches"),
    ("österreichisches", "deutsches"),
    ("Österreichischem", "Deutschem"),
    ("österreichischem", "deutschem"),
    ("Österreichweit", "Deutschlandweit"),
    ("österreichweit", "deutschlandweit"),
    ("Österreich", "Deutschland"),
    ("österreich", "deutschland"),
    ("de_AT", "de_DE"),
    ("de-AT", "de-DE"),
)


def update_dates(text: str) -> str:
    text = re.sub(
        r"(letztes\s+Update\s+)\d{2}/\d{2}/\d{4}",
        rf"\g<1>{VISIBLE_DATE}",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"((?:Casino Erfahrungen|Casino Test|Casino Bonus Code)\s+)202[0-5]",
        rf"\g<1>2026",
        text,
        flags=re.IGNORECASE,
    )

    escaped_key = r'\\"date(?:Published|Modified|Created)\\":\\"'
    text = re.sub(
        rf"({escaped_key})\d{{4}}-\d{{2}}-\d{{2}}T.*?(?=\\\")",
        rf"\g<1>{FRESH_TIMESTAMP}",
        text,
    )
    plain_key = r'"date(?:Published|Modified|Created)":"'
    text = re.sub(
        rf"({plain_key})\d{{4}}-\d{{2}}-\d{{2}}T.*?(?=\")",
        rf"\g<1>{FRESH_TIMESTAMP}",
        text,
    )

    text = re.sub(
        r'(\\"datePublished\\":\\"[^"]+?\\")(?!,\\"dateCreated\\")',
        rf'\1,\\"dateCreated\\":\\"{FRESH_TIMESTAMP}\\"',
        text,
    )
    text = re.sub(
        r'("datePublished":"[^"]+?")(?!,"dateCreated")',
        rf'\1,"dateCreated":"{FRESH_TIMESTAMP}"',
        text,
    )
    return text


def localize(text: str) -> str:
    for source, target in REPLACEMENTS:
        text = text.replace(source, target)
    return update_dates(text)


def main() -> None:
    files = [
        path
        for path in (ROOT / "src").rglob("*")
        if path.is_file() and path.suffix in {".astro", ".html"}
    ]
    files.append(ROOT / "scripts" / "html_to_astro.py")

    changed = 0
    for path in files:
        before = path.read_text(encoding="utf-8")
        after = localize(before)
        if after == before:
            continue
        path.write_text(after, encoding="utf-8")
        changed += 1

    print(f"localize_germany: updated {changed} files for {FRESH_DATE}")


if __name__ == "__main__":
    main()
