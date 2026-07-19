import re
from pathlib import Path
from collections import Counter
from urllib.parse import urlparse

SITE = Path(__file__).resolve().parent.parent / "mirror"
DOMAIN = "onlinecasinoexperte.org"

external = Counter()
wayback = Counter()
internal_abs = 0
examples = {}

for f in SITE.rglob("*"):
    if not f.is_file() or f.suffix.lower() not in (".html", ".htm", ".css", ".js", ".php", ".xml", ".svg"):
        continue
    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for m in re.finditer(r"https?://[^\s\"'<>]+|//[^\s\"'<>/][^\s\"'<>]*", text, re.I):
        url = m.group(0).rstrip(".,;)")
        if url.startswith("//"):
            url = "https:" + url
        host = urlparse(url).netloc.lower().replace("www.", "")
        if not host:
            continue
        if "archive.org" in host:
            wayback[host] += 1
        elif host == DOMAIN:
            internal_abs += 1
        else:
            external[host] += 1
            examples.setdefault(host, url[:140])

print("EXTERNAL HOSTS:", len(external))
print("EXTERNAL URL COUNT:", sum(external.values()))
for h, c in external.most_common(30):
    print(f"  {c:5d}  {h}")
    print(f"         {examples[h]}")
print("---")
print("wayback refs:", sum(wayback.values()))
print("absolute internal refs:", internal_abs)
