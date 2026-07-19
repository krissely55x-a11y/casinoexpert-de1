import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "mirror"
DOMAIN = "onlinecasinoexperte.org"
data = json.loads((ROOT / "reports" / "site_structure.json").read_text(encoding="utf-8"))

sec = data["sections"]["strategien"]
print("=== SECTION strategien ===")
print(f"Pages: {sec['pages']}")
print(f"Sum of in_links (all strategien pages): {sec['in_links']}")
print(f"Avg in_links per page: {sec['in_links'] / sec['pages']:.0f}")

pages = {}
for p in SITE.rglob("*.html"):
    if "wayback machine" in p.read_bytes()[:2000].decode("utf-8", errors="ignore").lower():
        continue
    rel = p.relative_to(SITE).as_posix()
    if rel == "index.html":
        url = "/"
    elif rel.endswith("/index.html"):
        url = "/" + rel[:-10] + "/"
    else:
        url = "/" + rel
    pages[url] = p

print(f"\nTotal site pages analyzed: {len(pages)}")

to_strat = Counter()
sources_to_strat = Counter()

for src, path in pages.items():
    text = path.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r'href=(["\'])(.*?)\1', text, re.I):
        href = m.group(2).split("#")[0].split("?")[0]
        if href.startswith("/"):
            full = href
        elif "onlinecasinoexperte.org" in href:
            full = urlparse(href).path
        else:
            continue
        if not full.endswith("/") and not Path(full).suffix:
            full += "/"
        if full.startswith("/strategien/"):
            to_strat[full] += 1
            sources_to_strat[src.split("/")[1] if src != "/" else "home"] += 1

print(f"\nTotal href instances pointing to /strategien/*: {sum(to_strat.values())}")
print(f"Unique strategien URLs targeted: {len(to_strat)}")
print(f"\nTop strategien pages by in-link count:")
for url, cnt in to_strat.most_common(8):
    print(f"  {cnt:4d}  {url}")

print(f"\nWho links to strategien (by source section):")
for sec_name, cnt in sources_to_strat.most_common(10):
    print(f"  {cnt:5d}  from /{sec_name}/ pages")

# menu link count on one page
sample = pages.get("/bonus/", pages.get("/"))
text = sample.read_text(encoding="utf-8", errors="ignore")
menu_strat = len(re.findall(r'href="/strategien/', text))
print(f"\nOn /bonus/ page: {menu_strat} links to /strategien/ in HTML")
