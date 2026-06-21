#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A3+A5: categorize raw-links into 6 categories -> data/links.json
Owner-confirmed decisions:
  18 南區AI指引 -> 教材與資源 ; 19 真光園區 -> 教牧與行政
  13/12/08/16 -> paginated (own sub-page)
"""
import json, re, os, urllib.parse
from collections import OrderedDict

RAW = json.load(open("crawl/raw-links.json", encoding="utf-8"))
BASE = "http://south.tjc.org.tw/"

CATEGORIES = [
    {"id": "official", "name": "公文/安排表", "icon": "doc"},
    {"id": "spirit",   "name": "線上靈糧",   "icon": "book"},
    {"id": "activity", "name": "活動與團契", "icon": "users"},
    {"id": "other",    "name": "其他資源",   "icon": "form"},
]

# source page path -> (category, group title, paginated)
SOURCE_MAP = {
    "01/index.htm":            ("official", "安息日領會表",    False),
    "02/index.htm":            ("official", "南區公文",       False),
    # 03 各教會頁改由 churches.py 解析成通訊錄，這裡不收散落的相片/簡介/FB
    "04/index-1.htm":          ("activity", "校園團契",       False),
    # 外地學生住宿資訊：併入「校園團契」整頁（放該頁下方），不再單獨成「其他資源」群組
    "04/提供外地同靈住宿資訊表.htm": ("activity", "校園團契",       False),
    "05/index.htm":            ("activity", "聖樂活動影音",     False),
    "06/讀經教材.htm":           ("spirit",   "讀經教材",       False),
    "08/index.htm":            ("spirit",   "講義彙編",       True),
    "09/index.htm":            ("activity", "宗教教育週海報",   False),
    "09/人力資源.htm":           ("activity", "人力資源",       False),
    "10/index.htm":            ("other",    "信徒服務",       False),
    "11/index.htm":            ("other",    "好站連結",       False),
    "12/index.htm":            ("activity", "教牧資源分享",     True),
    "13/index.htm":            ("spirit",   "傳道靈糧分享",     True),
    "14/人力資源.htm":           ("activity", "人力資源",       False),
    "15/index.htm":            ("spirit",   "線上靈糧",       False),
    "17/index.htm":            ("official", "總會公文",       False),
    "18/index.htm":            ("spirit",   "南區AI指引",      False),
    "18/index1.htm":           ("spirit",   "AI智能體使用備註",  False),
    "18/index2.htm":           ("spirit",   "AI智能體使用備註",  False),
    "18/index3.htm":           ("spirit",   "AI智能體使用備註",  False),
    "18/index4.htm":           ("spirit",   "AI智能體使用備註",  False),
    "19/index.htm":            ("other",    "真光園區",       False),
    "20/index.htm":            ("official", "高屏小區公文",     False),
}

HOME_SOURCES = {"(home)", "index.htm", "index2.htm"}
# 各教會頁：散落的「相片/簡介/FB」連結不收進分類，改用 churches.json 通訊錄呈現
# 07/index.htm（家護園地）、14/index.htm（原「最新公告」實為生活資訊）、16/index.htm（健康醫訊）：
# 非原站正式導覽頁、屬孤立內容，業主確認移除
# 17/index.htm（總會公文）：內容皆為 2019 舊資料，業主確認隱藏整頁
SKIP_SOURCES = {"03/index.htm", "03/index1.htm", "03/index2.htm",
                "07/index.htm", "14/index.htm", "16/index.htm",
                "17/index.htm"}

# 業主指定隱藏的個別連結（舊年度資料）：以 BASE 去除並解碼後的相對路徑比對
SKIP_URLS = {
    "公告附件/有時效性公告/112年南區行事曆.pdf",
    "公告附件/有時效性公告/112年南區駐牧安排表.pdf",
}


# 依附圖的菜單順序：每個一級菜單下，圖中列出的二級項目排在最前（其餘折進來的排後面）
ORDER = {
    # 公文/安排表
    "南區公文": 1, "高屏小區公文": 2, "安息日領會表": 3, "聚會與時間表": 4,
    # 線上靈糧
    "南區AI指引": 1, "讀經教材": 2, "講義彙編": 3, "線上靈糧": 4, "傳道靈糧分享": 5,
    # 活動與團契
    "人力資源": 1, "宗教教育週海報": 2, "聖樂活動影音": 3, "校園團契": 4,
    # 其他資源
    "教會地址": 1, "真光園區": 2, "好站連結": 3,
}


def group_order(title):
    """圖中列出的項目用指定順序排前；未列的折入項給 50，排在後面（再依大小）。"""
    return ORDER.get(title, 50)


def short(u):
    return u.replace(BASE, "")


def src_key(l):
    return urllib.parse.unquote(l["source"].replace(BASE, "")) or "(home)"


def classify_home(l):
    """Return (category_id, group_title) for a homepage curated link."""
    u = short(l["url"])
    t = l["text"]
    blob = u + " " + t
    # AI 智能體 (external ChatGPT/Gemini) -> 線上靈糧
    if "chatgpt.com" in u or "gemini.google" in u:
        return ("spirit", "AI 靈修智能體")
    # 安息日領會表 (01/ months) -> 公文/安排表
    if u.startswith("01/"):
        return ("official", "安息日領會表")
    # 聚會 / 早禱 / 靈恩佈道會 -> 公文/安排表
    if any(k in blob for k in ["聚會時間表", "早禱會", "靈恩佈道會", "靈恩會"]):
        return ("official", "聚會與時間表")
    # 駐牧 / 負責人 / 電話分機 / 行事曆 -> 公文/安排表
    if any(k in blob for k in ["駐牧", "負責人名單", "電話分機", "行事曆"]):
        return ("official", "教牧行政文件")
    # 讚美詩投影 / 聖經章節投放 / App -> 其他資源
    if any(k in blob for k in ["讚美詩歌詞", "聖經章節投放", "讚美詩App", "讚美詩 App"]):
        return ("other", "投影與軟體")
    # 志工 / 受洗 / 租屋 / 劃撥 / 捷運 / LOGO / 住宿 -> 其他資源
    if any(k in blob for k in ["志工服務證明", "受洗", "除偶像", "租屋", "劃撥", "捷運", "LOGO", "報名網址", "住宿"]):
        return ("other", "申請表單與服務")
    # 總會來文 -> 總會宣導 (公文/安排表)
    if u.startswith("總會來文"):
        return ("official", "總會宣導事項")
    # 02/ 活動 pdf -> 教區活動預告 (活動與團契)
    if u.startswith("02/"):
        return ("activity", "教區活動預告")
    # 生命體驗營等活動附件 -> 活動與團契
    if "生命體驗營" in u or "活動簡章" in t or "課程表" in t:
        return ("activity", "教區活動預告")
    # fallback
    return ("official", "其他公告")


def main():
    groups = OrderedDict()  # key -> group dict

    def get_group(gid, title, cat, paginated, order=None):
        if gid not in groups:
            groups[gid] = {"id": gid, "title": title, "category": cat,
                           "paginated": paginated,
                           "order": order if order is not None else group_order(title),
                           "links": []}
        return groups[gid]

    PAGE_TITLES = RAW.get("page_titles", {})
    unmapped = {}  # 安全網：未對映的新頁面 -> 標題

    seen = set()
    for l in RAW["links"]:
        if l["type"] == "page":
            continue  # navigation / section links, excluded from content
        sk = src_key(l)
        if sk in SKIP_SOURCES:
            continue  # 各教會頁 -> 改用通訊錄
        if urllib.parse.unquote(short(l["url"])) in SKIP_URLS:
            continue  # 業主指定隱藏的舊年度連結
        order = None
        if sk in HOME_SOURCES:
            cat, title = classify_home(l)
            paginated = False
        elif sk in SOURCE_MAP:
            cat, title, paginated = SOURCE_MAP[sk]
        else:
            # 安全網：未知的新頁面 -> 用該頁標題自動建群組，暫放「其他資源」最底，並記下待提醒
            title = PAGE_TITLES.get(sk) or ("新頁面 " + sk)
            cat, paginated, order = "other", False, 90
            unmapped[sk] = title
        # merge groups by category+title (collapses 18/index1-4, dup 人力資源, home groups)
        gid = cat + "|" + title
        # dedupe by (gid, url, text)
        key = (gid, l["url"], l["text"])
        if key in seen:
            continue
        seen.add(key)
        g = get_group(gid, title, cat, paginated, order)
        item = {"text": l["text"] or "(未命名連結)", "url": l["url"], "type": l["type"]}
        g["links"].append(item)

    cat_order = {c["id"]: i for i, c in enumerate(CATEGORIES)}
    glist = list(groups.values())
    glist = [g for g in glist if g["links"]]

    def year_in(url):
        m = re.search(r"(\d{2,3})年", urllib.parse.unquote(url))
        return int(m.group(1)) if m else -1

    for g in glist:
        # 1) 同一檔案連結去重（同 URL 只留一筆，例如 6月 同時被首頁與 01 頁連到）
        seen_u, dl = set(), []
        for l in g["links"]:
            if l["url"] in seen_u:
                continue
            seen_u.add(l["url"]); dl.append(l)
        g["links"] = dl

        # 2) 聚會與時間表：同名項只留最新年份（修正聚會時間表 / 早禱會重複）
        if g["title"] == "聚會與時間表":
            chosen, order = {}, []
            for l in g["links"]:
                t = l["text"]
                if t not in chosen:
                    chosen[t] = l; order.append(t)
                elif year_in(l["url"]) > year_in(chosen[t]["url"]):
                    chosen[t] = l
            g["links"] = [chosen[t] for t in order]

        # 3) 安息日領會表：只顯示「當年度」全 12 個月，沒安排的月份留空，同月 W/P 並排
        if g["title"] == "安息日領會表":
            files_by = {}  # (year, month) -> [files]
            for l in g["links"]:
                m = re.search(r"(\d{2,3})年(\d{1,2})月", urllib.parse.unquote(l["url"]))
                if not m:
                    continue
                yr, mo = int(m.group(1)), int(m.group(2))
                fmt = "W檔" if l["type"] in ("doc", "docx") else "PDF"
                files_by.setdefault((yr, mo), []).append({"kind": fmt, "url": l["url"], "type": l["type"]})
            if files_by:
                latest = max(k[0] for k in files_by)  # 當年度（最新年份）
                months = []
                for mo in range(1, 13):
                    fs = files_by.get((latest, mo), [])
                    fs.sort(key=lambda f: 0 if f["kind"] == "W檔" else 1)
                    months.append({"year": latest, "month": mo, "label": f"{mo}月", "files": fs})
                g["kind"] = "schedule"
                g["months"] = months
                g["latestYear"] = latest
                # 只保留當年度的連結（供搜尋用），丟掉舊年份
                g["links"] = [l for l in g["links"]
                              if ("%d年" % latest) in urllib.parse.unquote(l["url"])]

    # Inject single church directory group (低變動，沉到分類最底) with per-district buttons
    try:
        ch = json.load(open("data/churches.json", encoding="utf-8"))
        dists = [d for d in ch.get("districts", []) if d.get("churches")]
        dists.sort(key=lambda d: 0 if "高屏" in d["name"] else 1)  # 高屏、台南
        if dists:
            glist.append({
                "id": "other|教會地址",
                "title": "教會地址",
                "category": "other", "paginated": True, "order": ORDER.get("教會地址", 1),
                "kind": "directory", "links": [],
                "districts": [{"name": d["name"], "churches": d["churches"]} for d in dists],
            })
    except FileNotFoundError:
        print("warn: churches.json 不存在，先跑 crawl/churches.py")

    def gsize(g):
        if g.get("districts"):
            return sum(len(d["churches"]) for d in g["districts"])
        return len(g.get("churches") or g.get("links") or [])

    # Sort: category order -> group order (安排表前/通訊錄後) -> size desc
    glist.sort(key=lambda g: (cat_order.get(g["category"], 99),
                              g.get("order", 5),
                              -gsize(g)))

    # quick access (curated)
    quick = [
        {"title": "安息日領會表", "category": "official", "icon": "calendar"},
        {"title": "聚會時間表",   "url": BASE + "公告附件/永久性公告/各教會聚會時間表--115.4.2更新.pdf", "icon": "clock"},
        {"title": "最新公告",     "category": "official", "icon": "bell"},
        {"title": "讚美詩投影",   "category": "other",    "icon": "music"},
        {"title": "教會地址",     "category": "other",    "icon": "users"},
        {"title": "線上靈糧",     "category": "spirit",   "icon": "book"},
    ]

    out = {
        "meta": {
            "site": "south.tjc.org.tw",
            "base": BASE,
            "note": "連結指向原站;HTTPS 修復後將 base 改為 https 即可全站切換",
            "generated": "2026-06-12",
            "linkCount": sum(gsize(g) for g in glist),
            "groupCount": len(glist),
            "unmapped": unmapped,
        },
        "categories": CATEGORIES,
        "quickAccess": quick,
        "groups": glist,
    }
    os.makedirs("data", exist_ok=True)
    json.dump(out, open("data/links.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # report
    from collections import Counter
    by_cat = Counter()
    for g in glist:
        by_cat[g["category"]] += gsize(g)
    print("groups:", len(glist), "links:", out["meta"]["linkCount"])
    for c in CATEGORIES:
        gs = [g for g in glist if g["category"] == c["id"]]
        print(f"\n[{c['name']}] {by_cat[c['id']]} / {len(gs)} groups")
        for g in gs:
            tags = []
            if g.get("kind") == "directory":
                tags.append("通訊錄")
            if g["paginated"]:
                tags.append("分頁")
            tag = (" (" + "/".join(tags) + ")") if tags else ""
            print(f"    - [{g.get('order',5)}] {g['title']}: {gsize(g)}{tag}")

    # 安全網提醒：發現未歸類的新頁面
    if unmapped:
        print("\n" + "!" * 60)
        print(f"⚠ 發現 {len(unmapped)} 個未歸類的新頁面（已暫放「其他資源」最底，內容未遺失）：")
        for sk, ttl in unmapped.items():
            print(f"    · {sk}　（{ttl}）")
        print("  → 請在 crawl/categorize.py 的 SOURCE_MAP 加一行，指定它要放哪個菜單。")
        print("!" * 60)


if __name__ == "__main__":
    main()
