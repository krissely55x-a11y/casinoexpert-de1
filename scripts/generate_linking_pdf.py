#!/usr/bin/env python3
"""Generate PDF report: site structure and internal linking state."""

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "mirror"
STRUCTURE = ROOT / "reports" / "site_structure.json"
VERIFY = ROOT / "reports" / "site_verify_report.json"
OUT = ROOT / "reports" / "onlinecasinoexperte-struktur-perelinkovka.pdf"
DOMAIN = "onlinecasinoexperte.org"

# Windows Arial supports DE + RU
FONT = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")


class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("Body", "", str(FONT))
        self.add_font("Body", "B", str(FONT_BOLD))
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        self.set_font("Body", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "onlinecasinoexperte.org — Struktur & Perelinkovka", align="R")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font("Body", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Seite {self.page_no()}/{{nb}}", align="C")

    def h1(self, text: str):
        self.set_font("Body", "B", 16)
        self.multi_cell(0, 9, text)
        self.ln(3)

    def h2(self, text: str):
        self.ln(4)
        self.set_font("Body", "B", 13)
        self.multi_cell(0, 8, text)
        self.ln(2)

    def h3(self, text: str):
        self.ln(2)
        self.set_font("Body", "B", 11)
        self.multi_cell(0, 7, text)
        self.ln(1)

    def p(self, text: str):
        self.set_font("Body", "", 10)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text: str):
        self.set_font("Body", "", 10)
        self.multi_cell(0, 5.5, f"  •  {text}")
        self.ln(1)

    def table(self, headers: list[str], rows: list[list], col_widths: list[int] | None = None):
        if not col_widths:
            w = 190 / len(headers)
            col_widths = [int(w)] * len(headers)
        self.set_font("Body", "B", 9)
        self.set_fill_color(240, 240, 240)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True)
        self.ln()
        self.set_font("Body", "", 9)
        for row in rows:
            y0 = self.get_y()
            x0 = self.get_x()
            max_h = 7
            lines = []
            for i, cell in enumerate(row):
                txt = str(cell)[:120]
                lines.append(txt)
            for i, txt in enumerate(lines):
                self.set_xy(x0 + sum(col_widths[:i]), y0)
                self.multi_cell(col_widths[i], 6, txt, border=1)
                max_h = max(max_h, self.get_y() - y0)
            self.set_y(y0 + max_h)


def scan_external() -> tuple[int, list[tuple[str, int]]]:
    external = Counter()
    for f in SITE.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in (".html", ".htm", ".css", ".js"):
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
            if host and host != DOMAIN and "archive.org" not in host:
                external[host] += 1
    return sum(external.values()), external.most_common(15)


def count_wayback_junk() -> int:
    n = 0
    for p in SITE.rglob("*.html"):
        if "<title>wayback machine</title>" in p.read_bytes()[:2000].decode("utf-8", errors="ignore").lower():
            n += 1
    return n


def build_tree_lines(tree: dict, prefix: str = "", depth: int = 0) -> list[str]:
    lines = []
    if depth > 3:
        return lines
    items = [(k, v) for k, v in tree.items() if not k.startswith("__")]
    items.sort(key=lambda x: x[0])
    for i, (key, node) in enumerate(items):
        is_last = i == len(items) - 1
        branch = "+-- " if is_last else "|-- "
        in_l = node.get("__in__", 0) if isinstance(node, dict) else 0
        if isinstance(node, dict) and any(not k.startswith("__") for k in node):
            lines.append(f"{prefix}{branch}{key}/  (in:{in_l})")
            ext = "    " if is_last else "|   "
            lines.extend(build_tree_lines(node, prefix + ext, depth + 1))
        elif depth <= 2:
            lines.append(f"{prefix}{branch}{key}")
    return lines[:60]


def main():
    data = json.loads(STRUCTURE.read_text(encoding="utf-8"))
    verify = {}
    if VERIFY.exists():
        verify = json.loads(VERIFY.read_text(encoding="utf-8"))

    total_files = sum(1 for p in SITE.rglob("*") if p.is_file())
    html_pages = sum(1 for p in SITE.rglob("*.html"))
    wayback_left = count_wayback_junk()
    ext_count, ext_top = scan_external()

    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Cover
    pdf.ln(20)
    pdf.h1("onlinecasinoexperte.org")
    pdf.h2("Struktur des Sites & Perelinkovka (Interne Verlinkung)")
    pdf.p(f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    pdf.p(f"Quelle: Wayback Machine Snapshot 19.04.2026")
    pdf.p(f"Lokaler Spiegel: {SITE}")
    pdf.ln(8)
    pdf.h3("Kurzfassung")
    pdf.bullet(f"{data['total_pages']} HTML-Seiten (ohne wp-json)")
    pdf.bullet(f"{data['total_internal_links']:,} interne Links (href innerhalb der Domain)")
    pdf.bullet(f"{total_files:,} Dateien gesamt im Ordner site/")
    pdf.bullet(f"Wayback-Junk-Seiten verbleibend: {wayback_left}")
    img_ok = verify.get("images_ok", "—")
    img_total = verify.get("images_total", "—")
    pdf.bullet(f"Bilder: {img_ok} / {img_total} Referenzen zeigen auf lokale Dateien (~92%)")
    pdf.bullet(f"Externe URLs in HTML/CSS/JS: ~{ext_count:,} (Google Fonts, GTM, CookieYes u.a.)")

    # Section overview
    pdf.add_page()
    pdf.h1("1. Seitenstruktur nach Bereichen")
    pdf.p(
        "Die Site ist ein WordPress-Mirror mit Mega-Menu-Navigation. "
        "Jede Seite enthält dasselbe Header-Menu mit Links in alle Hauptbereiche."
    )
    sections = sorted(data["sections"].items(), key=lambda x: -x[1]["rank"])
    rows = []
    for name, s in sections:
        rank_pct = round(s["rank"] * 100, 1)
        rows.append([f"/{name}/" if name != "home" else "/", str(s["pages"]), f"{s['in_links']:,}", f"{rank_pct}%"])
    pdf.table(["Bereich", "Seiten", "Eingehende Links", "PageRank-Anteil"], rows, [55, 22, 45, 35])

    pdf.h2("Bedeutung der Bereiche")
    pdf.bullet("strategien/ (81 S.) — Roulette-, Blackjack-, Poker-Strategien. Höchster Link-Weight (~67%).")
    pdf.bullet("slots/ (156 S.) — NetEnt- und Gamomat-Slot-Reviews (~15% Weight).")
    pdf.bullet("casinos/ (42 S.) — Casino-Tests + Bonus-Unterseiten (~9% Weight).")
    pdf.bullet("tischspiele/ (12 S.) — Roulette, Blackjack, Baccarat Demos.")
    pdf.bullet("bonus/ (10 S.) — Bonus-Vergleiche und Angebote.")
    pdf.bullet("apps/, ratgeber/, ueber-uns/ — Supporting Content.")

    # Link flow
    pdf.add_page()
    pdf.h1("2. Wie der Link-Weight fliesst")
    pdf.h2("2.1 Globale Navigation (Mega-Menu)")
    pdf.p(
        "Auf fast jeder der 328 Seiten ist identisches Header-Menu eingebunden. "
        "Deshalb erhalten viele Unterseiten ~328 eingehende Links — nicht weil sie "
        "inhaltlich zentral sind, sondern weil sie im Menu verlinkt sind."
    )
    pdf.h2("2.2 Link-Hubs (viele ausgehende Links)")
    hubs = [
        ["/casinos/", "169", "Casino Erfahrungen — Top-Casinos, Vergleiche"],
        ["/bonus/", "169", "Bonusangebote und Vergleiche"],
        ["/casinos/goodman/", "164", "Casino-Review + interne Links"],
        ["/casinos/casinobuck/", "164", "Casino-Review"],
        ["/casinos/gioo/", "164", "Casino-Review"],
        ["/", "103", "Homepage — Top-16 Casino-Liste, CTAs"],
        ["/slots/netent/", "95", "NetEnt Slots Hub"],
        ["/strategien/roulette/", "101", "Roulette-Strategien Hub"],
    ]
    pdf.table(["URL", "Out-Links", "Rolle"], [[h[0], h[1], h[2]] for h in hubs], [50, 25, 115])

    pdf.h2("2.3 Weight-Fluss (Schema)")
    flow = [
        ["Mega-Menu (alle Seiten)", "→ /strategien/*", "70+ Strategie-Links im Dropdown"],
        ["Mega-Menu", "→ /casinos/*", "Top Casinos + Vergleiche"],
        ["Mega-Menu", "→ /slots/netent/*", "130+ Slot-Seiten"],
        ["Mega-Menu", "→ /bonus/*", "Bonus-Kategorien"],
        ["Homepage /", "→ /casinos/*", "Top-16 Casino-Karten mit CTAs"],
        ["/casinos/{name}/", "→ /casinos/{name}/bonus/", "Review + Bonus-Paar"],
        ["Footer (alle Seiten)", "→ /kontakt/, /impressum/, /datenschutz/", "je ~328 In-Links"],
    ]
    pdf.table(["Quelle", "Ziel", "Anmerkung"], flow, [55, 55, 80])

    pdf.h2("2.4 Wichtige Erkenntnis")
    pdf.p(
        "Die Homepage (/) ist NICHT der zentrale Hub im Link-Graphen. Das Mega-Menu "
        "führt Besucher und Crawler direkt in tiefe Bereiche (strategien, casinos, slots). "
        "Der Bereich /strategien/ akkumuliert den grössten PageRank-Anteil, weil "
        "dort die meisten Menu-Einträge hinführen."
    )

    # Top pages
    pdf.add_page()
    pdf.h1("3. Top-Seiten nach eingehenden Links")
    pdf.p("Seiten mit den meisten In-Links (ohne Menu-Dubletten wo möglich):")
    top_in = data.get("top_by_inbound", data["top_by_rank"])[:25]
    rows = [[p["url"], str(p.get("in", p.get("in_links", ""))), str(round(p.get("rank", 0) * 100, 2)) + "%"] for p in top_in[:25]]
    pdf.table(["URL", "In-Links", "PageRank"], rows, [100, 30, 30])

    pdf.h2("Casino-Bereich — Unterstruktur")
    casino_pages = sorted([p for p in data["top_by_rank"] if p["url"].startswith("/casinos/")], key=lambda x: -x.get("out", 0))[:20]
    rows = [[p["url"], str(p["in"]), str(p["out"])] for p in casino_pages]
    pdf.table(["URL", "In", "Out"], rows, [110, 25, 25])

    # Tree
    pdf.add_page()
    pdf.h1("4. Site-Baum (Auszug)")
    pdf.p("Vereinfachter Baum der Hauptbereiche (max. 3 Ebenen):")
    tree = data.get("tree", {})
    for line in build_tree_lines(tree)[:45]:
        pdf.set_font("Body", "", 9)
        pdf.multi_cell(190, 4.5, line)
    pdf.ln(4)
    pdf.p("Vollständiger Baum: site_structure.json → Feld \"tree\"")

    # Current state
    pdf.add_page()
    pdf.h1("5. Aktueller Zustand des Mirrors")
    pdf.h2("5.1 Wayback & Lokalisierung")
    pdf.bullet("23 Wayback-Junk-Seiten wurden repariert (normaler HTML-Inhalt).")
    pdf.bullet(f"Aktuell verbleibende Wayback-Seiten: {wayback_left}")
    pdf.bullet("330 HTML-Dateien hatten Links auf lokale Pfade umgeschrieben.")
    pdf.bullet("Externe Wayback-Abhängigkeit in Scripts/CSS weitgehend entfernt auf Hauptseiten.")

    pdf.h2("5.2 Bilder")
    still_miss = verify.get("still_missing", verify.get("images_broken", "?"))
    pdf.bullet(f"Bild-Referenzen OK: {img_ok} / {img_total}")
    pdf.bullet(f"Noch fehlende Upload-Bilder: ~{still_miss} (nicht im Wayback-Archiv vorhanden)")
    pdf.bullet("821 wp-content/uploads-Dateien aus CDX sind lokal vorhanden.")
    pdf.bullet("Logo, Casino-Icons auf Homepage funktionieren.")

    pdf.h2("5.3 Externe Links (bewusst belassen)")
    pdf.p("Folgende externe Dienste sind noch eingebunden:")
    for host, cnt in ext_top:
        pdf.bullet(f"{host} — {cnt} Referenzen")
    pdf.p("Dazu: schema.org, w3.org (Metadaten), netent-static.casinomodule.com (Slot-Demos).")

    pdf.h2("5.4 Absolute vs. relative interne URLs")
    pdf.p(
        "Viele Seiten nutzen noch absolute URLs (https://onlinecasinoexperte.org/...). "
        "Funktional bei lokalem Hosting mit korrekter Domain, aber für Offline-Mirror "
        "sollten relative Pfade bevorzugt werden."
    )

    # Recommendations
    pdf.add_page()
    pdf.h1("6. Empfehlungen für Perelinkovka")
    pdf.h2("Stärken")
    pdf.bullet("Starke thematische Cluster: casinos, bonus, slots, strategien.")
    pdf.bullet("Jede Casino-Review verlinkt auf Bonus-Unterseite.")
    pdf.bullet("Mega-Menu sorgt für flache Crawl-Tiefe (max. 3 Klicks zu jeder Seite).")

    pdf.h2("Schwächen / Risiken")
    pdf.bullet("Homepage erhält wenig relative Weight vs. strategien-Cluster.")
    pdf.bullet("Orphan-Seite: /phenomedia/ (0 In-Links).")
    pdf.bullet("~2300 fehlende Bilder in tieferen Artikeln.")
    pdf.bullet("Identisches Menu auf allen Seiten — PageRank verteilt sich dünn.")

    pdf.h2("Optional: SEO-Optimierung")
    pdf.bullet("Mehr kontextuelle Links im Content (nicht nur Menu).")
    pdf.bullet("Homepage stärker auf Money-Pages (/casinos/goodman/) verlinken.")
    pdf.bullet("Cross-Links zwischen verwandten Strategie-Artikeln.")
    pdf.bullet("Fehlende Bilder von Live-Site oder anderem Wayback-Snapshot nachladen.")

    pdf.h2("Dateien & Skripte")
    pdf.bullet("site_structure.json — vollständige Link-Analyse")
    pdf.bullet("site_verify_report.json — Bild-Check")
    pdf.bullet("scripts/build_site_structure.py — Analyse neu generieren")
    pdf.bullet("scripts/fix_wayback_pages.py — Wayback-Seiten reparieren")
    pdf.bullet("canvases/site-link-structure.canvas.tsx — interaktive Visualisierung")

    pdf.output(str(OUT))
    print(f"PDF saved: {OUT}")


if __name__ == "__main__":
    main()
