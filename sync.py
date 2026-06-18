#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一鍵同步：從舊站 south.tjc.org.tw 重新產生新站資料。

辦事員照舊用 Word 更新舊站後，志工只要跑這一個指令（或雙擊 sync.bat），
新站的 data/links.json 與 data/announcements.json 就會自動更新。

安全機制：先備份現有資料，三個步驟任一失敗或抓到的資料異常少，
就自動還原舊資料、不覆蓋，確保不會把好好的站弄壞。
"""
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
BACKUP = os.path.join(DATA, ".backup")
DATA_FILES = ["links.json", "announcements.json", "churches.json"]

# 合理下限：低於這些數字代表抓取異常（舊站掛了 / 被擋），不要覆蓋
MIN_LINKS = 200
MIN_GROUPS = 10
MIN_SECTIONS = 4


def run_step(label, script):
    print(f"\n▶ {label} …")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, os.path.join("crawl", script)],
                       cwd=ROOT, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"{label} 失敗（{script} 回傳 {r.returncode}）")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def backup():
    os.makedirs(BACKUP, exist_ok=True)
    for fn in DATA_FILES:
        src = os.path.join(DATA, fn)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(BACKUP, fn))


def restore():
    for fn in DATA_FILES:
        bak = os.path.join(BACKUP, fn)
        if os.path.exists(bak):
            shutil.copy2(bak, os.path.join(DATA, fn))


def main():
    print("=" * 52)
    print("  真耶穌教會南區辦事處官網 — 一鍵同步")
    print("=" * 52)
    print("從舊站抓取最新內容並更新新站資料…")

    os.makedirs(DATA, exist_ok=True)
    backup()

    try:
        run_step("步驟 1/4　爬取舊站全部連結", "crawl.py")
        raw = load_raw()
        if raw < MIN_LINKS:
            raise RuntimeError(f"只抓到 {raw} 條連結（< {MIN_LINKS}），疑似舊站異常，中止以保護現有資料")

        run_step("步驟 2/4　解析各教會通訊錄", "churches.py")

        run_step("步驟 3/4　歸入六大分類", "categorize.py")
        links = load("links.json")
        if links.get("meta", {}).get("groupCount", 0) < MIN_GROUPS:
            raise RuntimeError("分類結果異常，中止")

        run_step("步驟 4/4　解析首頁本月公告", "home_bulletin.py")
        ann = load("announcements.json")
        if len(ann.get("sections", [])) < MIN_SECTIONS:
            raise RuntimeError("公告分區異常，中止")

    except Exception as e:
        print("\n" + "✗" * 3 + f" 同步失敗：{e}")
        restore()
        print("已自動還原為先前的資料，新站維持原狀，未受影響。")
        print("請稍後再試；若持續失敗，可能是舊站連線問題。")
        return 1

    # 成功摘要
    print("\n" + "✓" * 3 + " 同步成功！")
    print(f"  連結總數　：{links['meta']['linkCount']} 條 / {links['meta']['groupCount']} 群組")
    print(f"  本月公告　：{len(ann['sections'])} 個分區")
    for s in ann["sections"]:
        new = "（新區塊，已自動顯示）" if str(s.get("id", "")).startswith("extra") else ""
        print(f"      ・{s['title']}（{s.get('updated') or '—'}）{len(s['items'])} 項{new}")

    # 結構變動提醒：未歸類的新頁面（內容沒掉，但要補一行歸類）
    unmapped = links.get("meta", {}).get("unmapped") or {}
    if unmapped:
        print("\n  ⚠ 注意：發現 %d 個未歸類的新頁面（已暫放「其他資源」，內容沒遺失）：" % len(unmapped))
        for sk, ttl in unmapped.items():
            print(f"      · {sk}（{ttl}）")
        print("    要歸到正確菜單，請在 crawl/categorize.py 的 SOURCE_MAP 加一行（找工程協助）。")

    print("\n新站資料已更新。若要部署到 GitHub Pages，再 push 上去即可。")
    return 0


def load_raw():
    with open(os.path.join(ROOT, "crawl", "raw-links.json"), encoding="utf-8") as f:
        return json.load(f).get("link_count", 0)


if __name__ == "__main__":
    sys.exit(main())
