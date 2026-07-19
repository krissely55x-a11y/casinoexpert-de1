#!/usr/bin/env python3
"""Build internal link graph and PageRank-style weight flow for the site."""

import json
import re
import urllib.parse
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "mirror"
DOMAIN = "onlinecasinoexperte.org"
OUT = ROOT / "reports" / "site_structure.json"


SKIP_PREFIXES = ("/wp-json/", "/feed/", "/xmlrpc.php")


def canonical(path: str) -> str:
    path = path or "/"
    if not path.startswith("/"):
        path = "/" + path
    path = re.sub(r"/+", "/", path)
    if path != "/" and not Path(path).suffix and not path.endswith("/"):
        path += "/"
    if path != "/":
        path = path.rstrip("/") + "/"
    return path


def page_url(path: Path) -> str:
    rel = path.relative_to(SITE).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return canonical("/" + rel[:-10])
    return canonical("/" + rel)


def normalize_href(href: str, base_url: str) -> str | None:
    href = href.strip().split("#")[0].split("?")[0]
    if not href or href in (".", "..") or href.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/"):
        full = f"https://{DOMAIN}{href}"
    elif href.startswith("http"):
        full = href
    else:
        base = f"https://{DOMAIN}{canonical(base_url)}"
        full = urllib.parse.urljoin(base, href)
    parsed = urllib.parse.urlparse(full)
    host = parsed.netloc.lower().replace("www.", "")
    if host and host != DOMAIN:
        return None
    path = canonical(parsed.path or "/")
    if any(path.startswith(p) for p in SKIP_PREFIXES):
        return None
    return path


def collect_pages() -> dict[str, Path]:
    pages = {}
    for p in SITE.rglob("*.html"):
        if "<title>wayback machine</title>" in p.read_bytes()[:2000].decode("utf-8", errors="ignore").lower():
            continue
        url = page_url(p)
        if any(url.startswith(p) for p in SKIP_PREFIXES):
            continue
        pages[url] = p
    return pages


def extract_links(html_path: Path, base_url: str) -> set[str]:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    links = set()
    for m in re.finditer(r'href\s*=\s*["\']([^"\']+)["\']', text, re.I):
        n = normalize_href(m.group(1), f"https://{DOMAIN}{base_url}")
        if n:
            links.add(n)
    return links


def pagerank(adj: dict[str, set[str]], pages: list[str], d=0.85, iters=40) -> dict[str, float]:
    n = len(pages)
    if n == 0:
        return {}
    idx = {p: i for i, p in enumerate(pages)}
    out_w = {p: max(len(adj.get(p, set())), 1) for p in pages}
    rank = {p: 1.0 / n for p in pages}
    for _ in range(iters):
        new = {p: (1 - d) / n for p in pages}
        for src, targets in adj.items():
            if src not in idx:
                continue
            share = d * rank[src] / out_w[src]
            for tgt in targets:
                if tgt in idx:
                    new[tgt] += share
        rank = new
    return rank


def section(path: str) -> str:
    parts = [x for x in path.strip("/").split("/") if x]
    return parts[0] if parts else "home"


def main():
    pages = collect_pages()
    adj: dict[str, set[str]] = defaultdict(set)
    inbound: dict[str, int] = defaultdict(int)
    outbound: dict[str, int] = defaultdict(int)

    for url, path in pages.items():
        for link in extract_links(path, url):
            if link in pages:
                adj[url].add(link)
                outbound[url] += 1
                inbound[link] += 1

    page_list = sorted(pages.keys())
    ranks = pagerank(adj, page_list)

    by_section: dict[str, dict] = defaultdict(lambda: {"pages": 0, "in_links": 0, "rank": 0.0})
    for url in page_list:
        sec = section(url)
        by_section[sec]["pages"] += 1
        by_section[sec]["in_links"] += inbound[url]
        by_section[sec]["rank"] += ranks[url]

    top_rank = sorted(page_list, key=lambda u: ranks[u], reverse=True)[:40]
    top_in = sorted(page_list, key=lambda u: inbound[u], reverse=True)[:30]
    top_out = sorted(page_list, key=lambda u: outbound[u], reverse=True)[:20]

    tree: dict = {}
    for url in page_list:
        parts = [x for x in url.strip("/").split("/") if x]
        node = tree
        for part in parts:
            node = node.setdefault(part, {})
        node.setdefault("__url__", url)
        node.setdefault("__rank__", ranks[url])
        node.setdefault("__in__", inbound[url])

    data = {
        "total_pages": len(page_list),
        "total_internal_links": sum(outbound.values()),
        "sections": {
            k: {**v, "rank": round(v["rank"], 4)}
            for k, v in sorted(by_section.items(), key=lambda x: -x[1]["rank"])
        },
        "top_by_rank": [
            {"url": u, "rank": round(ranks[u], 5), "in": inbound[u], "out": outbound[u]}
            for u in top_rank
        ],
        "top_by_inbound": [{"url": u, "in": inbound[u], "rank": round(ranks[u], 5)} for u in top_in],
        "top_by_outbound": [{"url": u, "out": outbound[u]} for u in top_out],
        "tree": tree,
    }
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Pages: {len(page_list)}, links: {sum(outbound.values())}")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
