#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse the homepage curated bulletin into data/announcements.json.
Preserves the office's 6 native sections + text-only notices (尋人啟示, 帳號, email, 說明).
"""
import json, re, urllib.request, urllib.parse
from bs4 import BeautifulSoup

BASE = "http://south.tjc.org.tw/"
raw = urllib.request.urlopen(urllib.request.Request(BASE, headers={"User-Agent": "Mozilla/5.0"}),
                             timeout=30).read().decode("big5", "replace")
soup = BeautifulSoup(raw, "html.parser")

SECTION_HEADERS = [
    ("special",  "特別公告"),
    ("missing",  "尋人啟示"),
    ("activity", "教區活動"),
    ("latest",   "最新公告"),
    ("notice",   "宣導事項"),
    ("reference","備查公告"),
]


def clean(s):
    return " ".join((s or "").split())


def norm_url(href):
    if not href:
        return None
    return urllib.parse.urljoin(BASE, href)


def match_header(txt):
    """Section header = short line, not starting with ※.
    Known headers keep stable ids; any other short line ending with a colon is
    treated as a NEW section so the office can add homepage blocks freely."""
    if txt.startswith("※"):
        return None, None
    s = txt.strip()
    if len(s) >= 30:
        return None, None
    # known sections first (stable ids: special/missing/activity/latest/notice/reference)
    has_colon = "：" in s or ":" in s
    for sid, kw in SECTION_HEADERS:
        if kw in s and (has_colon or s == kw):
            return sid, kw
    # generic: a short line ending with a colon = a brand-new homepage section
    if s.rstrip().endswith(("：", ":")):
        title = re.sub(r"[（(][^）)]*?更新[^）)]*?[）)]", "", s)  # drop (X月X日更新)
        title = title.rstrip("：:　 ").strip()
        if title:
            return "__GENERIC__", title
    return None, None


# Walk leaf-ish elements in reading order
body = soup.body or soup
leaves = []
for el in body.find_all(["p", "li", "h1", "h2", "h3", "td", "div"]):
    if el.find(["p", "li", "td", "div"]):
        continue
    txt = clean(el.get_text(" ", strip=True))
    if not txt:
        continue
    links = []
    for a in el.find_all("a", href=True):
        u = norm_url(a["href"])
        lab = clean(a.get_text(" ", strip=True))
        if u and not u.startswith(("mailto:", "javascript:")):
            links.append({"label": lab or "連結", "url": u})
    leaves.append({"text": txt, "links": links})

# Find start of bulletin (first section header)
start = None
for i, lf in enumerate(leaves):
    sid, _ = match_header(lf["text"])
    if sid:
        start = i
        break

sections = []
cur = None
extra_n = 0
date_re = re.compile(r"[（(]\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日更新")
for lf in leaves[start:]:
    sid, kw = match_header(lf["text"])
    if sid:
        if sid == "__GENERIC__":  # 辦事員在首頁新增的全新區塊
            extra_n += 1
            sid = "extra%d" % extra_n
        updated = ""
        m2 = re.search(r"(\d{1,2}\s*月\s*\d{1,2}\s*日更新|\d+\.\d+\s*更新)", lf["text"])
        if m2:
            updated = clean(m2.group(1)).replace(" ", "")
        cur = {"id": sid, "title": kw, "updated": updated, "items": []}
        sections.append(cur)
        continue
    if cur is None:
        continue
    # strip leading ※ and whitespace for display text
    disp = re.sub(r"^[※\s]+", "", lf["text"]).strip()
    cur["items"].append({"text": disp, "links": lf["links"]})

out = {
    "meta": {"source": BASE, "generated": "2026-06-12",
             "note": "首頁辦事處每月維護公告，原樣保留含純文字項目"},
    "sections": sections,
}
json.dump(out, open("data/announcements.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

print("sections:", len(sections))
for s in sections:
    nlinks = sum(len(i["links"]) for i in s["items"])
    print(f"  [{s['title']}] {s['updated']:12} items={len(s['items'])} links={nlinks}")
