# -*- coding: utf-8 -*-
"""解析原站「講義彙編」(/08/index.htm) → data/doc-handout.json

原頁四分類（事工類 / 生活類 / 查經類 / 靈修類），每表欄位：
  上傳日期 | 題目(連結，可能多個) | 作者 | 授課場次(或使用時機)
表格大量使用 rowspan：同一日期/場次跨多列；少欄列需向上繼承。

輸出共用 renderDocTable schema；題目多連結時用 {t, parts:[{label,url,kind}]}。
"""
import re
import os
import json
import html as htmllib
import urllib.request

SRC = "http://south.tjc.org.tw/08/index.htm"
BASE = "http://south.tjc.org.tw/08/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "doc-handout.json")


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("big5", "ignore")


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s).replace("\xa0", " ")).strip()


def kind_of(url):
    u = url.lower().split("?")[0]
    if "youtube" in u or "youtu.be" in u:
        return "youtube"
    ext = u.rsplit(".", 1)[-1] if "." in u else ""
    return {"pdf": "pdf", "doc": "doc", "docx": "doc", "ppt": "ppt", "pptx": "ppt",
            "pps": "ppt", "xls": "excel", "xlsx": "excel"}.get(ext, "page")


def links_in(frag):
    out = []
    for m in re.finditer(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', frag, re.S | re.I):
        url = htmllib.unescape(m.group(1).strip())
        if url.startswith("#") or not url:
            continue
        if not url.startswith("http"):
            url = BASE + url
        out.append({"label": clean(m.group(2)), "url": url, "kind": kind_of(url)})
    return out


def title_cell(frag):
    lks = links_in(frag)
    if not lks:
        return clean(frag)
    if len(lks) == 1 and clean(frag) == lks[0]["label"]:
        return {"t": lks[0]["label"], "u": lks[0]["url"], "k": lks[0]["kind"]}
    # 多連結：保留前導文字 + 各連結 chip
    lead = clean(frag)
    for l in lks:
        lead = lead.replace(l["label"], "")
    lead = lead.strip(" 、，,。;；")
    return {"t": lead, "parts": lks}


def parse_cells(tr):
    """回傳該列各 <td> 的 (rowspan, raw_html)。"""
    cells = []
    for m in re.finditer(r"<t[dh]\b([^>]*)>(.*?)</t[dh]>", tr, re.S | re.I):
        rs = re.search(r'rowspan=["\']?(\d+)', m.group(1), re.I)
        cells.append((int(rs.group(1)) if rs else 1, m.group(2)))
    return cells


def parse_table(t):
    trs = re.findall(r"<tr\b[^>]*>(.*?)</tr>", t, re.S | re.I)
    if not trs:
        return None, []
    header = [clean(c) for _, c in parse_cells(trs[0])]
    ncol = len(header)
    if ncol < 2:
        return None, []
    carries = {}   # col -> {"val":cell, "rem":n}
    rows = []
    for tr in trs[1:]:
        cells = parse_cells(tr)
        if not cells:
            continue
        result = [None] * ncol
        ptr = 0
        for col in range(ncol):
            c = carries.get(col)
            if c and c["rem"] > 0:
                result[col] = c["val"]
                c["rem"] -= 1
                continue
            if ptr < len(cells):
                rs, raw = cells[ptr]; ptr += 1
                val = title_cell(raw) if col == 1 else clean(raw)
                result[col] = val
                if rs > 1:
                    carries[col] = {"val": val, "rem": rs - 1}
        rows.append(result)
    return header, rows


def main():
    raw = fetch()
    b = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    b = re.sub(r"</?(span|o:p|b|i|font)\b[^>]*>", "", b, flags=re.I)
    parts = re.split(r"(<table\b.*?</table>)", b, flags=re.S | re.I)

    sections = []
    pending = None
    for p in parts:
        if p.strip().lower().startswith("<table"):
            header, rows = parse_table(p)
            if rows:
                name = pending or "講義"
                sections.append({"name": name, "columns": header, "primary": 1, "rows": rows})
            pending = None
        else:
            txt = clean(p)
            m = re.search(r"([事工生活靈修查經]+類)\s*[：:]", txt)
            if m:
                pending = m.group(1)

    data = {
        "source": SRC, "kicker": "講義彙編",
        "title": "講義彙編", "subtitle": "歷年進修會、講座講義與簡報彙整",
        "sections": sections,
        "note": "點「題目」開啟講義（PDF／簡報／影音）；部分含 QR-Code 版本。",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    for s in sections:
        miss = sum(1 for r in s["rows"] if not r[0])
        print(s["name"], "→", len(s["rows"]), "則（缺日期", miss, "） cols=", s["columns"])
    print("written:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
