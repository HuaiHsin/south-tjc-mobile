# -*- coding: utf-8 -*-
"""解析原站「好站連結」(/11/index.htm) → data/doc-links.json

原頁分組連結（各國網站 / 台總網站 / 教區網站…），多數連結後附（說明）。
重整為：每組一分區，每站一列（網站連結 + 說明），共用 renderDocTable。
"""
import re
import os
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/11/index.htm"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "doc-links.json")


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("big5", "ignore")


def kind_of(url):
    u = url.lower()
    if "youtube" in u or "youtu.be" in u:
        return "youtube"
    return "external"


def main():
    raw = fetch()
    b = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    b = re.sub(r"</?(span|o:p|b|i|font)\b[^>]*>", "", b, flags=re.I)
    b = re.sub(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
               lambda m: "{{" + re.sub(r"<[^>]+>", "", m.group(2)).strip() + "->" + htmllib.unescape(m.group(1).strip()) + "}}",
               b, flags=re.S | re.I)
    b = re.sub(r"</p>|</tr>|<br[^>]*>|</td>", "\n", b, flags=re.I)
    b = re.sub(r"<[^>]+>", " ", b)
    b = htmllib.unescape(b).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in b.splitlines()]
    lines = [ln for ln in lines if ln]

    sections = []
    cur = None

    def new_section(name):
        s = {"name": name, "columns": ["網站", "說明"], "primary": 0, "rows": []}
        sections.append(s)
        return s

    MARK = re.compile(r"\{\{(.*?)->(.*?)\}\}\s*([（(][^）)]*[）)])?")
    for ln in lines:
        if ln.startswith("好站連結") or ln == "好 站 連 結":
            continue
        has_mark = "{{" in ln
        # 區段標題：以「：」結尾且無連結
        if not has_mark and ln.endswith(("：", ":")):
            cur = new_section(ln.rstrip("：:").strip())
            continue
        if has_mark:
            if cur is None:
                cur = new_section("好站連結")
            # 行首若有「XX網站：」當標題
            head = re.match(r"^([^：:{}]{2,12}網站)\s*[：:]", ln)
            if head:
                cur = new_section(head.group(1))
            for m in MARK.finditer(ln):
                label, url, desc = m.group(1), m.group(2), m.group(3) or ""
                if not label or "index.htm" in url or url.startswith("#"):
                    continue
                desc = desc.strip("（）() ").strip()
                cur["rows"].append([{"t": label, "u": url, "k": kind_of(url)}, desc])

    sections = [s for s in sections if s["rows"]]
    data = {
        "source": SRC, "kicker": "好站連結",
        "title": "好站連結", "subtitle": "聯總、台總、教區及各地教會實用網站",
        "sections": sections,
        "note": "點網站名稱於新分頁開啟；說明摘自原站。",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    for s in sections:
        print(s["name"], "→", len(s["rows"]), "站")
    print("written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
