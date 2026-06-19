# -*- coding: utf-8 -*-
"""解析原站「最新公告」(/14/index.htm，實為『生活資訊』) → data/doc-life.json

單表，欄位：上傳日期 | 類別 | 單元題目（多篇文章連結）
上傳日期、類別以 rowspan 跨多列。重整為一表：每（日期＋類別）一列，文章以 chip。
"""
import re
import os
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/14/index.htm"
BASE = "http://south.tjc.org.tw/14/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "doc-life.json")


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


def main():
    raw = fetch()
    b = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    b = re.sub(r"</?(span|o:p|b|i|font)\b[^>]*>", "", b, flags=re.I)
    t = re.search(r"<table\b.*?</table>", b, re.S | re.I).group(0)
    trs = re.findall(r"<tr\b[^>]*>(.*?)</tr>", t, re.S | re.I)

    groups = []
    cur = None
    for tr in trs:
        cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", tr, re.S | re.I)
        if not cells or "上傳日期" in clean(cells[0]):
            continue
        idx = 0
        first_link = "<a" in cells[0].lower()
        if not first_link and re.search(r"\d+\.\d+|改版", clean(cells[0])):
            date = clean(cells[0]); idx = 1
            cat = ""
            if len(cells) > 1 and "<a" not in cells[1].lower():
                cat = clean(cells[1]); idx = 2
            cur = {"date": date, "cat": cat, "articles": []}
            groups.append(cur)
        if cur is None:
            continue
        for c in cells[idx:]:
            cur["articles"].extend(links_in(c))

    rows = [[g["date"], g["cat"], {"parts": g["articles"]}] for g in groups if g["articles"]]
    data = {
        "source": SRC, "kicker": "生活資訊",
        "title": "生活資訊", "subtitle": "生活、健康類實用文章彙整（原站選單為「最新公告」）",
        "sections": [{"name": "生活資訊", "columns": ["上傳日期", "類別", "單元 / 文章"], "primary": 2, "rows": rows}],
        "note": "以上文章或簡報為網路流傳轉載（版權為原作者所有），在此對所有作者致上深摯的感謝！",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    for g in groups:
        print(g["date"], "/", g["cat"], "→", len(g["articles"]), "篇")
    print("written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
