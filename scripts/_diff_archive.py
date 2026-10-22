"""See whether archive/git-repo still matches pages before today's edits."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CUR = ROOT / "src" / "pages"
OLD = ROOT / "archive" / "git-repo" / "src" / "pages"

samples = [
    "casinos/vegaz/index.astro",
    "casinos/vegaz/_body.html",
    "bonus/ohne-umsatz/index.astro",
    "bonus/ohne-umsatz/_body.html",
    "lizenz/index.astro",
    "slots/gamomat/index.astro",
    "slots/gamomat/_body.html",
    "apps/index.astro",
]
for rel in samples:
    a = (OLD / rel).read_text(encoding="utf-8", errors="ignore")
    b = (CUR / rel).read_text(encoding="utf-8", errors="ignore")
    print(f"\n== {rel} old {len(a)} new {len(b)} same {a==b}")
    if a == b:
        continue
    # first differing line
    al, bl = a.splitlines(), b.splitlines()
    n = 0
    for i, (x, y) in enumerate(zip(al, bl)):
        if x != y:
            n += 1
            if n <= 3:
                print(" line", i + 1)
                print("  OLD", x[:180])
                print("  NEW", y[:180])
    extra = abs(len(al) - len(bl))
    print(" differing line pairs shown, line count delta", extra, "old lines", len(al), "new", len(bl))
