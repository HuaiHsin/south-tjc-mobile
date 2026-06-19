# -*- coding: utf-8 -*-
"""解析原站「人力資源」(/09/人力資源.htm) → data/doc-hr.json

第一表：宗教教育週邀請講員及專題
  舉辦年度 | 主題(連結) | 專題內容 | 講員(所屬教會) | 邀請教會
  （舉辦年度/主題/邀請教會 以 rowspan 跨多列）→ 依年度分區，欄位＝主題/專題/講員/邀請教會
第二表：信仰生活週之課程規劃  類別 | 課程
"""
import re
import os
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/09/%E4%BA%BA%E5%8A%9B%E8%B3%87%E6%BA%90.htm"
BASE = "http://south.tjc.org.tw/09/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "doc-hr.json")


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("big5", "ignore")


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s).replace("\xa0", " ")).strip()


def kind_of(url):
    u = url.lower().split("?")[0]
    ext = u.rsplit(".", 1)[-1] if "." in u else ""
    return {"jpg": "image", "jpeg": "image", "png": "image", "gif": "image", "pdf": "pdf"}.get(ext, "image")


def link_cell(frag):
    m = re.search(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', frag, re.S | re.I)
    if not m:
        return clean(frag)
    url = htmllib.unescape(m.group(1).strip())
    if url.startswith("#") or not url:
        return clean(frag)
    if not url.startswith("http"):
        url = BASE + url
    return {"t": clean(frag) or clean(m.group(2)), "u": url, "k": kind_of(url)}


def parse_cells(tr):
    out = []
    for m in re.finditer(r"<t[dh]\b([^>]*)>(.*?)</t[dh]>", tr, re.S | re.I):
        rs = re.search(r'rowspan=["\']?(\d+)', m.group(1), re.I)
        out.append((int(rs.group(1)) if rs else 1, m.group(2)))
    return out


def expand(trs, ncol, link_col):
    carries = {}
    grid = []
    for tr in trs:
        cells = parse_cells(tr)
        if not cells:
            continue
        row = [None] * ncol
        ptr = 0
        for col in range(ncol):
            c = carries.get(col)
            if c and c["rem"] > 0:
                row[col] = c["val"]; c["rem"] -= 1; continue
            if ptr < len(cells):
                rs, raw = cells[ptr]; ptr += 1
                row[col] = link_cell(raw) if col == link_col else clean(raw)
                if rs > 1:
                    carries[col] = {"val": row[col], "rem": rs - 1}
        grid.append(row)
    return grid


def main():
    raw = fetch()
    b = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    b = re.sub(r"</?(span|o:p|b|i|font)\b[^>]*>", "", b, flags=re.I)
    tables = re.findall(r"<table\b.*?</table>", b, re.S | re.I)

    # 頂部說明 + 底部參考書籍
    intro = ""
    mi = re.search(r"(南區教會宗教教育週[^<]*?海報內容[^<）)]*[）)])", b)
    if mi:
        intro = clean(mi.group(1))
    note = ""
    flat = clean(re.sub(r"<[^>]+>", " ", b))   # 先轉純文字再抓，避免被標籤截斷
    mn = re.search(r"(參考書籍.{1,400}?上網)", flat)
    if mn:
        note = mn.group(1)

    sections = []
    # 表0：依年度分區
    trs0 = re.findall(r"<tr\b[^>]*>(.*?)</tr>", tables[0], re.S | re.I)
    grid = expand(trs0[1:], 5, link_col=1)
    order, buckets = [], {}
    for row in grid:
        y = (row[0] or "").replace(" ", "") or "其他"
        if y not in buckets:
            buckets[y] = []; order.append(y)
        buckets[y].append([row[1], row[2], row[3], row[4]])
    cols = ["主題", "專題內容", "講員（所屬教會）", "邀請教會"]
    for y in order:
        sections.append({"name": y + " 宗教教育週", "columns": cols, "primary": 0, "rows": buckets[y]})

    # 表1：信仰生活週課程規劃
    if len(tables) > 1:
        trs1 = re.findall(r"<tr\b[^>]*>(.*?)</tr>", tables[1], re.S | re.I)
        rows = []
        for tr in trs1[1:]:
            cs = parse_cells(tr)
            if len(cs) >= 2:
                rows.append([clean(cs[0][1]).replace(" ", ""), clean(cs[1][1])])
        if rows:
            sections.append({"name": "信仰生活週之課程規劃", "columns": ["類別", "課程"], "primary": 0, "rows": rows})

    data = {
        "source": SRC, "kicker": "人力資源",
        "title": "人力資源", "subtitle": "宗教教育週邀請講員、專題與信仰生活週課程規劃",
        "intro": [intro] if intro else [],
        "sections": sections,
        "note": note or "點各「主題」可開啟該場海報。",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    for s in sections:
        print(s["name"], "→", len(s["rows"]), "列")
    print("written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
