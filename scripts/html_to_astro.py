#!/usr/bin/env python3
"""Convert WordPress HTML mirror pages to Astro pages."""

import json
import re
import html as html_lib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "mirror"
PAGES_DIR = ROOT / "src" / "pages"
DOMAIN = "onlinecasinoexperte.org"


def is_wayback_junk(text: str) -> bool:
    head = text[:3000].lower()
    return "<title>wayback machine</title>" in head


def canonical_path(html_path: Path) -> str:
    rel = html_path.relative_to(SITE).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[:-10].rstrip("/") + "/"
    return "/" + rel


def astro_output_path(html_path: Path) -> Path:
    rel = html_path.relative_to(SITE)
    if rel.as_posix() == "index.html":
        return PAGES_DIR / "index.astro"
    if rel.name == "index.html":
        return PAGES_DIR / rel.parent / "index.astro"
    return PAGES_DIR / rel.with_suffix(".astro")


def layout_import(astro_path: Path) -> str:
    rel = astro_path.relative_to(PAGES_DIR)
    depth = len(rel.parent.parts) + 1
    return "../" * depth + "layouts/BaseLayout.astro"


def normalize_content(html: str) -> str:
    html = re.sub(
        rf"https?://(?:www\.)?{re.escape(DOMAIN)}",
        "",
        html,
        flags=re.I,
    )
    html = re.sub(r'(?:\.\./)+wp-content/', '/wp-content/', html)
    html = re.sub(r'(?:\.\./)+', '/', html)

    def fix_href(m: re.Match[str]) -> str:
        val = m.group(1)
        if val.startswith(("/", "#", "mailto:", "tel:", "javascript:")):
            if val.startswith("/") and not val.endswith("/") and "." not in Path(val).name:
                return f'href="{val}/"'
            return m.group(0)
        val = val.strip("/")
        return f'href="/{val}/"'

    html = re.sub(r'href="([^"]+)"', fix_href, html)

    def fix_src(m: re.Match[str]) -> str:
        val = m.group(1)
        if val.startswith(("/", "http", "//", "data:")):
            return m.group(0)
        return f'src="/{val.lstrip("/")}"'

    html = re.sub(r'src="([^"]+)"', fix_src, html)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.I | re.S)
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.I | re.S)
    return html.strip()


SKIP_PATH_PREFIXES = ("wp-json/",)


def should_skip_path(html_path: Path) -> bool:
    rel = html_path.relative_to(SITE).as_posix()
    return rel.startswith(SKIP_PATH_PREFIXES)


def extract_main(html: str) -> str:
    m = re.search(r"<main[^>]*>(.*?)</main>", html, re.I | re.S)
    if m:
        return normalize_content(m.group(0))

    m = re.search(
        r"<!-- Page Section Start -->(.*?)<!-- Page Section End -->",
        html,
        re.I | re.S,
    )
    if m:
        return normalize_content(f"<main>{m.group(1).strip()}</main>")

    m = re.search(
        r"<!-- Header End -->(.*?)<!-- Footer Start -->",
        html,
        re.I | re.S,
    )
    if m:
        chunk = m.group(1).strip()
        chunk = re.sub(r"<footer[^>]*>.*", "", chunk, flags=re.I | re.S)
        return normalize_content(f"<main>{chunk}</main>")

    raise ValueError("No content region found")


def extract_meta(html: str) -> dict:
    def meta_content(name: str | None = None, prop: str | None = None) -> str:
        if name:
            pat = rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']*)["\']'
            alt = rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']{re.escape(name)}["\']'
        else:
            pat = rf'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']*)["\']'
            alt = rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']{re.escape(prop)}["\']'
        for p in (pat, alt):
            m = re.search(p, html, re.I)
            if m:
                return html_lib.unescape(m.group(1))
        return ""

    title = ""
    tm = re.search(r"<title>([^<]*)</title>", html, re.I)
    if tm:
        title = html_lib.unescape(tm.group(1).strip())

    canonical = ""
    cm = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', html, re.I)
    if not cm:
        cm = re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']', html, re.I)
    if cm:
        canonical = cm.group(1).replace(f"https://{DOMAIN}", "").replace(f"http://{DOMAIN}", "")
        if canonical and not canonical.endswith("/"):
            canonical += "/"

    json_ld = ""
    jm = re.search(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        re.I | re.S,
    )
    if jm:
        json_ld = jm.group(1).strip()

    body_class = ""
    bm = re.search(r'<body[^>]*class="([^"]*)"', html, re.I)
    if bm:
        body_class = bm.group(1)

    return {
        "title": title,
        "description": meta_content(name="description"),
        "canonical": canonical,
        "ogLocale": meta_content(prop="og:locale"),
        "ogType": meta_content(prop="og:type"),
        "ogTitle": meta_content(prop="og:title"),
        "ogDescription": meta_content(prop="og:description"),
        "ogUrl": meta_content(prop="og:url"),
        "ogImage": meta_content(prop="og:image"),
        "twitterCard": meta_content(name="twitter:card"),
        "jsonLd": json_ld,
        "bodyClass": body_class,
    }


def js_string(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def write_page(html_path: Path, meta: dict, main_html: str, astro_path: Path) -> None:
    body_path = astro_path.parent / "_body.html"
    body_path.parent.mkdir(parents=True, exist_ok=True)
    body_path.write_text(main_html + "\n", encoding="utf-8")

    import_path = layout_import(astro_path)
    body_import = "./_body.html?raw"

    lines = [
        "---",
        f"import BaseLayout from '{import_path}';",
        f"import bodyHtml from '{body_import}';",
        "",
        "const meta = {",
        f"  title: {js_string(meta['title'])},",
        f"  description: {js_string(meta['description'])},",
        f"  canonical: {js_string(meta['canonical'])},",
        f"  ogLocale: {js_string(meta.get('ogLocale', ''))},",
        f"  ogType: {js_string(meta.get('ogType', ''))},",
        f"  ogTitle: {js_string(meta.get('ogTitle', ''))},",
        f"  ogDescription: {js_string(meta.get('ogDescription', ''))},",
        f"  ogUrl: {js_string(meta.get('ogUrl', ''))},",
        f"  ogImage: {js_string(meta.get('ogImage', ''))},",
        f"  twitterCard: {js_string(meta.get('twitterCard', ''))},",
        f"  jsonLd: {js_string(meta.get('jsonLd', ''))},",
        f"  bodyClass: {js_string(meta.get('bodyClass', ''))},",
        "};",
        "---",
        "",
        "<BaseLayout {...meta}>",
        '  <Fragment set:html={bodyHtml} />',
        "</BaseLayout>",
        "",
    ]
    astro_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    html_files = sorted(SITE.rglob("*.html"))
    ok = skip = fail = 0
    errors: list[str] = []

    for html_path in html_files:
        if should_skip_path(html_path):
            skip += 1
            continue
        canonical_path_from_html = canonical_path(html_path)
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        if is_wayback_junk(text):
            skip += 1
            continue
        try:
            meta = extract_meta(text)
            meta["canonical"] = meta["canonical"] or canonical_path_from_html
            main_html = extract_main(text)
            astro_path = astro_output_path(html_path)
            write_page(html_path, meta, main_html, astro_path)
            ok += 1
        except Exception as exc:
            fail += 1
            errors.append(f"{html_path.relative_to(SITE)}: {exc}")

    print(f"Converted: {ok}, skipped (Wayback): {skip}, failed: {fail}")
    if errors:
        print("Errors:")
        for e in errors[:20]:
            print(" ", e)
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")


if __name__ == "__main__":
    main()
