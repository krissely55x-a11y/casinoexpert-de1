"""Stricter GSC phrase gaps: distinctive slug, German queries, exact phrase missing."""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "src" / "pages"
GSC = ROOT / "reports" / "gsc-2026-10-18"
FOREIGN = re.compile(
    r"avis|opinione|opiniones|reseña|review|anmeldelse|analise|bonuskod|bonusa|"
    r"jocuri|stratégie|strategie à|ruleta|κωδ|opinie|recension|betrouwbaar|"
    r"rabatkode|promo kód|bonusový|kod promocyjny|sloturi|pacanele",
    re.I,
)

def canon(url: str) -> str:
    path = url.split("onlinecasinoexperte.org", 1)[-1]
    return path if path.endswith("/") else path + "/"

def body_for(path: str) -> Path:
    rel = path.strip("/")
    return PAGES / rel / "_body.html" if rel else PAGES / "_body.html"

def slug_needles(path: str) -> list[str]:
    parts = [p for p in path.strip("/").split("/") if p]
    if not parts:
        return []
    last = parts[-1]
    special = {
        "ohne-umsatz": ["umsatz"],
        "lizenz": ["lizenz"],
        "freispiele": ["freispiele", "free spins"],
        "willkommensbonus": ["willkommens"],
        "karten-zaehlen": ["karten zählen", "kartenzählen", "karten zaehlen"],
        "grundstrategie": ["grundstrategie", "basisstrategie"],
        "romanowsky": ["romanow"],
        "double-ball": ["double ball"],
        "101-roulette": ["101 roulette", "ruleta 101"],
        "aloha-cluster-pays": ["aloha cluster"],
        "dead-or-alive-2": ["dead or alive 2"],
        "dead-or-alive": ["dead or alive"],
        "arcane-reel-chaos": ["arcane reel"],
        "divine-fortune": ["divine fortune"],
        "blood-suckers": ["blood suckers"],
        "berryburst": ["berryburst"],
        "bankroll-management": ["bankroll"],
        "red-and-black-system": ["red and black", "rot oder schwarz", "red or black"],
        "contra-d-alembert": ["contra", "d'alembert", "d alembert"],
        "d-alembert": ["d'alembert", "d alembert"],
        "dutzend-raster": ["dutzend"],
        "mini-roulette": ["mini roulette", "mini-roulette"],
        "franzoesisch": ["französisch", "franzoesisch", "french roulette"],
        "volatilitaet": ["volatil"],
        "rtp": ["rtp"],
        "squeeze-play": ["squeeze"],
        "thin-value-betting": ["thin value"],
        "rockwin-io": ["rockwin"],
        "casinobuck": ["casinobuck", "casino buck"],
        "hitnspin": ["hitnspin", "hit'n'spin", "hit n spin"],
        "crownplay": ["crownplay", "crown play"],
        "skycrown": ["skycrown", "sky crown"],
        "kryptosino": ["kryptosino"],
        "levelup": ["levelup", "level up"],
        "myempire": ["myempire", "my empire"],
        "goodman": ["goodman"],
        "gamomat": ["gamomat"],
        "echtgeld": ["echtgeld"],
        "willkommensbonus": ["willkommens"],
        "apps": ["app"],
        "live": ["live casino"],
        "tischspiele": ["tischspiel"],
        "roulette": ["roulette"],
        "blackjack": ["blackjack", "black jack"],
        "poker": ["poker"],
        "martingale": ["martingale"],
        "paroli": ["paroli"],
        "bluff": ["bluff"],
        "excalibur": ["excalibur"],
        "arabian-nights": ["arabian nights"],
        "gioo": ["gioo"],
        "gslot": ["gslot"],
        "haz": ["haz"],
        "horus": ["horus"],
        "vegaz": ["vegaz"],
    }
    if last in special:
        return special[last]
    return [last.replace("-", " ")]

pages = []
with open(GSC / "Pages.csv", encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        pages.append(canon(row["Top pages"]))

queries = []
with open(GSC / "Queries.csv", encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        queries.append((row["Top queries"].strip(), int(row["Impressions"])))

lines = []
for path in pages:
    bp = body_for(path)
    if not bp.exists():
        lines.append(f"MISSING FILE {path}")
        continue
    text = bp.read_text(encoding="utf-8", errors="ignore").lower()
    needles = slug_needles(path)
    # longer child slug should not use parent-only needles if last part is specific
    hits = []
    for q, qi in queries:
        if qi < 8:
            continue
        if FOREIGN.search(q):
            continue
        ql = q.lower()
        if not any(n in ql for n in needles):
            continue
        # dead-or-alive page should not eat dead or alive 2 queries
        if path.rstrip("/").endswith("dead-or-alive") and "dead or alive 2" in ql:
            continue
        if path.rstrip("/").endswith("/blackjack") and "karten" in ql and "karten-zaehlen" not in path:
            # counting queries belong on the counting article
            if "zählen" in ql or "zaehlen" in ql or "kartenz" in ql:
                continue
        if ql in text:
            continue
        hits.append((qi, q))
    hits.sort(reverse=True)
    if not hits:
        lines.append(f"COVERED {path}")
    else:
        shown = ", ".join(f"{q} [{qi}]" for qi, q in hits[:5])
        lines.append(f"GAP {path} :: {shown}")

out = ROOT / "reports" / "gsc-content-gaps.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print("gaps", sum(1 for x in lines if x.startswith("GAP")))
print("covered", sum(1 for x in lines if x.startswith("COVERED")))
print("wrote", out)
