# -*- coding: utf-8 -*-
"""解析原站「高屏小區公文」(/20/index.htm) → data/doc-gaoping-gongwen.json

單一表格，欄位：發文日期 | 主旨(連結) | 舉辦地點 | 報名期限
"""
import re
import os
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/20/index.htm"
BASE = "http://south.tjc.org.tw/20/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "doc-gaoping-gongwen.json")
COLUMNS = ["發文日期", "主旨", "舉辦地點", "報名期限"]


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("big5", "ignore")


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s).replace("\xa0", " ")).strip()


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


def main():
    raw = fetch()
    b = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    b = re.sub(r"</?(span|o:p|b|i|font)\b[^>]*>", "", b, flags=re.I)
    t = re.search(r"<table\b.*?</table>", b, re.S | re.I).group(0)
    trs = re.findall(r"<tr\b[^>]*>(.*?)</tr>", t, re.S | re.I)
    rows = []
    for tr in trs[1:]:
        cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", tr, re.S | re.I)
        if len(cells) < 4:
            continue
        subj = cell_link(cells[1]) or {"t": clean(cells[1])}
        rows.append([clean(cells[0]), subj, clean(cells[2]), clean(cells[3])])

    data = {
        "source": SRC, "kicker": "高屏小區公文",
        "title": "高屏小區公文", "subtitle": "高屏小區聚會、活動通知一覽",
        "sections": [{"name": "高屏小區公文列表", "columns": COLUMNS, "primary": 1, "rows": rows}],
        "note": "點「主旨」開啟公文電子檔；請留意各案報名期限。",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("高屏小區公文 →", len(rows), "則")
    print("written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
