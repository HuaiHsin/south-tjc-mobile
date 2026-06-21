/*
 * 原站 → 新版（手機/桌機最佳化版）跳轉提示
 * 用法：在原站 index.htm（big5）的 </body> 前加入一行（純 ASCII，不受編碼影響）：
 *   <script src="https://huaihsin.github.io/south-tjc-mobile/redirect.js"></script>
 * 行為：進站時彈出詢問「前往新版 / 留在舊版」；選擇後 30 天內不再詢問。
 * 文案要改直接改本檔即可，原站不必再動。
 */
(function () {
  "use strict";
  var NEW_URL = "https://huaihsin.github.io/south-tjc-mobile/";
  var KEY = "tjcSouthRedirectChoice";
  var REMEMBER_DAYS = 30;

  // 已在 GitHub Pages（新版）本身就不要再跳
  if (location.host.indexOf("huaihsin.github.io") >= 0) return;

  // 最近已選擇過 → 不再打擾
  try {
    var saved = parseInt(window.localStorage.getItem(KEY), 10);
    if (saved && (Date.now() - saved) < REMEMBER_DAYS * 86400000) return;
  } catch (e) { /* localStorage 不可用就照常顯示 */ }

  function remember() {
    try { window.localStorage.setItem(KEY, String(Date.now())); } catch (e) {}
  }

  function show() {
    if (document.getElementById("tjc-redirect")) return;
    var ov = document.createElement("div");
    ov.id = "tjc-redirect";
    ov.setAttribute("role", "dialog");
    ov.style.cssText =
      "position:fixed;left:0;top:0;right:0;bottom:0;z-index:2147483647;" +
      "background:rgba(16,35,63,.55);display:flex;align-items:center;justify-content:center;" +
      'padding:20px;font-family:"Microsoft JhengHei","PingFang TC","Noto Sans TC",sans-serif;' +
      "-webkit-text-size-adjust:100%;";

    var box = document.createElement("div");
    box.style.cssText =
      "background:#fff;max-width:380px;width:100%;border-radius:16px;" +
      "box-shadow:0 18px 50px rgba(0,0,0,.32);overflow:hidden;animation:tjcPop .2s ease;";
    box.innerHTML =
      '<div style="background:#0041C4;color:#fff;padding:17px 22px;font-size:18px;font-weight:bold;letter-spacing:.5px;">' +
        '真耶穌教會南區辦事處</div>' +
      '<div style="padding:22px 22px 18px;color:#333;font-size:15px;line-height:1.75;">' +
        '本站已推出<b style="color:#0041C4;">手機 / 電腦最佳化新版</b>，' +
        '畫面更清楚、查詢更方便。<br>是否前往新版網站？</div>' +
      '<div style="display:flex;gap:10px;padding:0 22px 14px;">' +
        '<button id="tjc-stay" style="flex:1;padding:12px;border:1px solid #d2d8e4;border-radius:10px;' +
          'background:#f4f6fb;color:#444;font-size:15px;cursor:pointer;font-family:inherit;">留在舊版</button>' +
        '<button id="tjc-go" style="flex:1.5;padding:12px;border:0;border-radius:10px;' +
          'background:#0041C4;color:#fff;font-size:15px;font-weight:bold;cursor:pointer;font-family:inherit;">前往新版 →</button>' +
      '</div>' +
      '<div style="padding:0 22px 18px;color:#9aa3b2;font-size:12px;line-height:1.5;text-align:center;">' +
        '（選擇後 30 天內不再詢問）</div>';

    ov.appendChild(box);
    document.body.appendChild(ov);

    var style = document.createElement("style");
    style.textContent = "@keyframes tjcPop{from{opacity:0;transform:translateY(8px) scale(.98)}to{opacity:1;transform:none}}";
    document.head.appendChild(style);

    document.getElementById("tjc-go").onclick = function () {
      remember();
      window.location.href = NEW_URL;
    };
    document.getElementById("tjc-stay").onclick = function () {
      remember();
      if (ov.parentNode) ov.parentNode.removeChild(ov);
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", show);
  } else {
    show();
  }
})();
