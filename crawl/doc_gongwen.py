# -*- coding: utf-8 -*-
"""解析原站「南區公文」(/02/index.htm) → data/doc-south-gongwen.json（通用表格 schema）

原頁：兩張公文列表（115年 / 114年），每列欄位：
  發文日期 | 字 | 號 | 發文內容(連結) | 公文電子檔上傳對象 | 公文紙本寄送對象
（兩表最後兩欄順序相反，依表頭正規化為 電子檔→紙本）

輸出 schema（共用 renderDocTable）：
  { title, subtitle, kicker, sections:[ {name, columns, primary, rows:[ [cell|{t,u,k}] ]} ] }
"""
import re
import os
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/02/index.htm"
BASE = "http://south.tjc.org.tw/02/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "doc-south-gongwen.json")
COLUMNS = ["發文日期", "字號", "發文內容", "公文電子檔上傳對象", "公文紙本寄送對象"]


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("big5", "ignore")


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = htmllib.unescape(s).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def cell_link(c):
    m = re.search(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', c, re.S | re.I)
    if not m:
        return None
    url = htmllib.unescape(m.group(1).strip())
    if url.startswith("#") or not url:
        return None
    if not url.startswith("http"):
        url = BASE + url
    return {"t": clean(m.group(2)), "u": url, "k": "pdf"}


def sort_key(row):
    """依發文日期（無年份者年=0）再以字號數字排序，供倒敘用。"""
    m = re.match(r"(?:(\d{2,3})[./])?(\d{1,2})[/.](\d{1,2})", row[0] or "")
    date = (int(m.group(1) or 0), int(m.group(2)), int(m.group(3))) if m else (0, 0, 0)
    zh = row[1] if len(row) > 1 and isinstance(row[1], str) else ""
    zn = re.search(r"(\d+)", zh or "")
    return date + (int(zn.group(1)) if zn else 0,)


def parse_table(t):
    trs = re.findall(r"<tr\b[^>]*>(.*?)</tr>", t, re.S | re.I)
    if not trs:
        return []
    head = [clean(c) for c in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", trs[0], re.S | re.I)]
    # 找出最後兩欄：哪個是電子檔、哪個是紙本
    e_idx = next((i for i, h in enumerate(head) if "電子檔" in h), 4)
    p_idx = next((i for i, h in enumerate(head) if "紙本" in h), 5)
    rows = []
    for tr in trs[1:]:
        cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", tr, re.S | re.I)
        if len(cells) < 6:
            continue
        date = clean(cells[0])
        zihao = (clean(cells[1]) + clean(cells[2])).replace(" ", "")
        content = cell_link(cells[3]) or {"t": clean(cells[3])}
        erec = clean(cells[e_idx])
        prec = clean(cells[p_idx])
        rows.append([date, zihao, content, erec, prec])
    return rows


def main():
    raw = fetch()
    b = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    b = re.sub(r"</?(span|o:p|b|i|font)\b[^>]*>", "", b, flags=re.I)
    parts = re.split(r"(<table\b.*?</table>)", b, flags=re.S | re.I)

    sections = []
    pending = None
    for p in parts:
        if p.strip().lower().startswith("<table"):
            rows = parse_table(p)
            if rows:
                rows.sort(key=sort_key, reverse=True)   # 倒敘：最新公文在最上面
                name = pending or "公文列表"
                m = re.search(r"(\d{3}年)", name)
                upd = re.search(r"(\d{1,2}/\d{1,2})\s*更新", name)
                label = (m.group(1) + " 公文列表") if m else name
                if upd:
                    label += "（" + upd.group(1) + " 更新）"
                sections.append({"name": label, "columns": COLUMNS, "primary": 2, "rows": rows})
            pending = None
        else:
            txt = clean(p)
            if "列表" in txt:
                pending = txt

    data = {
        "source": SRC, "kicker": "南區公文",
        "title": "南區公文", "subtitle": "南區與教會相關公文一覽",
        "sections": sections,
        "note": "完整公文電子檔請點「發文內容」開啟；如需紙本請洽所列寄送對象。",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    for s in sections:
        print(s["name"], "→", len(s["rows"]), "則")
    print("written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
