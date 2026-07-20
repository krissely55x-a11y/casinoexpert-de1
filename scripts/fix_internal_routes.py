#!/usr/bin/env python3
"""Repair legacy root-relative links using the generated Astro route map."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "src" / "pages"

MANUAL = {
    "/http://integriert/": "/strategien/poker/squeeze-play/",
    "/http://casinos/": "/casinos/",
    "/einzahlungsbonus/index.html": "/bonus/einzahlungsbonus/",
    "/freispiele/index.html": "/bonus/freispiele/",
    "/ohne-einzahlung/index.html": "/bonus/ohne-einzahlung/",
    "/d-alembert/": "/strategien/roulette/d-alembert/",
    "/blackjack/": "/strategien/blackjack/",
    "/3/": "/ueber-uns/juergen/",
    "/8/": "/ueber-uns/juergen/",
    "/page/21/": "/ueber-uns/tobias/",
    "/page/22/": "/ueber-uns/tobias/",
}


def route_for_page(path: Path) -> str:
    relative = path.relative_to(PAGES).as_posix()
    if relative == "index.astro":
        return "/"
    return f"/{relative.removesuffix('index.astro')}"


def main() -> None:
    routes = {route_for_page(path) for path in PAGES.rglob("index.astro")}
    replacements = dict(MANUAL)

    referenced: set[str] = set()
    bodies = list(PAGES.rglob("_body.html"))
    for path in bodies:
        text = path.read_text(encoding="utf-8")
        referenced.update(re.findall(r'href="(/[^"#?]*)', text, flags=re.IGNORECASE))

    for href in referenced:
        if href in routes or href.startswith(("/go/", "/wp-content/")):
            continue
        candidates = [route for route in routes if route.endswith(href)]
        if len(candidates) == 1:
            replacements[href] = candidates[0]

    changed_files = changed_links = 0
    for path in bodies:
        before = path.read_text(encoding="utf-8")

        def replace(match: re.Match[str]) -> str:
            nonlocal changed_links
            href = match.group(1)
            target = replacements.get(href)
            if target is None:
                return match.group(0)
            changed_links += 1
            return f'href="{target}"'

        after = re.sub(r'href="(/[^"#?]*)"', replace, before, flags=re.IGNORECASE)
        if after == before:
            continue
        path.write_text(after, encoding="utf-8")
        changed_files += 1

    print(
        f"fix_internal_routes: repaired {changed_links} links in "
        f"{changed_files} files using {len(replacements)} aliases"
    )


if __name__ == "__main__":
    main()
