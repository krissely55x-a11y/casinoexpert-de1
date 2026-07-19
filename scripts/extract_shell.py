#!/usr/bin/env python3
"""Extract shared shell (header, footer, scripts) from WordPress mirror."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "mirror"
SOURCE = SITE / "index.html"
PARTIALS = ROOT / "src" / "partials"
DOMAIN = "onlinecasinoexperte.org"


def normalize_urls(html: str) -> str:
    html = re.sub(
        rf"https?://(?:www\.)?{re.escape(DOMAIN)}",
        "",
        html,
        flags=re.I,
    )
    html = re.sub(r'href="(?!/|#|mailto:|tel:|javascript:)([^"]+)"', r'href="/\1/"', html)
    html = re.sub(r"href='(?!/|#|mailto:|tel:|javascript:)([^']+)'", r"href='/\1/'", html)
    html = re.sub(r'src="(?!/|http|//|data:)([^"]+)"', r'src="/\1"', html)
    html = re.sub(r"src='(?!/|http|//|data:)([^']+)'", r"src='/\1'", html)
    html = re.sub(r'action="(?:https?://[^"]+)?/?"', 'action="/"', html)
    return html


def extract_between(html: str, start_pat: str, end_pat: str) -> str:
    m = re.search(start_pat, html, re.I | re.S)
    if not m:
        raise ValueError(f"Start pattern not found: {start_pat}")
    start = m.start()
    m2 = re.search(end_pat, html[m.end() :], re.I | re.S)
    if not m2:
        raise ValueError(f"End pattern not found: {end_pat}")
    return html[start : m.end() + m2.end()]


def extract_groovy_scripts(html: str) -> str:
    chunks = []
    for pat in [
        r'<script type="text/javascript" id="groovy-menu-js-js-extra">.*?</script>',
        r'<script[^>]+src="wp-content/plugins/groovy-menu/assets/js/frontend\.js"[^>]*></script>',
        r'<script type="text/javascript" id="groovy-menu-js-js-after">.*?</script>',
        r'<script type="text/javascript" nowprocket>var eleColl = document\.getElementsByClassName\("gm-navigation-drawer--mobile"\).*?</script>',
    ]:
        m = re.search(pat, html, re.I | re.S)
        if m:
            chunks.append(m.group(0))
    chunks.append(
        '<script defer src="//kit.fontawesome.com/23b8c66013.js" crossorigin="anonymous"></script>'
    )
    chunks.append(
        """<script defer src="/wp-content/themes/mercury/js/floating-header.js"></script>
<script defer src="/wp-content/themes/mercury/js/scripts.js"></script>"""
    )
    return "\n".join(chunks)


def main() -> None:
    html = SOURCE.read_text(encoding="utf-8", errors="ignore")

    header_style = ""
    m = re.search(r"<style>#menu-additional-menu.*?</style>", html, re.S)
    if m:
        header_style = m.group(0)

    header = extract_between(
        html,
        r'<header class="gm-navbar',
        r"</aside>",
    )
    header = header_style + "\n" + header

    footer_inner = extract_between(
        html,
        r'<footer class="space-footer',
        r"</footer>",
    )
    footer_inner = "<footer" + footer_inner.split("<footer", 1)[1] if "<footer" in footer_inner else footer_inner
    if not footer_inner.rstrip().endswith("</footer>"):
        footer_inner = footer_inner + "</footer>"

    post_footer = extract_between(
        html,
        r"<!-- Mobile Menu Start -->",
        r"<!-- Back to Top End -->",
    )

    scripts = extract_groovy_scripts(html)

    PARTIALS.mkdir(parents=True, exist_ok=True)
    (PARTIALS / "header.html").write_text(normalize_urls(header), encoding="utf-8")
    (PARTIALS / "footer.html").write_text(normalize_urls(footer_inner), encoding="utf-8")
    (PARTIALS / "post-footer.html").write_text(normalize_urls(post_footer), encoding="utf-8")
    (PARTIALS / "scripts.html").write_text(normalize_urls(scripts), encoding="utf-8")

    body_class = ""
    bm = re.search(r"<body[^>]*class=\"([^\"]*)\"", html, re.I)
    if bm:
        body_class = bm.group(1)

    (PARTIALS / "body-class.txt").write_text(body_class, encoding="utf-8")
    print(f"Extracted shell to {PARTIALS}")
    print(f"  header: {(PARTIALS / 'header.html').stat().st_size // 1024} KB")
    print(f"  footer: {(PARTIALS / 'footer.html').stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
