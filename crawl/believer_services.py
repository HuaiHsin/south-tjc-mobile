# -*- coding: utf-8 -*-
"""解析原站「信徒服務」(/10/index.htm) → data/believer-services.json

原頁結構：
  說明（歡迎信徒提供服務資訊…下載登錄表…）
  分類索引（產品類 / 技術類 / 服務類）
  三個分類表格，每列 7 欄：
    服務種類名稱 | 聯絡人 | 所屬教會 | 公司行號及服務項目 | 聯絡電話 | 手機號碼 | 傳真號碼

重新美編成「同靈商家通訊錄」卡片，依產品/技術/服務分類。連結指回原站。
"""
import re
import os
import sys
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/10/index.htm"
BASE = "http://south.tjc.org.tw/10/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "believer-services.json")
CATS = ["產品類", "技術類", "服務類"]


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("big5", "ignore")


def absolutize(url):
    url = htmllib.unescape(url.strip())
    if url.startswith("http") or url.startswith("mailto:"):
        return url
    if url.startswith("#"):
        return ""
    return BASE + url


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = htmllib.unescape(s).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def cell_link(c):
    m = re.search(r'href="([^"]*)"', c, re.I)
    if not m:
        return None
    url = absolutize(m.group(1))
    if not url:
        return None
    label = clean(re.search(r"<a\b[^>]*>(.*?)</a>", c, re.S | re.I).group(1))
    return {"label": label or url, "url": url}


def main():
    raw = fetch()
    doc = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    doc = re.sub(r"</?(span|o:p|b|i|font)\b[^>]*>", "", doc, flags=re.I)

    # 說明文 + 登錄表連結
    intro = ""
    mi = re.search(r"說明：(.*?)分類索引", doc, re.S)
    if mi:
        intro = clean(re.sub(r"<a\b[^>]*>.*?</a>", "", mi.group(0), flags=re.S | re.I))
        intro = intro.replace("分類索引", "").replace("說明：", "").strip()
    form = None
    mf = re.search(r'<a\b[^>]*href="([^"]*登錄表[^"]*)"', doc, re.I)
    if mf:
        form = {"label": "信徒服務網頁登錄表", "url": absolutize(mf.group(1))}
    mfax = re.search(r"傳真\(([0-9\-]+)\)", doc)
    fax = mfax.group(1) if mfax else ""

    # 逐 <tr> 取 7 欄列；以表頭列切分分類
    groups = []
    cur = None
    for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>", doc, re.S | re.I):
        cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", tr, re.S | re.I)
        if len(cells) != 7:
            continue
        texts = [clean(c) for c in cells]
        if texts[0].replace(" ", "") == "服務種類名稱":   # 表頭 → 新分類
            cur = {"name": CATS[len(groups)] if len(groups) < len(CATS) else "其他", "entries": []}
            groups.append(cur)
            continue
        if cur is None:
            cur = {"name": CATS[0], "entries": []}
            groups.append(cur)
        entry = {
            "type": texts[0], "contact": texts[1], "church": texts[2],
            "desc": texts[3], "phone": texts[4], "mobile": texts[5], "fax": texts[6],
        }
        lk = cell_link(cells[3])
        if lk:
            entry["link"] = lk
        cur["entries"].append(entry)

    data = {"source": SRC, "title": "信徒服務",
            "subtitle": "南區同靈商家・服務通訊錄",
            "intro": intro, "form": form, "office_fax": fax, "categories": groups}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    for g in groups:
        print(g["name"], "→", len(g["entries"]), "筆")
    print("form:", bool(form), "| intro:", len(intro), "字 | fax:", fax)
    print("written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
