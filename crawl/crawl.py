#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crawl south.tjc.org.tw (Word-exported, big5, HTTP only).
Fetch homepage + all internal .htm subpages, extract (text, url, source) links.
Output: raw-links.csv + raw-links.json
"""
import csv
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import OrderedDict

BASE = "http://south.tjc.org.tw/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TJC-crawler/1.0)"}

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("need bs4", file=sys.stderr)
    sys.exit(1)


def encode_url(url):
    """Percent-encode non-ASCII path/query (server accepts UTF-8 encoding)."""
    parts = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(parts.path, safe="/%")
    query = urllib.parse.quote(parts.query, safe="=&%?")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, query, parts.fragment))


def fetch(url):
    req = urllib.request.Request(encode_url(url), headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    # Word export is big5; decode leniently
    return raw.decode("big5", errors="replace")


def classify(href):
    low = href.lower()
    if low.startswith(("http://", "https://")) and "south.tjc.org.tw" not in low:
        # external host
        if "youtube" in low or "youtu.be" in low:
            return "youtube"
        return "external"
    ext = low.rsplit(".", 1)[-1].split("?")[0] if "." in low.rsplit("/", 1)[-1] else ""
    return {
        "pdf": "pdf", "doc": "doc", "docx": "doc",
        "xls": "excel", "xlsx": "excel",
        "jpg": "image", "jpeg": "image", "png": "image", "gif": "image",
        "rar": "archive", "zip": "archive",
        "htm": "page", "html": "page",
        "tif": "image", "tiff": "image",
    }.get(ext, "page" if not ext else ext)


def norm_text(t):
    return re.sub(r"\s+", " ", (t or "").strip())


def is_internal_page(abs_url):
    return abs_url.startswith(BASE) and abs_url.lower().split("?")[0].endswith((".htm", ".html"))


def main():
    # Seed pages: homepage + discovered numbered index pages
    seeds = [BASE]
    numbered = {
        "01": "index.htm", "02": "index.htm", "03": "index.htm",
        "04": "index-1.htm", "05": "index.htm", "06": "讀經教材.htm",
        "07": "index.htm", "08": "index.htm", "09": "index.htm",
        "10": "index.htm", "11": "index.htm", "12": "index.htm",
        "13": "index.htm", "14": "index.htm", "15": "index.htm",
        "16": "index.htm", "17": "index.htm", "18": "index.htm",
        "19": "index.htm", "20": "index.htm",
    }
    for n, fn in numbered.items():
        seeds.append(urllib.parse.urljoin(BASE, f"{n}/{urllib.parse.quote(fn)}"))

    visited = set()
    queue = list(OrderedDict.fromkeys(seeds))
    all_links = []   # dicts: text, url, source, type
    page_errors = []
    page_titles = {}  # path -> <title>, for the new-page safety net in categorize

    while queue:
        page = queue.pop(0)
        if page in visited:
            continue
        visited.add(page)
        try:
            html = fetch(page)
        except Exception as e:
            page_errors.append({"url": page, "error": str(e)})
            print(f"ERR  {page} -> {e}", file=sys.stderr)
            continue
        soup = BeautifulSoup(html, "html.parser")
        ttl = soup.title.get_text().strip() if soup.title else ""
        page_titles[urllib.parse.unquote(page.replace(BASE, "")) or "(home)"] = ttl
        n_found = 0
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
                continue
            abs_url = urllib.parse.urljoin(page, href)
            text = norm_text(a.get_text())
            all_links.append({
                "text": text,
                "url": abs_url,
                "raw_href": href,
                "source": page,
                "type": classify(href),
            })
            n_found += 1
            # Recurse into internal sub-pages not yet queued/visited
            if is_internal_page(abs_url) and abs_url not in visited and abs_url not in queue:
                # avoid recursing into the giant attachment dirs (they're files anyway)
                queue.append(abs_url)
        print(f"OK   {page}  ({n_found} links)", file=sys.stderr)

    # Dedupe links by (url, text)
    seen = set()
    deduped = []
    for l in all_links:
        key = (l["url"], l["text"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(l)

    # Write CSV
    with open("crawl/raw-links.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["text", "type", "url", "source", "raw_href"])
        w.writeheader()
        for l in deduped:
            w.writerow(l)

    with open("crawl/raw-links.json", "w", encoding="utf-8") as f:
        json.dump({
            "pages_crawled": sorted(visited),
            "page_titles": page_titles,
            "page_errors": page_errors,
            "link_count": len(deduped),
            "links": deduped,
        }, f, ensure_ascii=False, indent=2)

    # Summary
    from collections import Counter
    by_type = Counter(l["type"] for l in deduped)
    print("\n=== SUMMARY ===", file=sys.stderr)
    print(f"pages crawled : {len(visited)}", file=sys.stderr)
    print(f"page errors   : {len(page_errors)}", file=sys.stderr)
    print(f"unique links  : {len(deduped)}", file=sys.stderr)
    print(f"by type       : {dict(by_type)}", file=sys.stderr)


if __name__ == "__main__":
    main()
