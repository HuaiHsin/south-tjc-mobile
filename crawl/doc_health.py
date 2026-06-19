# -*- coding: utf-8 -*-
"""解析原站「健康醫訊」(/16/index.htm) → data/doc-health.json

原頁兩張表，每期（上傳日期＋月號）以 rowspan 跨多列，每列數篇文章連結。
重整為「每期一列、文章以 chip 呈現」（共用 renderDocTable，內容欄用 {parts}）。
"""
import re
import os
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/16/index.htm"
BASE = "http://south.tjc.org.tw/16/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "doc-health.json")


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

    issues = []
    cur = None
    for t in re.findall(r"<table\b.*?</table>", b, re.S | re.I):
        for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>", t, re.S | re.I):
            cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", tr, re.S | re.I)
            if not cells:
                continue
            if "上傳日期" in clean(cells[0]):       # 表頭
                continue
            start = 0
            first_txt = clean(cells[0])
            first_link = "<a" in cells[0].lower()
            if not first_link and re.search(r"月號|\d+\.\d+", first_txt):
                cur = {"issue": first_txt, "articles": []}
                issues.append(cur)
                start = 1
            if cur is None:
                continue
            for c in cells[start:]:
                cur["articles"].extend(links_in(c))

    rows = [[it["issue"], {"parts": it["articles"]}] for it in issues if it["articles"]]
    data = {
        "source": SRC, "kicker": "健康醫訊",
        "title": "健康醫訊", "subtitle": "歷期健康・醫療專欄文章彙整",
        "sections": [{"name": "各期健康醫訊", "columns": ["期別", "單元 / 文章"], "primary": 1, "rows": rows}],
        "note": "以上文章為網路流傳轉載（版權為原作者所有），在此向所有作者致上深摯的感謝！",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("期數 →", len(rows), "｜文章總數 →", sum(len(it["articles"]) for it in issues))
    print("written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
