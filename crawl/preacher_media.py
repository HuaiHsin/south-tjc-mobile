# -*- coding: utf-8 -*-
"""解析原站「傳道影音專區」(/13/index.htm) → data/preacher-media.json

原頁結構：
  一、黃志傑傳道靈糧分享：阿傑傳道房   （表格：每格 = 日期+(編號)+國語/台語影片）
  二、黃志傑傳道靈修小語             （表格：每格 = 日期+標題 PDF）
  三、翁正晃傳道 靈糧分享            （同一）
  四、翁正晃傳道靈修小語            （同二）
  五、傳道者聖經講座               （依傳道分組，每人多個系列，系列下多講）

重新美編但盡量保留原版位與格式：日期欄 + 國語/台語並排、靈修小語日期+標題、
聖經講座依傳道分組。連結一律指回原站。
"""
import re
import os
import sys
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/13/index.htm"
BASE = "http://south.tjc.org.tw/13/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "preacher-media.json")


def fetch():
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        return open(sys.argv[1], "rb").read().decode("big5", "ignore")
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("big5", "ignore")


def absolutize(url):
    url = htmllib.unescape(url.strip())
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return BASE + url


def kind_of(url):
    u = url.lower().split("?")[0]
    if "youtube" in u or "youtu.be" in u:
        return "youtube"
    ext = u.rsplit(".", 1)[-1] if "." in u else ""
    return {"pdf": "pdf", "ppt": "ppt", "pptx": "ppt", "pps": "ppt",
            "doc": "doc", "docx": "doc"}.get(ext, "page")


def clean(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = htmllib.unescape(s).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def links_in(frag):
    out = []
    for m in re.finditer(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', frag, re.S | re.I):
        out.append((clean(m.group(2)), absolutize(m.group(1))))
    return out


def split_sections(body):
    """以粗體標頭 一、二、三、四、五 切段，回傳 {num: html_chunk}。"""
    nums = list("一二三四五")
    marks = []
    for n in nums:
        m = re.search(r"<p[^>]*>\s*<b[^>]*>\s*" + n + r"、", body)
        if m:
            marks.append((m.start(), n))
    marks.sort()
    chunks = {}
    for i, (pos, n) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(body)
        chunks[n] = body[pos:end]
    return chunks


def header_text(chunk):
    m = re.search(r"<b[^>]*>\s*[一二三四五]、(.*?)</b>", chunk, re.S)
    return clean(m.group(1)) if m else ""


DATE_RE = re.compile(r"(1\d{2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{1,2})")
NO_RE = re.compile(r"[（(]\s*(\d+)\s*[)）]")


def parse_cells(chunk):
    """回傳每個表格 <td> 的 (text, links)。"""
    cells = []
    for m in re.finditer(r"<td\b[^>]*>(.*?)</td>", chunk, re.S | re.I):
        frag = m.group(1)
        cells.append((clean(frag), links_in(frag)))
    return cells


def parse_sermon(chunk):
    """靈糧分享：每格 = 日期 +(編號) + 國語/台語。"""
    entries = []
    for text, links in parse_cells(chunk):
        if not links:
            continue
        dm = DATE_RE.search(text)
        date = ".".join(dm.groups()) if dm else ""
        nm = NO_RE.search(text)
        no = nm.group(1) if nm else ""
        langs = []
        for label, url in links:
            lm = re.search(r"[（(]\s*(國語|台語)\s*[)）]?", label)
            lang = lm.group(1) if lm else ""
            ref = re.sub(r"\s*[（(]\s*(國語|台語)\s*[)）]?\s*$", "", label).strip()
            langs.append({"lang": lang, "ref": ref, "url": url, "kind": kind_of(url)})
        ref0 = langs[0]["ref"] if langs else ""
        entries.append({"date": date, "no": no, "ref": ref0, "langs": langs})
    return entries


def parse_devotion(chunk):
    """靈修小語：每格 = 日期 + 標題（PDF 或影片）。"""
    entries = []
    for text, links in parse_cells(chunk):
        if not links:
            continue
        dm = DATE_RE.search(text)
        date = ".".join(dm.groups()) if dm else ""
        label, url = links[0]
        entries.append({"date": date, "title": label, "url": url, "kind": kind_of(url)})
    return entries


def parse_lectures(chunk):
    """聖經講座：依傳道分組，標記連結後轉純文字解析。"""
    note = ""
    nm = re.search(r"[（(]\s*(以下影片[^)）]*)\s*[)）]", chunk)
    if nm:
        note = clean(nm.group(1))
    # 連結轉成標記 {{label¦url}}
    def mark(m):
        return " {{" + clean(m.group(2)) + "¦" + absolutize(m.group(1)) + "}} "
    txt = re.sub(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', mark, chunk, flags=re.S | re.I)
    # 換行保留段落
    txt = re.sub(r"</p>", "\n", txt, flags=re.I)
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = htmllib.unescape(txt).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in txt.splitlines()]
    lines = [ln for ln in lines if ln]
    # 丟掉標頭那行
    lines = [ln for ln in lines if not re.match(r"^[一二三四五]、", ln)]

    # 依「姓名行」切成各傳道區塊（姓名單獨成行）
    NAME_RE = re.compile(r"^[一-鿿]{2,5}(?:傳道|執事|長老)$")
    blocks = []
    cur = None
    for ln in lines:
        if NAME_RE.match(ln):
            cur = {"name": ln, "body_lines": []}
            blocks.append(cur)
        elif cur is not None:
            cur["body_lines"].append(ln)

    # 系列：標題：講次、講次…（講次=標記，標題與講次可跨行）
    SERIES_RE = re.compile(r"([^：:；;{}]+?)\s*[：:]\s*((?:\{\{.*?\}\}[\s、,]*)+)", re.S)
    TRIM = "。.，,、；;　 "

    def tidy(s):
        return clean(s).strip(TRIM)

    preachers = []
    for blk in blocks:
        body = " ".join(blk["body_lines"])
        lang = ""
        lm = re.search(r"[（(]\s*(國語|台語)\s*[)）]", body)
        if lm:
            lang = lm.group(1)
        # 移除語言標記，避免混進第一個系列標題
        body = re.sub(r"[（(]\s*(?:國語|台語)\s*[)）]", " ", body)
        series = []
        for title, parts_str in SERIES_RE.findall(body):
            parts = re.findall(r"\{\{(.*?)¦(.*?)\}\}", parts_str)
            if not parts:
                continue
            series.append({"title": tidy(title),
                           "parts": [{"label": tidy(l), "url": u, "kind": kind_of(u)} for l, u in parts]})
        preachers.append({"name": blk["name"], "lang": lang, "series": series})
    return {"note": note, "preachers": preachers}


def main():
    raw = fetch()
    m = re.search(r"<body.*?>(.*)</body>", raw, re.S | re.I)
    body = m.group(1) if m else raw
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    # Word 匯出的 <span>/<o:p> 不帶結構意義，先清掉讓標頭/儲存格規則單純
    body = re.sub(r"<o:p>.*?</o:p>", "", body, flags=re.S | re.I)
    body = re.sub(r"</?(span|o:p)\b[^>]*>", "", body, flags=re.I)

    # 頁面標題與頻道入口
    title = clean(re.search(r"<title>(.*?)</title>", raw, re.S | re.I).group(1)) if re.search(r"<title>", raw, re.I) else "傳道影音專區"
    channel = None
    for label, url in links_in(body):
        if "channel" in url and "youtube" in url:
            channel = {"text": label or "南區頻道 YouTube 入口網站", "url": url}
            break

    chunks = split_sections(body)
    sections = []
    typ = {"一": "sermon", "二": "devotion", "三": "sermon", "四": "devotion", "五": "lecture"}
    for n in "一二三四五":
        if n not in chunks:
            continue
        chunk = chunks[n]
        sec = {"no": n, "title": header_text(chunk), "type": typ[n]}
        if typ[n] == "sermon":
            sec["entries"] = parse_sermon(chunk)
        elif typ[n] == "devotion":
            sec["entries"] = parse_devotion(chunk)
        else:
            lec = parse_lectures(chunk)
            sec["note"] = lec["note"]
            sec["preachers"] = lec["preachers"]
        sections.append(sec)

    data = {"source": SRC, "title": title, "channel": channel, "sections": sections}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 摘要
    for s in sections:
        if s["type"] == "lecture":
            np = len(s["preachers"])
            ns = sum(len(p["series"]) for p in s["preachers"])
            print(f'{s["no"]}、{s["title"]} → {np} 位傳道 / {ns} 系列')
        else:
            print(f'{s["no"]}、{s["title"]} → {len(s["entries"])} 筆')
    print("written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
