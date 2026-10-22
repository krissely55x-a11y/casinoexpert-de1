"""Classify page diffs against the August archive snapshot."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CUR = ROOT / "src" / "pages"
OLD = ROOT / "archive" / "git-repo" / "src" / "pages"

only_cur = []
only_old = []
same = 0
date_only = 0
other = []

DATE_SWAPS = [
    ("letztes Update 20/07/2026", "letztes Update 18/10/2026"),
    ("2026-07-20T00:00:00+02:00", "2026-10-18T00:00:00+02:00"),
    ("2026-08-14T00:00:00+02:00", "2026-10-18T00:00:00+02:00"),
    ("1 Woche ago", "letztes Update 18/10/2026"),
    ("1 Tag ago", "letztes Update 18/10/2026"),
    ("vor 5 Monaten", "letztes Update 18/10/2026"),
    ("2 Wochen ago", "letztes Update 18/10/2026"),
]

for path in CUR.rglob("*"):
    if not path.is_file():
        continue
    rel = path.relative_to(CUR)
    old = OLD / rel
    if not old.exists():
        only_cur.append(rel.as_posix())
        continue
    a = old.read_text(encoding="utf-8", errors="ignore")
    b = path.read_text(encoding="utf-8", errors="ignore")
    if a == b:
        same += 1
        continue
    trial = a
    for src, dst in DATE_SWAPS:
        trial = trial.replace(src, dst)
    if trial == b:
        date_only += 1
    else:
        other.append(rel.as_posix())

for path in OLD.rglob("*"):
    if path.is_file():
        rel = path.relative_to(OLD)
        if not (CUR / rel).exists():
            only_old.append(rel.as_posix())

print("same", same)
print("date_only", date_only)
print("other", len(other))
for rel in other:
    print(" ", rel)
print("only in current", len(only_cur))
for rel in only_cur[:20]:
    print("  C", rel)
print("only in archive", len(only_old))
