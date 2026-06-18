#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析各教會通訊錄（03/index1 台南、03/index2 高屏）。
把「教會名 ↔ 相片/簡介/FB 連結 + 地址/電話/傳真」綁回去，
輸出 data/churches.json。
"""
import json, re, urllib.request, urllib.parse
from bs4 import BeautifulSoup

BASE = "http://south.tjc.org.tw/"
PAGES = [
    ("台南小區", "03/index1.htm"),
    ("高屏小區", "03/index2.htm"),
]


def enc(u):
    p = urllib.parse.urlsplit(u)
    return urllib.parse.urlunsplit((p.scheme, p.netloc,
        urllib.parse.quote(p.path, safe="/%"), p.query, p.fragment))


def fetch(path):
    u = urllib.parse.urljoin(BASE, path)
    return urllib.request.urlopen(urllib.request.Request(enc(u),
        headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode("big5", "replace")


def clean(s):
    return " ".join((s or "").split())


def parse_page(district, path):
    soup = BeautifulSoup(fetch(path), "html.parser")
    churches = []
    cur = None
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        first = cells[0]
        anchors = first.find_all("a", href=True)
        ftext = clean(first.get_text(" ", strip=True))
        # A church-start row: first cell mentions 教會 and carries links
        if "教會" in ftext and anchors and re.search(r"教會", ftext):
            name = re.split(r"\s*(相片|簡介|FB|Facebook)", ftext)[0].strip()
            name = re.sub(r"[、，,\s]+$", "", name)
            links = []
            for a in anchors:
                lab = clean(a.get_text(" ", strip=True))
                href = urllib.parse.urljoin(BASE, a["href"])
                if lab and href and not href.startswith(("mailto:", "javascript:")):
                    links.append({"label": lab, "url": href})
            cur = {"district": district, "name": name, "links": links,
                   "address": "", "phone": "", "fax": ""}
            # second cell often holds 地址
            if len(cells) > 1:
                t = clean(cells[1].get_text(" ", strip=True))
                if "地址" in t:
                    cur["address"] = t.replace("地址：", "").replace("地址:", "").strip()
            churches.append(cur)
            continue
        # follow-up rows: 地址 / 電話 / 傳真
        if cur:
            t = clean(tr.get_text(" ", strip=True))
            if t.startswith("地址") and not cur["address"]:
                cur["address"] = re.sub(r"^地址[：:]\s*", "", t)
            elif t.startswith("電話"):
                cur["phone"] = re.sub(r"^電話[：:]\s*", "", t)
            elif t.startswith("傳真"):
                cur["fax"] = re.sub(r"^傳真[：:]\s*", "", t)
    return churches


def main():
    out = {"meta": {"source": BASE, "generated": "2026-06-12"}, "districts": []}
    for district, path in PAGES:
        chs = parse_page(district, path)
        out["districts"].append({"name": district, "churches": chs})
        print(f"{district}: {len(chs)} 間")
        for c in chs[:3]:
            print(f"   {c['name']} | links={[l['label'] for l in c['links']]} | {c['phone']}")
    json.dump(out, open("data/churches.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
