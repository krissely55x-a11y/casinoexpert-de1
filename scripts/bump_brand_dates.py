from pathlib import Path

root = Path(__file__).resolve().parents[1] / "src" / "pages" / "casinos"
brands = ["skycrown", "goodman", "horus", "gioo", "casinobuck"]

for brand in brands:
    path = root / brand / "index.astro"
    text = path.read_text(encoding="utf-8")
    updated = text.replace(
        '"dateModified":"2026-07-20T00:00:00+02:00"',
        '"dateModified":"2026-08-14T00:00:00+02:00"',
    )
    updated = updated.replace(
        r"\"dateModified\":\"2026-07-20T00:00:00+02:00\"",
        r"\"dateModified\":\"2026-08-14T00:00:00+02:00\"",
    )
    path.write_text(updated, encoding="utf-8")
    print(f"{brand}: {'changed' if updated != text else 'unchanged'}")
