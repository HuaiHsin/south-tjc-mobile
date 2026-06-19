# -*- coding: utf-8 -*-
"""解析原站「宗教教育週海報」(/09/index.htm) → data/doc-reposters.json

原頁每年一張表（2025…2017），各格為一張教會海報連結。
年度標題（114年…107年）夾在各表之間。重整為：每年一列、海報以 chip 呈現。
"""
import re
import os
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/09/index.htm"
BASE = "http://south.tjc.org.tw/09/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "doc-reposters.json")


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

    updated = ""
    mu = re.search(r"(\d{2,3}\.\d{1,2}\.\d{1,2})\s*更新", b)
    if mu:
        updated = mu.group(1)

    parts = re.split(r"(<table\b.*?</table>)", b, flags=re.S | re.I)
    rows = []
    pending_year = ""
    for p in parts:
        if p.strip().lower().startswith("<table"):
            posters = links_in(p)
            if posters:
                label = pending_year or (posters[0]["label"][:4] + " 年度")
                rows.append([label, {"parts": posters}])
            pending_year = ""
        else:
            txt = clean(p)
            ys = re.findall(r"(\d{3}\s*年)", txt)
            if ys:
                pending_year = ys[-1].replace(" ", "")

    data = {
        "source": SRC, "kicker": "宗教教育週海報",
        "title": "宗教教育週海報", "subtitle": "各教會歷年宗教教育週海報", "updated": updated,
        "sections": [{"name": "各年度海報", "columns": ["年度", "各教會海報"], "primary": 1, "rows": rows}],
        "note": "以上為各教會宗教教育週的海報，在此向提供的教會致謝。點海報名稱開啟原站圖檔。",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    for r in rows:
        print(r[0], "→", len(r[1]["parts"]), "張")
    print("updated:", updated, "| written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
