# -*- coding: utf-8 -*-
"""解析原站「真光園區」(/19/index.htm) → data/doc-zhenguang.json

兩段：
  1. 公告與申請文件：公告日期(rowspan) | 檔案內容(連結) | 修正日期
  2. 相片集：類別（公告及地圖 / 入園道路 / 園區景觀…）| 多張相片連結
皆輸出共用 renderDocTable schema。
"""
import re
import os
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/19/index.htm"
BASE = "http://south.tjc.org.tw/19/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "doc-zhenguang.json")


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("big5", "ignore")


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s).replace("\xa0", " ")).strip()


def kind_of(url):
    u = url.lower().split("?")[0]
    ext = u.rsplit(".", 1)[-1] if "." in u else ""
    return {"pdf": "pdf", "doc": "doc", "docx": "doc", "jpg": "image", "jpeg": "image",
            "png": "image", "gif": "image"}.get(ext, "page")


def links_in(frag):
    out = []
    for m in re.finditer(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', frag, re.S | re.I):
        url = htmllib.unescape(m.group(1).strip())
        if url.startswith("#") or not url:
            continue
        if not url.startswith("http"):
            url = BASE + url
        lab = clean(m.group(2))
        if lab:
            out.append({"label": lab, "url": url, "kind": kind_of(url)})
    return out


def link_cell(frag):
    lks = links_in(frag)
    if not lks:
        return clean(frag)
    if len(lks) == 1 and clean(frag) == lks[0]["label"]:
        return {"t": lks[0]["label"], "u": lks[0]["url"], "k": lks[0]["kind"]}
    lead = clean(frag)
    for l in lks:
        lead = lead.replace(l["label"], "")
    return {"t": lead.strip(" 、，,。;；"), "parts": lks}


def parse_cells(tr):
    out = []
    for m in re.finditer(r"<t[dh]\b([^>]*)>(.*?)</t[dh]>", tr, re.S | re.I):
        rs = re.search(r'rowspan=["\']?(\d+)', m.group(1), re.I)
        out.append((int(rs.group(1)) if rs else 1, m.group(2)))
    return out


def parse_docs(t):
    trs = re.findall(r"<tr\b[^>]*>(.*?)</tr>", t, re.S | re.I)
    carries = {}
    rows = []
    for tr in trs[1:]:
        cells = parse_cells(tr)
        if not cells:
            continue
        row = [None] * 3
        ptr = 0
        for col in range(3):
            c = carries.get(col)
            if c and c["rem"] > 0:
                row[col] = c["val"]; c["rem"] -= 1; continue
            if ptr < len(cells):
                rs, raw = cells[ptr]; ptr += 1
                row[col] = link_cell(raw) if col == 1 else clean(raw)
                if rs > 1:
                    carries[col] = {"val": row[col], "rem": rs - 1}
        rows.append(row)
    return rows


def parse_photos(t):
    rows = []
    for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>", t, re.S | re.I):
        cells = parse_cells(tr)
        if len(cells) < 2:
            continue
        label = clean(cells[0][1])
        photos = links_in(cells[1][1])
        if photos:
            rows.append([label, {"parts": photos}])
    return rows


def main():
    raw = fetch()
    b = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    b = re.sub(r"</?(span|o:p|b|i|font)\b[^>]*>", "", b, flags=re.I)
    tables = re.findall(r"<table\b.*?</table>", b, re.S | re.I)

    sections = []
    docs = parse_docs(tables[0])
    if docs:
        sections.append({"name": "公告與申請文件", "columns": ["公告日期", "檔案內容", "修正日期"],
                         "primary": 1, "rows": docs})
    if len(tables) > 1:
        photos = parse_photos(tables[1])
        if photos:
            sections.append({"name": "相片集", "columns": ["類別", "相片"], "primary": 1, "rows": photos})

    data = {
        "source": SRC, "kicker": "真光園區",
        "title": "真光園區", "subtitle": "南區真光紀念園區公告、申請文件與園區相片",
        "sections": sections,
        "note": "點檔案內容開啟公告／申請書；相片連結導向原站圖檔。",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    for s in sections:
        print(s["name"], "→", len(s["rows"]), "列")
    print("written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
