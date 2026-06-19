# -*- coding: utf-8 -*-
"""解析原站「教牧資源分享」(/12/index.htm) → data/doc-pastoral.json

單一大表，欄位：股別 | 主題 | 內容(連結，可能多個) | 提供教會
兩層 rowspan（股別跨多列、主題跨數列）。展開後依「股別」切成分區，
每區欄位＝主題 | 內容 | 提供教會。
"""
import re
import os
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/12/index.htm"
BASE = "http://south.tjc.org.tw/12/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "doc-pastoral.json")


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("big5", "ignore")


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s).replace("\xa0", " ")).strip()


def kind_of(url):
    u = url.lower().split("?")[0]
    if "youtube" in u or "youtu.be" in u:
        return "youtube"
    ext = u.rsplit(".", 1)[-1] if "." in u else ""
    return {"pdf": "pdf", "doc": "doc", "docx": "doc", "ppt": "ppt", "pptx": "ppt",
            "pps": "ppt", "xls": "excel", "xlsx": "excel"}.get(ext, "page")


def links_in(frag):
    out = []
    for m in re.finditer(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', frag, re.S | re.I):
        url = htmllib.unescape(m.group(1).strip())
        if url.startswith("#") or not url:
            continue
        if not url.startswith("http"):
            url = BASE + url
        out.append({"label": clean(m.group(2)), "url": url, "kind": kind_of(url)})
    return out


def title_cell(frag):
    lks = links_in(frag)
    if not lks:
        return clean(frag)
    if len(lks) == 1 and clean(frag) == lks[0]["label"]:
        return {"t": lks[0]["label"], "u": lks[0]["url"], "k": lks[0]["kind"]}
    lead = clean(frag)
    for l in lks:
        lead = lead.replace(l["label"], "")
    lead = lead.strip(" 、，,。;；")
    return {"t": lead, "parts": lks}


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
                val = title_cell(raw) if col == link_col else clean(raw)
                row[col] = val
                if rs > 1:
                    carries[col] = {"val": val, "rem": rs - 1}
        grid.append(row)
    return grid


def main():
    raw = fetch()
    b = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    b = re.sub(r"</?(span|o:p|b|i|font)\b[^>]*>", "", b, flags=re.I)
    t = re.search(r"<table\b.*?</table>", b, re.S | re.I).group(0)
    trs = re.findall(r"<tr\b[^>]*>(.*?)</tr>", t, re.S | re.I)
    header = [clean(c) for _, c in parse_cells(trs[0])]    # 股別 主題 內容 提供教會
    grid = expand(trs[1:], 4, link_col=2)

    # 依股別（col0）切分區，保留出現順序
    order, buckets = [], {}
    for row in grid:
        gu = (row[0] or "").replace(" ", "") or "其他"
        if gu not in buckets:
            buckets[gu] = []; order.append(gu)
        buckets[gu].append([row[1], row[2], row[3]])   # 主題 內容 提供教會

    cols = [header[1].replace(" ", ""), header[2].replace(" ", ""), header[3].replace(" ", "")]
    sections = [{"name": gu, "columns": cols, "primary": 1, "rows": buckets[gu]} for gu in order]

    data = {
        "source": SRC, "kicker": "教牧資源分享",
        "title": "教牧資源分享", "subtitle": "各股室主題資源、簡報與表格彙整",
        "sections": sections,
        "note": "點「內容」開啟資源檔（簡報／文件／表格）；資料由各提供教會分享。",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    for s in sections:
        print(s["name"], "→", len(s["rows"]), "則")
    print("cols=", cols, "| written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
