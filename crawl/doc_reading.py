# -*- coding: utf-8 -*-
"""解析原站「讀經教材」(/06/讀經教材.htm) → data/doc-reading.json

三段：
  1. 讀經教材：各卷合併檔（書卷 PDF 格狀清單）
  2. 讀經小挑戰：上傳日期 | 內容（rowspan 日期）
  3. 聽道筆記：上傳日期 | 內容
"""
import re
import os
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/06/%E8%AE%80%E7%B6%93%E6%95%99%E6%9D%90.htm"
BASE = "http://south.tjc.org.tw/06/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "doc-reading.json")


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("big5", "ignore")


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s).replace("\xa0", " ")).strip()


def kind_of(url):
    u = url.lower().split("?")[0]
    ext = u.rsplit(".", 1)[-1] if "." in u else ""
    return {"pdf": "pdf", "doc": "doc", "docx": "doc", "ppt": "ppt", "pptx": "ppt"}.get(ext, "page")


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
    if len(lks) == 1:
        return {"t": lks[0]["label"], "u": lks[0]["url"], "k": lks[0]["kind"]}
    return {"t": "", "parts": lks}


def parse_cells(tr):
    out = []
    for m in re.finditer(r"<t[dh]\b([^>]*)>(.*?)</t[dh]>", tr, re.S | re.I):
        rs = re.search(r'rowspan=["\']?(\d+)', m.group(1), re.I)
        out.append((int(rs.group(1)) if rs else 1, m.group(2)))
    return out


def parse_dated(t):
    """上傳日期 | 內容（rowspan 日期）。"""
    trs = re.findall(r"<tr\b[^>]*>(.*?)</tr>", t, re.S | re.I)
    carries = {}
    rows = []
    for tr in trs[1:]:
        cells = parse_cells(tr)
        if not cells:
            continue
        row = [None, None]
        ptr = 0
        for col in range(2):
            c = carries.get(col)
            if c and c["rem"] > 0:
                row[col] = c["val"]; c["rem"] -= 1; continue
            if ptr < len(cells):
                rs, raw = cells[ptr]; ptr += 1
                row[col] = link_cell(raw) if col == 1 else clean(raw)
                if rs > 1:
                    carries[col] = {"val": row[col], "rem": rs - 1}
        if row[1]:
            rows.append(row)
    return rows


def main():
    raw = fetch()
    b = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    b = re.sub(r"</?(span|o:p|b|i|font)\b[^>]*>", "", b, flags=re.I)
    tables = re.findall(r"<table\b.*?</table>", b, re.S | re.I)

    sections = []
    # 1) 書卷合併檔
    books = links_in(tables[0])
    if books:
        sections.append({"name": "讀經教材（各卷合併檔）", "columns": ["書卷"], "primary": 0,
                         "rows": [[{"t": "", "parts": books}]]})
    # 2) 讀經小挑戰
    if len(tables) > 1:
        rows = parse_dated(tables[1])
        if rows:
            sections.append({"name": "讀經小挑戰", "columns": ["上傳日期", "內容"], "primary": 1, "rows": rows})
    # 3) 聽道筆記
    if len(tables) > 2:
        rows = parse_dated(tables[2])
        if rows:
            sections.append({"name": "聽道筆記", "columns": ["上傳日期", "內容"], "primary": 1, "rows": rows})

    data = {
        "source": SRC, "kicker": "讀經教材",
        "title": "讀經教材", "subtitle": "各卷讀經合併檔、讀經小挑戰與聽道筆記",
        "sections": sections,
        "note": "點書卷或項目開啟 PDF；讀經小挑戰另附家長版／教員版使用說明。",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    for s in sections:
        n = len(s["rows"][0][0]["parts"]) if s["rows"] and isinstance(s["rows"][0][0], dict) and s["rows"][0][0].get("parts") else len(s["rows"])
        print(s["name"], "→", n, "項")
    print("written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
