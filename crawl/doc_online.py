# -*- coding: utf-8 -*-
"""解析原站「線上靈糧」(/15/index.htm) → data/doc-online.json

原頁為分組連結清單（❤️聯總 / 台總 / 宗教教育課程 / 台灣北區 / 各國…），
含子標題（Northwest Region 等）與備註。重整為：每組一分區，每頻道一列
（教會/頻道 連結 + 備註），共用 renderDocTable。
"""
import re
import os
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/15/index.htm"
BASE = "http://south.tjc.org.tw/15/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "doc-online.json")


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
    # 連結轉標記
    b = re.sub(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
               lambda m: "{{" + re.sub(r"<[^>]+>", "", m.group(2)).strip() + "->" + htmllib.unescape(m.group(1).strip()) + "}}",
               b, flags=re.S | re.I)
    b = re.sub(r"</p>|</tr>|<br[^>]*>", "\n", b, flags=re.I)
    b = re.sub(r"<[^>]+>", " ", b)
    b = htmllib.unescape(b).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in b.splitlines()]
    lines = [ln for ln in lines if ln]

    sections = []
    cur = None
    top = ""

    def new_section(name):
        s = {"name": name, "columns": ["教會 / 頻道", "備註"], "primary": 0, "rows": []}
        sections.append(s)
        return s

    for ln in lines:
        if "線上直播" in ln or ln.startswith("線上靈糧"):
            continue
        if "❤" in ln:
            name = re.sub(r"[❤️\s:：]+", "", ln).strip()
            if name:
                top = name
                cur = new_section(name)
            continue
        marks = re.findall(r"\{\{(.*?)->(.*?)\}\}", ln)
        if marks:
            if cur is None:
                cur = new_section("線上頻道")
            label, url = marks[0]
            if not label or "index.htm" in url or url.startswith("#"):
                continue
            note = ln
            for lb, u in marks:
                note = note.replace("{{" + lb + "->" + u + "}}", "")
            note = re.sub(r"\(\s*https?://[^)]*\)?", "", note)   # 去掉重複的網址 echo
            note = re.sub(r"^\s*\d+\s*[.\)、]", "", note)        # 去掉清單編號 1. 2.
            note = note.strip(" ※•.()（）:：、 ")
            if re.fullmatch(r"\d*", note):                       # 純數字/空 → 無備註
                note = ""
            cur["rows"].append([{"t": label, "u": url, "k": kind_of(url)}, note])
        else:
            t = ln.strip(" ※•:：")
            if t.startswith("(http") or re.match(r"^https?://", t) or t.startswith("("):
                continue
            if 1 < len(t) < 40:                 # 子標題（地區/Region…）
                cur = new_section((top + " · " + t) if top and top not in t else t)

    # 移除空分區
    sections = [s for s in sections if s["rows"]]
    data = {
        "source": SRC, "kicker": "線上靈糧",
        "title": "線上靈糧", "subtitle": "各地教會線上直播・聚會頻道彙整",
        "sections": sections,
        "note": "點教會/頻道名稱開啟線上聚會或直播連結；各連結由原站提供。",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    for s in sections:
        print(s["name"], "→", len(s["rows"]))
    print("共", len(sections), "區 | written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
