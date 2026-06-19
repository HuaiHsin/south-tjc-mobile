# -*- coding: utf-8 -*-
"""解析原站「聖樂活動影音」(/05/index.htm) → data/doc-music.json

原頁每個活動一張表（兒童音樂營 / 青少年音樂營 / 聖樂研習會 / 新年音樂會 /
合唱指揮研習）。表內「年度列」與「影音連結列」交錯，依欄位對齊。
重整為：每活動一分區，每屆一列（年度 + 成果/花絮/大合照 chip）。
"""
import re
import os
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/05/index.htm"
BASE = "http://south.tjc.org.tw/05/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "doc-music.json")


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("big5", "ignore")


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s).replace("\xa0", " ")).strip()


def kind_of(url):
    u = url.lower()
    if "youtube" in u or "youtu.be" in u:
        return "youtube"
    ext = u.split("?")[0].rsplit(".", 1)[-1] if "." in u else ""
    return {"jpg": "image", "jpeg": "image", "png": "image", "gif": "image", "pdf": "pdf"}.get(ext, "page")


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


def parse_cells(tr):
    out = []
    for m in re.finditer(r"<t[dh]\b([^>]*)>(.*?)</t[dh]>", tr, re.S | re.I):
        rs = re.search(r'rowspan=["\']?(\d+)', m.group(1), re.I)
        out.append((int(rs.group(1)) if rs else 1, m.group(2)))
    return out


def parse_event(t):
    event = None
    years, media = [], []
    for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>", t, re.S | re.I):
        cells = parse_cells(tr)
        if not cells:
            continue
        has_link = any("<a" in raw.lower() for _, raw in cells)
        if has_link:
            for _, raw in cells:
                media.append(links_in(raw))
        else:
            for rs, raw in cells:
                if rs > 1:                 # 活動名稱（rowspan）
                    if event is None:
                        event = clean(raw).replace(" ", "")   # 去除 Word 換行造成的空白
                    continue
                years.append(clean(raw))
    rows = []
    for i, y in enumerate(years):
        links = media[i] if i < len(media) else []
        if y and links:
            rows.append([y, {"parts": links}])
    return event or "活動", rows


def main():
    raw = fetch()
    b = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    b = re.sub(r"</?(span|o:p|b|i|font)\b[^>]*>", "", b, flags=re.I)

    channel = None
    for l in links_in(b.split("<table")[0]):
        if "youtube" in l["url"]:
            channel = {"text": l["label"] or "南區聖樂活動 YouTube 入口", "url": l["url"]}
            break

    sections = []
    for t in re.findall(r"<table\b.*?</table>", b, re.S | re.I):
        name, rows = parse_event(t)
        if rows:
            sections.append({"name": name, "columns": ["年度 / 屆別", "影音・相片"], "primary": 1, "rows": rows})

    data = {
        "source": SRC, "kicker": "聖樂活動影音",
        "title": "聖樂活動影音", "subtitle": "歷屆音樂營、研習會與音樂會成果影音、相片",
        "channel": channel, "sections": sections,
        "note": "點各屆「成果／花絮／大合照」開啟影音或相片；亦可由上方 YouTube 入口瀏覽。",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    for s in sections:
        print(s["name"], "→", len(s["rows"]), "屆")
    print("channel:", bool(channel), "| written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
