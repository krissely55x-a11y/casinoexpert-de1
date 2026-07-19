import re, urllib.parse, json
from pathlib import Path
SITE = Path(__file__).resolve().parent.parent / "mirror"
exist_fix = truly_missing = 0
seen = set()
for html in SITE.rglob("*.html"):
    text = html.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"https?://(?:www\.)?onlinecasinoexperte\.org/wp-content/uploads/[^\s\"'<>]+", text, re.I):
        url = m.group(0).split("?")[0]
        if url in seen:
            continue
        seen.add(url)
        p = SITE / urllib.parse.urlparse(url).path.lstrip("/")
        if p.exists():
            exist_fix += 1
        else:
            truly_missing += 1
print(json.dumps({
    "absolute_upload_urls": len(seen),
    "fixable": exist_fix,
    "truly_missing": truly_missing,
    "total_files": sum(1 for _ in SITE.rglob("*") if _.is_file()),
}))
