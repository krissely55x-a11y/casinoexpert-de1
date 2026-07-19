#!/usr/bin/env python3
"""Bundle WordPress CSS from mirror into a single legacy.css for Astro."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "mirror"
SOURCE_HTML = SITE / "index.html"
OUT_CSS = ROOT / "public" / "styles" / "legacy.css"

SKIP_STYLE_IDS = {
    "core-block-supports-inline-css",
    "core-block-supports-duotone-inline-css",
}

EDITOR_PATTERNS = [
    re.compile(r"--wp-admin-[^;]+;"),
    re.compile(r"--wp-block-synced-color[^;]*;"),
    re.compile(r"--wp-editor-canvas-background[^;]*;"),
    re.compile(r"--wp-bound-block-color[^;]*;"),
]


def read_stylesheet_href(href: str) -> str | None:
    href = href.strip().strip('"').strip("'")
    if not href or href.startswith(("http://", "https://", "//")):
        return None
    path = SITE / href.replace("/", "\\") if "\\" not in href else SITE / href
    if not path.is_file():
        path = SITE / href.lstrip("/")
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="ignore")
    return None


def strip_editor_css(text: str) -> str:
    for pat in EDITOR_PATTERNS:
        text = pat.sub("", text)
    return text


def sanitize_css(text: str) -> str:
    text = strip_editor_css(text)
    text = re.sub(r"^--YOAST[^\n]*$", "", text, flags=re.M)
    text = re.sub(r"/\*#\s*sourceURL=.*?\*/", "", text)
    return text


def extract_inline_styles(html: str) -> list[str]:
    blocks = []
    for m in re.finditer(
        r'<style[^>]*id=["\']([^"\']*)["\'][^>]*>(.*?)</style>',
        html,
        re.I | re.S,
    ):
        style_id = m.group(1)
        if style_id in SKIP_STYLE_IDS:
            continue
        css = sanitize_css(m.group(2).strip())
        if css:
            blocks.append(f"/* inline: {style_id} */\n{css}")
    return blocks


def extract_linked_styles(html: str) -> list[str]:
    blocks = []
    seen: set[str] = set()
    for m in re.finditer(
        r'<link[^>]+rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)["\']',
        html,
        re.I,
    ):
        href = m.group(1)
        if href in seen:
            continue
        seen.add(href)
        css = read_stylesheet_href(href)
        if css:
            blocks.append(f"/* linked: {href} */\n{sanitize_css(css)}")
    return blocks


def main() -> None:
    html = SOURCE_HTML.read_text(encoding="utf-8", errors="ignore")
    parts = [
        "/* Bundled legacy WordPress styles for onlinecasinoexperte.org */",
        *extract_linked_styles(html),
        *extract_inline_styles(html),
    ]
    OUT_CSS.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSS.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    size_kb = OUT_CSS.stat().st_size / 1024
    print(f"Wrote {OUT_CSS} ({size_kb:.1f} KB, {len(parts)-1} blocks)")


if __name__ == "__main__":
    main()
