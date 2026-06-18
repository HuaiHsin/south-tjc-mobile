# 真耶穌教會南區辦事處官網（手機優化版 DEMO）

原站 [south.tjc.org.tw](http://south.tjc.org.tw) 的手機優先重構版。純 HTML + CSS + 原生 JS，零依賴、零建置。所有連結指向原站既有檔案，後台與下載檔位置不變。

## 本地預覽

需用 HTTP 伺服器開啟（`data/links.json` 走 `fetch`，直接雙擊 `index.html` 會被瀏覽器 CORS 擋）。

```bash
cd D:\TJCsouth
python -m http.server 8899
# 瀏覽器開 http://127.0.0.1:8899/index.html
```

## 部署到 GitHub Pages

1. 建 repo（建議名 `south-tjc-mobile`），把本資料夾內容推上去。
2. Settings → Pages → Source 選 `main` 分支 `/ (root)`。
3. 幾分鐘後得到 `https://<帳號>.github.io/south-tjc-mobile/`，交辦事處審閱。

> 注意：GitHub Pages 只走 HTTPS，而原站目前只有 HTTP（HTTPS 失效，見下）。連結點擊仍可開，但會帶「不安全」標記。原站修好 HTTPS 後，把 `data/links.json` 的 `meta.base` 與各 URL 改為 `https://` 即可。

## 專案結構

```
index.html          首頁（單頁式）
css/styles.css      設計 token + 元件樣式（品牌色：寶藍#0041C4 / 青綠#00B2A2）
js/app.js           載入 links.json、渲染、互動
js/search.js        站內搜尋過濾
data/links.json         全站連結資料（六大分類，單一資料源）
data/announcements.json 本月公告（首頁 6 大分區，含純文字）
data/churches.json      各教會通訊錄（名稱 + 相片/簡介/FB + 地址/電話）
assets/             LOGO（去背 PNG）+ 多尺寸 favicon
crawl/              爬取與分類腳本、盤點報告、驗證截圖（非上線必要）
```

## 資料更新

新增 / 修改連結只需編輯 `data/links.json` 的 `groups[].links[]`，欄位：

```json
{ "text": "顯示標題", "url": "http://south.tjc.org.tw/...", "type": "pdf" }
```

`type` 可選：`pdf` `doc` `excel` `youtube` `image` `external` `archive` `ppt` `mp3` …（控制標籤顏色）。

**本月公告**更新：編輯 `data/announcements.json` 的 `sections[].items[]`，每項可含 `text`（顯示文字，純文字項留空 `links` 即可）與 `links[]`（`{label, url}`）。

重新從原站產生全部資料：一鍵跑 `python sync.py`（或雙擊 `sync.bat`），會依序：
```
crawl.py          # 爬全站連結 + 各頁標題 -> raw-links
churches.py       # 各教會通訊錄 -> data/churches.json
categorize.py     # 歸入四大菜單 -> data/links.json
home_bulletin.py  # 解析首頁公告 -> data/announcements.json
```

### 同步能/不能自動處理什麼

- ✅ **既有結構內的內容變動**（新檔案、新公告、改月份、新教會、移除舊項）→ 完全自動。
- ✅ **首頁新增一個公告區塊**（任何 `XXX：` 開頭的大標）→ home_bulletin 會自動當成新區塊，前端「本月公告」自動顯示，不用改程式。
- ⚠️ **新增一個編號子頁 / 新菜單**（如 `21/防疫專區.htm`）→ 內容不會掉，會用該頁標題自動建群組、暫放「其他資源」最底，並由 `sync.py` 印出提醒；要歸到正確菜單需在 `categorize.py` 的 `SOURCE_MAP` 加一行（工程協助，非辦事員）。

## 功能

- 固定頂部列（LOGO + 站名 + 漢堡選單 + 搜尋）
- 本月活動橫向滑動橫幅
- 6 個常用功能大按鈕
- **本月公告**：原樣還原首頁辦事處每月維護的 6 大分區（特別公告 / 尋人啟示 / 教區活動 / 最新公告 / 宣導事項 / 備查公告），含純文字項目（尋人啟示、劃撥帳號、電子信箱、軟體說明）；信箱與帳號可一鍵複製，尋人啟示與特別公告紅框標示並預設展開
- 六大分類折疊卡（安息日與聚會 / 公文與公告 / 教材與資源 / 教牧與行政 / 影音與靈糧 / 服務與表單）做完整瀏覽
- 大型分類（講義彙編 192、教牧資源 211、傳道影音 246、健康醫訊 126）自動分頁，點「查看全部」進獨立清單
- 全屏站內搜尋，即時過濾標題 / 分類
- 手機 / 平板 / 桌機響應式

> 資訊架構：**本月公告** = 辦事處每月手動維護的「這個月有什麼」（對應原首頁中段內容）；**資訊分類** = 全站 1,500+ 連結的完整歸檔。兩者並存。

## 已知待優化（交辦事處審閱後處理）

1. **HTTPS**：原站 443 連線被重置，目前只有 HTTP。需業主端 IIS 設定憑證。
2. ~~各教會連結脈絡~~（已處理）：各教會的「相片 / 簡介 / FB」已綁回教會名，整理成「各教會通訊錄」（含地址、可點電話），收在「安息日與聚會」分類最底（低變動）。安排表 / 時間表（高變動）則排在分類最前。
3. **`14/` 深層頁內容**：原站 `14/` 標題為「最新公告」但實為汽車生活小百科，已歸入公文與公告分類，建議業主確認去留。（首頁真正的「最新公告」分區已在「本月公告」中原樣呈現，與此頁無關。）
4. 連結量大的分類，未來可再細分子類。
