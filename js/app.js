/* Main app: load data, render editorial homepage, wire interactions. */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = window.TJCSearch.escapeHtml;

  var ICONS = {
    calendar: '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 2v4M16 2v4"/></svg>',
    doc: '<svg viewBox="0 0 24 24"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/></svg>',
    book: '<svg viewBox="0 0 24 24"><path d="M4 4h12a2 2 0 0 1 2 2v14H6a2 2 0 0 1-2-2z"/><path d="M18 6v14"/></svg>',
    users: '<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0M17 8a3 3 0 0 1 0 6M21 20a5 5 0 0 0-4-5"/></svg>',
    play: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M10 9l5 3-5 3z" fill="currentColor"/></svg>',
    form: '<svg viewBox="0 0 24 24"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>',
    clock: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    bell: '<svg viewBox="0 0 24 24"><path d="M6 9a6 6 0 0 1 12 0c0 7 2 8 2 8H4s2-1 2-8M10 21a2 2 0 0 0 4 0"/></svg>',
    music: '<svg viewBox="0 0 24 24"><path d="M9 18V6l10-2v12"/><circle cx="6" cy="18" r="3"/><circle cx="16" cy="16" r="3"/></svg>'
  };
  var BADGE = { doc: "DOC", pdf: "PDF", excel: "XLS", youtube: "影片", image: "圖", external: "外連",
    archive: "壓縮", ppt: "簡報", pps: "簡報", pptx: "簡報", ppsx: "簡報", mp3: "音檔", mp4: "影片",
    wma: "音檔", m4a: "音檔", txt: "文字" };
  function badge(t) {
    var cls = ["pdf","doc","excel","youtube","image","external","archive"].indexOf(t) >= 0 ? t : "external";
    return '<span class="badge ' + cls + '">' + (BADGE[t] || "連結") + "</span>";
  }
  function attrs(url) { return 'href="' + esc(url) + '" target="_blank" rel="noopener"'; }
  function linkRow(l) {
    return '<a class="link" ' + attrs(l.url) + '><span class="ttl">' + esc(l.text) + "</span>" + badge(l.type) + "</a>";
  }
  function gsize(g) {
    if (g.districts) return g.districts.reduce(function (n, d) { return n + d.churches.length; }, 0);
    return (g.churches || g.links || []).length;
  }

  var DATA = null, INDEX = null, CATS = {}, BULLETIN = null, AIGUIDE = null, PMEDIA = null, CAMPUS = null, SERVICES = null;
  var AI_GUIDE_GID = "spirit|南區AI指引";   // 開啟時顯示重製版「南區 AI 使用指引」整頁
  var PMEDIA_GID = "spirit|傳道靈糧分享";    // 開啟時顯示重製版「傳道影音專區」整頁
  var CAMPUS_GID = "activity|校園團契";      // 開啟時顯示重製版「校園團契」整頁
  var SERVICES_GID = "other|信徒服務";       // 開啟時顯示重製版「信徒服務（同靈商家通訊錄）」整頁

  // 表格型頁面（共用 renderDocTable）：原站整頁是欄位表格，逐頁解析成結構化 JSON
  var DOC_DEFS = [
    { gid: "official|南區公文", file: "data/doc-south-gongwen.json", icon: "📑", sub: "發文日期、字號、收送對象一覽" },
    { gid: "official|高屏小區公文", file: "data/doc-gaoping-gongwen.json", icon: "📋", sub: "高屏小區聚會、活動通知一覽" },
    { gid: "spirit|講義彙編", file: "data/doc-handout.json", icon: "📚", sub: "歷年進修會、講座講義與簡報（事工／生活／查經／靈修類）" },
    { gid: "activity|教牧資源分享", file: "data/doc-pastoral.json", icon: "🗂️", sub: "各股室主題資源、簡報與表格（依股別分區）" },
    { gid: "other|健康醫訊", file: "data/doc-health.json", icon: "🩺", sub: "歷期健康・醫療專欄文章" },
    { gid: "other|真光園區", file: "data/doc-zhenguang.json", icon: "🌳", sub: "園區公告、申請文件與相片集" },
    { gid: "activity|聖樂活動影音", file: "data/doc-music.json", icon: "🎵", sub: "歷屆音樂營、研習會成果影音與相片" },
    { gid: "activity|宗教教育週海報", file: "data/doc-reposters.json", icon: "🖼️", sub: "各教會歷年宗教教育週海報" },
    { gid: "spirit|線上靈糧", file: "data/doc-online.json", icon: "📡", sub: "各地教會線上直播・聚會頻道" },
    { gid: "other|好站連結", file: "data/doc-links.json", icon: "🔗", sub: "聯總、台總、教區及各地教會實用網站" },
    { gid: "spirit|讀經教材", file: "data/doc-reading.json", icon: "📖", sub: "各卷讀經合併檔、讀經小挑戰與聽道筆記" },
    { gid: "activity|人力資源", file: "data/doc-hr.json", icon: "🧑‍🏫", sub: "宗教教育週邀請講員、專題與信仰生活週課程" }
  ];
  var DOCS = {};

  Promise.all([
    fetch("data/links.json").then(function (r) { return r.json(); }),
    fetch("data/announcements.json").then(function (r) { return r.json(); }).catch(function () { return null; }),
    fetch("data/ai-guide.json").then(function (r) { return r.json(); }).catch(function () { return null; }),
    fetch("data/preacher-media.json").then(function (r) { return r.json(); }).catch(function () { return null; }),
    fetch("data/campus-fellowship.json").then(function (r) { return r.json(); }).catch(function () { return null; }),
    fetch("data/believer-services.json").then(function (r) { return r.json(); }).catch(function () { return null; })
  ].concat(DOC_DEFS.map(function (d) {
    return fetch(d.file).then(function (r) { return r.json(); }).catch(function () { return null; });
  }))).then(function (res) {
    DATA = res[0]; BULLETIN = res[1]; AIGUIDE = res[2]; PMEDIA = res[3]; CAMPUS = res[4]; SERVICES = res[5];
    DOC_DEFS.forEach(function (d, i) { if (res[6 + i]) DOCS[d.gid] = res[6 + i]; });
    (DATA.categories || []).forEach(function (c) { CATS[c.id] = c; });
    INDEX = window.TJCSearch.buildIndex(DATA);
    renderTopnav();
    renderAiBots();
    renderHero();
    renderActivityStrip();
    renderBulletin();
    renderDrawer();
    renderCategories();
    renderFooter();
  }).catch(function (e) {
    $("#catList").innerHTML = '<p style="padding:16px;color:#c0392b">資料載入失敗：' + esc(String(e)) + "</p>";
  });

  var AI_GID = "spirit|AI 靈修智能體";  // 置頂專區，不在分類內重複出現
  function groupsOf(catId) {
    return (DATA.groups || []).filter(function (g) { return g.category === catId && g.id !== AI_GID; });
  }
  function countOf(catId) { return groupsOf(catId).reduce(function (n, g) { return n + gsize(g); }, 0); }
  function bsec(id) { return BULLETIN ? (BULLETIN.sections || []).filter(function (s) { return s.id === id; })[0] : null; }

  /* ---------- Top nav (desktop) ---------- */
  function closeAllDrops() {
    document.querySelectorAll("#topnav .topnav-drop").forEach(function (d) { d.hidden = true; });
    document.querySelectorAll("#topnav .topnav-cat.open").forEach(function (b) { b.classList.remove("open"); });
  }
  document.addEventListener("click", function () { closeAllDrops(); });

  function renderTopnav() {
    $("#topnav").innerHTML = (DATA.categories || []).map(function (c) {
      var items = groupsOf(c.id).map(function (g) {
        return '<a class="td-item" data-cat="' + c.id + '" data-gid="' + esc(g.id) + '">' +
          "<span>" + esc(g.title) + '</span><span class="td-n">' + gsize(g) +
          (g.kind === "directory" ? " 間" : "") + "</span></a>";
      }).join("");
      return '<div class="topnav-item">' +
        '<button class="topnav-cat" data-cat="' + c.id + '">' + esc(c.name) +
        '<svg class="td-chev" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></button>' +
        '<div class="topnav-drop" hidden>' + items +
        '<a class="td-all" data-cat="' + c.id + '">查看全部 ' + countOf(c.id) + " 項　›</a></div></div>";
    }).join("");
    $("#topnav").querySelectorAll(".topnav-cat").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        var drop = btn.nextElementSibling, wasOpen = !drop.hidden;
        closeAllDrops();
        if (!wasOpen) { drop.hidden = false; btn.classList.add("open"); }
      });
    });
    $("#topnav").querySelectorAll(".topnav-drop").forEach(function (d) {
      d.addEventListener("click", function (e) { e.stopPropagation(); });
    });
    $("#topnav").querySelectorAll(".td-item").forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault(); closeAllDrops();
        openGroup(a.getAttribute("data-cat"), a.getAttribute("data-gid"));
      });
    });
    $("#topnav").querySelectorAll(".td-all").forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault(); closeAllDrops(); openCategoryDetail(a.getAttribute("data-cat"));
      });
    });
  }

  /* ---------- AI 靈修智能體 (top block) ---------- */
  function renderAiBots() {
    var host = $("#aiBots");
    if (!host) return;
    var g = (DATA.groups || []).filter(function (x) { return x.id === AI_GID; })[0];
    if (!g || !g.links.length) { host.hidden = true; return; }
    var rows = [
      { name: "GPT", test: function (u) { return u.indexOf("chatgpt") >= 0; } },
      { name: "Gemini", test: function (u) { return u.indexOf("gemini") >= 0; } }
    ];
    function wrapTitle(t) { return /^《/.test(t) ? t : "《" + t + "》"; }
    var body = rows.map(function (r) {
      var links = g.links.filter(function (l) { return r.test(l.url); });
      if (!links.length) return "";
      return '<div class="ab-row"><span class="ab-label"><b>' + r.name + "</b> 智能體</span>" +
        '<div class="ab-links">' + links.map(function (l) {
          return '<a ' + attrs(l.url) + ">" + esc(wrapTitle(l.text)) + "</a>";
        }).join("") + "</div></div>";
    }).join("");
    if (!body) { host.hidden = true; return; }
    var guideBtn = AIGUIDE ? '<button class="ab-guide" id="abGuide">南區 AI 使用指引 · 智能體分析　›</button>' : "";
    host.innerHTML = '<div class="aibots-inner">' +
      '<div class="ab-kicker">✦ AI 靈修智能體</div>' + body + guideBtn + "</div>";
    host.hidden = false;
    var gb = $("#abGuide");
    if (gb) gb.addEventListener("click", openAiGuide);
  }

  /* ---------- Hero (特別公告 + 尋人啟示) ---------- */
  function renderHero() {
    var host = $("#heroWrap");
    var special = bsec("special"), missing = bsec("missing");
    if (!special && !missing) { host.hidden = true; return; }
    var html = "";
    if (special) {
      var top = special.items[0] || { text: "", links: [] };
      var title = top.text;
      // strip trailing link labels (e.g. "---報名網址") from the headline
      (top.links || []).forEach(function (l) {
        title = title.replace(new RegExp("[-—、，,\\s]*" + l.label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\s*$"), "");
      });
      title = title.replace(/[-—\s]+$/, "");
      var chips = (top.links || []).map(function (l, i) {
        return '<a class="' + (i ? "ghost" : "") + '" ' + attrs(l.url) + ">" + esc(l.label) + "</a>";
      }).join("");
      // include any extra special items' links too
      special.items.slice(1).forEach(function (it) {
        (it.links || []).forEach(function (l) { chips += '<a class="ghost" ' + attrs(l.url) + ">" + esc(l.label) + "</a>"; });
      });
      html += '<div class="hero-main"><div class="hero-kick">特別公告' +
        (special.updated ? " · " + esc(special.updated) : "") + "</div>" +
        '<div class="hero-h1">' + esc(title) + "</div>" +
        '<div class="hero-chips">' + chips + "</div></div>";
    }
    if (missing) {
      html += '<div class="hero-aside"><h3>⚠ ' + esc(missing.title) + "</h3>" +
        missing.items.map(function (it) { return "<p>" + emphasize(esc(it.text)) + "</p>"; }).join("") + "</div>";
    }
    host.innerHTML = html;
  }
  function emphasize(s) {
    return s.replace(/(末\s*5\s*碼\s*)(\d{4,6})/g, '$1<span class="acct">$2</span>')
            .replace(/(0\d{2,3}-\d{3}-\d{3,4})/g, '<span class="acct">$1</span>');
  }

  /* ---------- Activity strip (教區活動) ---------- */
  function renderActivityStrip() {
    var act = bsec("activity");
    var host = $("#activityStrip");
    if (!act) { host.hidden = true; return; }
    host.innerHTML = '<div class="strip-head">📅 ' + esc(act.title) +
      (act.updated ? '<span class="u">' + esc(act.updated) + "</span>" : "") + "</div>" +
      '<div class="strip-list">' + act.items.map(function (it) {
        var m = it.text.split(/[：:]/);
        var body = m.length > 1
          ? '<span class="lab">' + esc(m[0]) + "：</span>" + esc(m.slice(1).join("："))
          : esc(it.text);
        return '<div class="strip-item"><span class="dot"></span><span>' + body + "</span></div>";
      }).join("") + "</div>";
  }

  /* ---------- Quick access ---------- */
  function renderQuick() {
    var grid = $("#quickGrid");
    grid.innerHTML = (DATA.quickAccess || []).map(function (q) {
      var inner = '<span class="qi">' + (ICONS[q.icon] || ICONS.doc) + '</span><span class="ql">' + esc(q.title) + "</span>";
      if (q.url) return '<a class="quick-btn" ' + attrs(q.url) + ">" + inner + "</a>";
      return '<button class="quick-btn" data-cat="' + esc(q.category) + '">' + inner + "</button>";
    }).join("");
    grid.querySelectorAll("[data-cat]").forEach(function (b) {
      b.addEventListener("click", function () { openCategoryDetail(b.getAttribute("data-cat")); });
    });
  }

  /* ---------- Bulletin (最新公告 / 宣導事項 / 備查公告) ---------- */
  var EMAIL_RE = /[\w.+-]+@[\w-]+\.[\w.-]+/;
  var ACCT_RE = /帳號[：:]\s*([0-9]{6,})/;
  function inferType(url) {
    var u = url.toLowerCase().split("?")[0];
    if (/youtube|youtu\.be/.test(u)) return "youtube";
    if (/^https?:/.test(u) && u.indexOf("south.tjc.org.tw") < 0) return "external";
    var ext = u.indexOf(".") >= 0 ? u.split(".").pop() : "";
    return { pdf: "pdf", doc: "doc", docx: "doc", xls: "excel", xlsx: "excel",
      jpg: "image", jpeg: "image", png: "image", gif: "image", rar: "archive", zip: "archive" }[ext] || "page";
  }
  function cleanText(t) { return t.replace(/[、，,；;。\s]+$/, "").trim(); }

  function bulletinItem(it) {
    // pure text (no link): note + optional copy button (email / account)
    if (!it.links.length) {
      var em = it.text.match(EMAIL_RE), ac = it.text.match(ACCT_RE), extra = "";
      if (em) extra = '<button class="copybtn" data-copy="' + esc(em[0]) + '">複製信箱</button>';
      else if (ac) extra = '<button class="copybtn" data-copy="' + esc(ac[1]) + '">複製帳號</button>';
      return '<div class="bitem note"><span class="btx">' + esc(it.text) + extra + "</span></div>";
    }
    // single link: the title itself is the link (no duplicate chip)
    if (it.links.length === 1) {
      var l = it.links[0];
      return '<a class="bitem bline" ' + attrs(l.url) + '><span class="ttl">' +
        esc(cleanText(it.text)) + "</span>" + badge(inferType(l.url)) + "</a>";
    }
    // multiple links: short label (if any) + chips
    var chips = it.links.map(function (lk) {
      return '<a class="chip" ' + attrs(lk.url) + ">" + esc(lk.label) + "</a>";
    }).join("");
    var ci = it.text.search(/[：:]/);
    var lbl = ci > 0 ? it.text.slice(0, ci).trim() : "";
    var lblIsLink = it.links.some(function (lk) { return lk.label.trim() === lbl; });
    var labelHtml = (lbl && !lblIsLink) ? '<span class="blabel">' + esc(lbl) + "</span>" : "";
    return '<div class="bitem">' + labelHtml + '<div class="blinks">' + chips + "</div></div>";
  }
  function renderBulletin() {
    var host = $("#bulletin");
    // show every bulletin section except those rendered elsewhere (hero + activity strip);
    // this means any NEW homepage block the office adds shows up here automatically.
    var elsewhere = ["special", "missing", "activity"];
    var secs = BULLETIN ? (BULLETIN.sections || []).filter(function (s) { return elsewhere.indexOf(s.id) < 0; }) : [];
    if (!secs.length) { host.parentElement.hidden = true; return; }
    host.innerHTML = secs.map(function (s, i) {
      var open = i === 0 ? "true" : "false";
      return '<div class="bsec" aria-expanded="' + open + '">' +
        '<button class="bsec-head"><span class="bt">' + esc(s.title) + "</span>" +
        (s.updated ? '<span class="bu">' + esc(s.updated) + "</span>" : "") +
        '<span class="bn">' + s.items.length + " 項</span>" +
        '<span class="chev"><svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></span></button>' +
        '<div class="bsec-body">' + s.items.map(bulletinItem).join("") + "</div></div>";
    }).join("");
    host.querySelectorAll(".bsec-head").forEach(function (h) {
      h.addEventListener("click", function () {
        var s = h.parentElement;
        s.setAttribute("aria-expanded", s.getAttribute("aria-expanded") === "true" ? "false" : "true");
      });
    });
    host.querySelectorAll("[data-copy]").forEach(function (b) {
      b.addEventListener("click", function (e) {
        e.preventDefault(); e.stopPropagation();
        var v = b.getAttribute("data-copy");
        if (navigator.clipboard) navigator.clipboard.writeText(v);
        var old = b.textContent; b.textContent = "已複製 ✓";
        setTimeout(function () { b.textContent = old; }, 1500);
      });
    });
  }

  /* ---------- Footer ---------- */
  function renderFooter() {
    var sm = $("#footSitemap");
    if (sm) {
      sm.innerHTML = (DATA.categories || []).map(function (c) {
        return '<li><a href="#" data-cat="' + c.id + '">' + esc(c.name) + "</a></li>";
      }).join("");
      sm.querySelectorAll("[data-cat]").forEach(function (a) {
        a.addEventListener("click", function (e) { e.preventDefault(); openCategoryDetail(a.getAttribute("data-cat")); });
      });
    }
    var ch = $("#footChurches");
    if (ch) ch.addEventListener("click", function (e) {
      e.preventDefault(); openCategoryDetail("other", "other|教會地址");
    });
    document.querySelectorAll(".footcopy").forEach(function (b) {
      b.addEventListener("click", function () {
        var v = b.getAttribute("data-copy");
        if (navigator.clipboard) navigator.clipboard.writeText(v);
        var old = b.textContent; b.textContent = "已複製 ✓";
        setTimeout(function () { b.textContent = old; }, 1500);
      });
    });
  }

  /* ---------- Drawer (two-level accordion) ---------- */
  function renderDrawer() {
    $("#drawerList").innerHTML = (DATA.categories || []).map(function (c) {
      var sub = groupsOf(c.id).map(function (g) {
        return '<li><a href="#" data-cat="' + c.id + '" data-gid="' + esc(g.id) + '">' +
          "<span>" + esc(g.title) + '</span><span class="cc">' + gsize(g) +
          (g.kind === "directory" ? " 間" : "") + "</span></a></li>";
      }).join("");
      return '<li class="draw-cat">' +
        '<button class="draw-head" data-cat="' + c.id + '">' +
        '<span class="ci">' + (ICONS[c.icon] || ICONS.doc) + "</span>" +
        '<span class="cn">' + esc(c.name) + "</span>" +
        '<span class="cc">' + countOf(c.id) + "</span>" +
        '<svg class="dchev" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></button>' +
        '<ul class="draw-sub" hidden>' + sub + "</ul></li>";
    }).join("");
    $("#drawerList").querySelectorAll(".draw-head").forEach(function (h) {
      h.addEventListener("click", function () {
        var sub = h.nextElementSibling, willOpen = sub.hidden;
        sub.hidden = !willOpen;
        h.classList.toggle("open", willOpen);
      });
    });
    $("#drawerList").querySelectorAll(".draw-sub a").forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault(); closeDrawer();
        openGroup(a.getAttribute("data-cat"), a.getAttribute("data-gid"));
      });
    });
  }

  /* ---------- Category preview grid ---------- */
  function renderCategories() {
    $("#catList").innerHTML = (DATA.categories || []).map(function (c) {
      var groups = groupsOf(c.id);
      var top = groups.slice(0, 3).map(function (g) {
        return "<li>" + esc(g.title) + '<span class="gc">' + gsize(g) + (g.kind === "directory" ? " 間" : "") + "</span></li>";
      }).join("");
      return '<button class="cat-card" data-cat="' + c.id + '">' +
        '<div class="cc-head"><span class="cc-ic">' + (ICONS[c.icon] || ICONS.doc) + "</span>" +
        '<span class="cc-nm">' + esc(c.name) + "</span>" +
        '<span class="cc-badge">' + countOf(c.id) + " 項</span></div>" +
        "<ul>" + top + "</ul>" +
        '<span class="cc-more">查看全部 ' + groups.length + " 類　›</span></button>";
    }).join("");
    $("#catList").querySelectorAll("[data-cat]").forEach(function (b) {
      b.addEventListener("click", function () { openCategoryDetail(b.getAttribute("data-cat")); });
    });
  }

  /* ---------- Detail overlay with simple history stack ---------- */
  var detailStack = [];
  function showDetail(title, html, wire) {
    $("#detailTitle").textContent = title;
    $("#detailBody").innerHTML = '<div class="detail-inner">' + html + "</div>";
    $("#detailOverlay").hidden = false;
    $("#detailBody").scrollTop = 0;
    if (wire) wire();
  }
  function pushDetail(fn) { detailStack.push(fn); fn(); }
  function popDetail() {
    detailStack.pop();
    if (detailStack.length) detailStack[detailStack.length - 1]();
    else $("#detailOverlay").hidden = true;
  }
  $("#detailBack").addEventListener("click", popDetail);

  function openGroup(catId, gid) {
    if (gid === AI_GUIDE_GID && AIGUIDE) { openAiGuide(); return; }
    if (gid === PMEDIA_GID && PMEDIA) { openPreacherMedia(); return; }
    if (gid === CAMPUS_GID && CAMPUS) { openCampus(); return; }
    if (gid === SERVICES_GID && SERVICES) { openServices(); return; }
    if (DOCS[gid]) { openDocPage(gid); return; }
    openCategoryDetail(catId, gid);
  }
  function openCategoryDetail(catId, targetGid) {
    detailStack = [];
    pushDetail(function () { renderCategoryDetail(catId, targetGid); });
  }
  function openAiGuide() { detailStack = []; pushDetail(renderAiGuideDetail); }
  function openPreacherMedia() { detailStack = []; pushDetail(renderPreacherMediaDetail); }
  function openCampus() { detailStack = []; pushDetail(renderCampusDetail); }
  function openServices() { detailStack = []; pushDetail(renderServicesDetail); }
  function openDocPage(gid) { detailStack = []; pushDetail(function () { renderDocPageDetail(gid); }); }
  function docDef(gid) { return DOC_DEFS.filter(function (x) { return x.gid === gid; })[0]; }

  /* ---------- 表格型頁面（共用：南區公文、高屏公文、講義彙編…） ---------- */
  function dtCell(c) {
    if (c == null) return "";
    if (typeof c === "string") c = { t: c };
    var t = esc(c.t || "");
    if (c.parts) {
      var lead = c.t ? '<span class="dt-lead">' + t + "</span>" : "";
      return lead + '<span class="dt-chips">' + c.parts.map(function (p) {
        return '<a class="chip" ' + attrs(p.url) + ">" + esc(p.label) + (p.kind ? badge(p.kind) : "") + "</a>";
      }).join("") + "</span>";
    }
    if (c.u) return '<a class="dt-link" ' + attrs(c.u) + ">" + t + (c.k ? badge(c.k) : "") + "</a>";
    return t || '<span class="dt-empty">／</span>';
  }
  function renderDocTable(d) {
    var secs = d.sections.map(function (s) {
      var pri = (s.primary != null) ? s.primary : 0;
      var thead = "<tr>" + s.columns.map(function (c) { return "<th>" + esc(c) + "</th>"; }).join("") + "</tr>";
      var body = s.rows.map(function (r) {
        return "<tr>" + r.map(function (c, i) {
          return '<td data-label="' + esc(s.columns[i] || "") + '"' + (i === pri ? ' class="dt-pri"' : "") + ">" + dtCell(c) + "</td>";
        }).join("") + "</tr>";
      }).join("");
      return '<section class="dt-sec">' +
        (s.name ? '<h2 class="cf-h2">' + esc(s.name) + '<span class="sv-n">' + s.rows.length + " 則</span></h2>" : "") +
        '<div class="dt-wrap"><table class="dt-table"><thead>' + thead + "</thead><tbody>" + body + "</tbody></table></div></section>";
    }).join("");
    var intro = (d.intro || []).map(function (p) { return '<p class="cf-sub" style="display:block">' + esc(p) + "</p>"; }).join("");
    var channel = d.channel ? '<div class="cf-cta"><a class="pm-channel" ' + attrs(d.channel.url) +
      '><svg viewBox="0 0 24 24"><rect x="3" y="6" width="18" height="12" rx="3"/><path d="M10 9l5 3-5 3z" fill="currentColor" stroke="none"/></svg>' +
      esc(d.channel.text) + "　›</a></div>" : "";
    return '<div class="cf dt">' +
      '<div class="cf-hero"><div class="cf-kick">✦ ' + esc(d.kicker || "南區辦事處") + "</div>" +
      '<h1 class="cf-h1">' + esc(d.title) + "</h1>" +
      (d.subtitle ? '<p class="cf-sub">' + esc(d.subtitle) +
        (d.updated ? '<span class="cf-upd">' + esc(d.updated) + " 更新</span>" : "") + "</p>" : "") +
      intro + channel + "</div>" + secs +
      (d.note ? '<p class="cf-foot-note">' + esc(d.note) + "</p>" : "") + "</div>";
  }
  function renderDocPageDetail(gid) {
    var d = DOCS[gid]; if (!d) return;
    showDetail(d.title, renderDocTable(d));
  }

  /* ---------- 信徒服務（重製 10/index.htm） ---------- */
  function telLinks(s) {
    if (!s) return "";
    return s.split(/\s+/).filter(Boolean).map(function (n) {
      var digits = n.replace(/[^0-9+]/g, "");
      return '<a class="sv-tel" href="tel:' + digits + '">' + esc(n) + "</a>";
    }).join("");
  }
  function serviceCard(e) {
    var rows = "";
    if (e.phone) rows += '<div class="sv-line"><span class="sv-ic">☎</span><span class="sv-tels">' + telLinks(e.phone) + "</span></div>";
    if (e.mobile) rows += '<div class="sv-line"><span class="sv-ic">📱</span><span class="sv-tels">' + telLinks(e.mobile) + "</span></div>";
    if (e.fax) rows += '<div class="sv-line sv-fax"><span class="sv-ic">📠</span><span>' + esc(e.fax) + "</span></div>";
    var desc = esc(e.desc);
    if (e.link) desc += ' <a class="sv-web" ' + attrs(e.link.url) + ">" + esc(e.link.label) + " ↗</a>";
    return '<div class="sv-card">' +
      '<div class="sv-card-h"><span class="sv-type">' + esc(e.type) + "</span>" +
      '<span class="sv-church">' + esc(e.church) + "</span></div>" +
      '<div class="sv-contact">聯絡人　' + esc(e.contact) + "</div>" +
      '<p class="sv-desc">' + desc + "</p>" +
      '<div class="sv-lines">' + rows + "</div></div>";
  }
  function renderServicesDetail() {
    var d = SERVICES;
    var nav = d.categories.map(function (c) {
      return '<a class="pm-jump" data-jump="sv-cat-' + esc(c.name) + '">' + esc(c.name.charAt(0)) + "</a>";
    }).join("");
    var secs = d.categories.map(function (c) {
      return '<section class="sv-sec" id="sv-cat-' + esc(c.name) + '">' +
        '<h2 class="cf-h2">' + esc(c.name) + '<span class="sv-n">' + c.entries.length + " 家</span></h2>" +
        '<div class="sv-grid">' + c.entries.map(serviceCard).join("") + "</div></section>";
    }).join("");
    var form = d.form ? '<a class="cf-fg" ' + attrs(d.form.url) +
      '><svg viewBox="0 0 24 24"><path d="M12 3v12M7 10l5 5 5-5M5 21h14"/></svg>下載登錄表　›</a>' : "";
    var html = '<div class="cf">' +
      '<div class="cf-hero"><div class="cf-kick">✦ 南區信徒服務</div>' +
      '<h1 class="cf-h1">' + esc(d.title) + "</h1>" +
      '<p class="cf-sub">' + esc(d.subtitle) + "</p>" +
      (d.intro ? '<p class="sv-intro">' + esc(d.intro) + "</p>" : "") +
      '<div class="cf-cta">' + form + "</div>" +
      '<div class="pm-nav">' + nav + "</div></div>" +
      secs + "</div>";
    showDetail("信徒服務", html, function () {
      $("#detailBody").querySelectorAll("[data-jump]").forEach(function (a) {
        a.addEventListener("click", function () {
          var el = document.getElementById(a.getAttribute("data-jump"));
          if (el) $("#detailBody").scrollTop = el.offsetTop - 12;
        });
      });
    });
  }

  /* ---------- 校園團契（重製 04/index-1.htm） ---------- */
  function linkifyUrls(s) {
    return esc(s).replace(/(https?:\/\/[^\s，、）)]+)/g, function (u) {
      return '<a ' + attrs(u) + ">" + u + "</a>";
    });
  }
  function campusRegion(r) {
    var rows = r.fellowships.map(function (f) {
      return '<div class="cf-row">' +
        '<div class="cf-name">' + esc(f.name) + "</div>" +
        '<div class="cf-schools">' + esc(f.schools) + "</div>" +
        '<div class="cf-church"><span class="cf-church-tag">' + esc(f.church) + "</span></div></div>";
    }).join("");
    return '<div class="cf-region"><div class="cf-region-h">' + esc(r.name) +
      '<span class="cf-region-n">' + r.fellowships.length + " 團契</span></div>" +
      '<div class="cf-rows"><div class="cf-row cf-head">' +
      '<div class="cf-name">' + esc(CAMPUS.columns.name) + "</div>" +
      '<div class="cf-schools">' + esc(CAMPUS.columns.schools) + "</div>" +
      '<div class="cf-church">' + esc(CAMPUS.columns.church) + "</div></div>" +
      rows + "</div></div>";
  }
  function renderCampusDetail() {
    var d = CAMPUS;
    var notes = (d.notes || []).map(function (n, i) {
      var num = "一二三四五六七八九十".charAt(i) || (i + 1);
      return '<li><span class="cf-note-n">' + num + "</span><span>" + linkifyUrls(n) + "</span></li>";
    }).join("");
    var html = '<div class="cf">' +
      '<div class="cf-hero"><div class="cf-kick">✦ 南區大專事工</div>' +
      '<h1 class="cf-h1">' + esc(d.title) + "</h1>" +
      '<p class="cf-sub">' + esc(d.subtitle) +
      (d.updated ? '<span class="cf-upd">' + esc(d.updated) + " 更新</span>" : "") + "</p>" +
      '<div class="cf-cta">' +
      '<a class="cf-fg" ' + attrs(d.fg.url) + '><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>' +
      esc(d.fg.label) + " 查詢系統　›</a>" +
      (d.lodging ? '<a class="cf-lodging" ' + attrs(d.lodging.url) + ">🏠 " + esc(d.lodging.label) + "</a>" : "") +
      "</div></div>" +
      '<section class="cf-sec">' + d.regions.map(campusRegion).join("") + "</section>" +
      (notes ? '<section class="cf-sec"><h2 class="cf-h2">大專事工說明</h2><ul class="cf-notes">' + notes + "</ul></section>" : "") +
      "</div>";
    showDetail("校園團契", html);
  }

  /* ---------- 傳道影音專區（重製 13/index.htm） ---------- */
  function pmSermonEntry(e) {
    var langs = e.langs.map(function (l) {
      var cls = l.lang === "台語" ? "tai" : "guo";
      return '<a class="pm-lang ' + cls + '" ' + attrs(l.url) + ">" +
        '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M10 9l5 3-5 3z" fill="currentColor" stroke="none"/></svg>' +
        (l.lang || "影片") + "</a>";
    }).join("");
    return '<div class="pm-card">' +
      '<div class="pm-card-top">' + (e.date ? '<span class="pm-date">' + esc(e.date) + "</span>" : "") +
      (e.no ? '<span class="pm-no">' + esc(e.no) + "</span>" : "") + "</div>" +
      '<div class="pm-ref">' + esc(e.ref) + "</div>" +
      '<div class="pm-langs">' + langs + "</div></div>";
  }
  function pmDevotionEntry(e) {
    return '<a class="pm-dev" ' + attrs(e.url) + ">" +
      (e.date ? '<span class="pm-dev-date">' + esc(e.date) + "</span>" : "") +
      '<span class="pm-dev-title">' + esc(e.title) + "</span>" + badge(e.kind === "youtube" ? "youtube" : e.kind) + "</a>";
  }
  function pmPreacher(p) {
    var series = p.series.map(function (s) {
      var parts = s.parts.map(function (pt) {
        return '<a class="chip" ' + attrs(pt.url) + ">" + esc(pt.label) + "</a>";
      }).join("");
      return '<div class="pm-series"><div class="pm-series-t">' + esc(s.title) + "</div>" +
        '<div class="pm-parts">' + parts + "</div></div>";
    }).join("");
    var lang = p.lang ? '<span class="pm-plang">' + esc(p.lang) + "</span>" : "";
    return '<div class="pm-preacher"><div class="pm-pname">' + esc(p.name) + lang + "</div>" + series + "</div>";
  }
  function pmSection(s) {
    var inner;
    if (s.type === "lecture") {
      inner = '<div class="pm-preachers">' + s.preachers.map(pmPreacher).join("") + "</div>";
    } else if (s.type === "devotion") {
      inner = '<div class="pm-dev-list">' + s.entries.map(pmDevotionEntry).join("") + "</div>";
    } else {
      inner = '<div class="pm-grid">' + s.entries.map(pmSermonEntry).join("") + "</div>";
    }
    var count = s.type === "lecture" ? s.preachers.length + " 位傳道" : s.entries.length + " 則";
    var sub = s.note ? '<span class="pm-sec-sub">（' + esc(s.note) + "）</span>" : "";
    return '<section class="pm-sec" id="pm-sec-' + esc(s.no) + '">' +
      '<h2 class="pm-sec-h"><span class="n">' + esc(s.no) + "</span>" +
      '<span class="pm-sec-t">' + esc(s.title) + sub + "</span>" +
      '<span class="pm-sec-n">' + count + "</span></h2>" + inner + "</section>";
  }
  function renderPreacherMediaDetail() {
    var d = PMEDIA;
    var nav = d.sections.map(function (s) {
      return '<a class="pm-jump" data-jump="pm-sec-' + esc(s.no) + '">' + esc(s.no) + "</a>";
    }).join("");
    var channel = d.channel
      ? '<a class="pm-channel" ' + attrs(d.channel.url) + '>' +
        '<svg viewBox="0 0 24 24"><rect x="3" y="6" width="18" height="12" rx="3"/><path d="M10 9l5 3-5 3z" fill="currentColor" stroke="none"/></svg>' +
        esc(d.channel.text) + "　›</a>"
      : "";
    var html = '<div class="pm">' +
      '<div class="pm-hero"><div class="pm-kick">✦ 南區傳道影音</div>' +
      '<h1 class="pm-h1">傳道者靈糧分享・靈修小語・聖經講座</h1>' +
      '<p class="pm-lead">歷年傳道講道、每週靈修小語與聖經講座影音彙整，影片開啟後導向 YouTube／原站檔案。</p>' +
      channel + '<div class="pm-nav">' + nav + "</div></div>" +
      d.sections.map(pmSection).join("") + "</div>";
    showDetail("傳道影音專區", html, function () {
      $("#detailBody").querySelectorAll("[data-jump]").forEach(function (a) {
        a.addEventListener("click", function () {
          var el = document.getElementById(a.getAttribute("data-jump"));
          if (el) $("#detailBody").scrollTop = el.offsetTop - 12;
        });
      });
    });
  }

  /* ---------- 南區 AI 使用指引（重製 index.htm + index4.htm） ---------- */
  function agentCard(a) {
    function lk(url, label, cls) {
      return '<a class="aig-bot ' + cls + '" ' + attrs(url) + "><b>" + label + "</b></a>";
    }
    var note = a.note ? '<a class="aig-note" ' + attrs(a.note) + ">使用備註 ›</a>" : "";
    return '<div class="aig-agent">' +
      '<div class="aig-agent-h"><span class="aig-agent-nm">《' + esc(a.name) + "》</span>" + note + "</div>" +
      '<div class="aig-agent-d">' + esc(a.desc) + "</div>" +
      '<div class="aig-bots">' + lk(a.gpt, "GPT", "gpt") + lk(a.gemini, "Gemini", "gemini") + "</div></div>";
  }
  function renderAiGuideDetail() {
    var g = AIGUIDE;
    var builders = g.builders.map(function (b) {
      return '<span class="aig-builder"><b>' + esc(b.platform) + "</b> · " + esc(b.maintainer) + "</span>";
    }).join("");
    var agents = g.agents.map(agentCard).join("");

    var teamGroups = g.team.groups.map(function (gr) {
      var reps = gr.reports.map(function (r) {
        return '<a class="aig-report" ' + attrs(r.url) + '><span class="ttl">' + esc(r.text) + "</span>" + badge("pdf") + "</a>";
      }).join("");
      var mem = gr.members.map(function (m) { return "<li>" + esc(m) + "</li>"; }).join("");
      return '<div class="aig-team-card"><div class="aig-team-nm">' + esc(gr.name) + "</div>" +
        '<div class="aig-reports">' + reps + "</div>" +
        '<ul class="aig-members">' + mem + "</ul></div>";
    }).join("");

    var html =
      '<div class="aig">' +
      '<div class="aig-hero"><div class="aig-kick">✦ 南區宣牧聖工 AI 策略小組</div>' +
      '<h1 class="aig-title">' + esc(g.title) + "</h1>" +
      '<div class="aig-copy">' + esc(g.copyright) + "</div>" +
      '<div class="aig-builders">' + builders + "</div></div>" +

      '<section class="aig-sec"><h2 class="aig-h2"><span class="n">壹</span>信仰型智能體</h2>' +
      '<p class="aig-lead">點選下方智能體即可開啟對話；各平台同名智能體內容一致，請擇一使用。</p>' +
      '<div class="aig-agents">' + agents + "</div></section>" +

      '<section class="aig-sec"><h2 class="aig-h2"><span class="n">貳</span>' + esc(g.team.title) + "</h2>" +
      '<div class="aig-teams">' + teamGroups + "</div>" +
      '<p class="aig-secretary">' + esc(g.team.secretary) + "</p></section>" +

      '<button class="aig-analysis-btn" data-aig-analysis="1">' +
      '<span class="aig-ab-tx"><span class="aig-ab-t">真耶穌教會智能體分析</span>' +
      '<span class="aig-ab-s">三款信仰型 AI 的定位、特色與互補比較</span></span>' +
      '<svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></button>' +
      "</div>";

    showDetail("南區 AI 使用指引", html, function () {
      var b = $("#detailBody").querySelector("[data-aig-analysis]");
      if (b) b.addEventListener("click", function () { pushDetail(renderAiAnalysisDetail); });
    });
  }

  function renderAiAnalysisDetail() {
    var a = AIGUIDE.analysis, nm = a.names;
    function tableHead(first, cols) {
      return "<tr><th>" + esc(first) + "</th>" + cols.map(function (c) { return "<th>" + esc(c) + "</th>"; }).join("") + "</tr>";
    }
    // 定位比較
    var posRows = a.positioning.rows.map(function (r) {
      return "<tr><th>" + esc(r.label) + "</th>" + r.values.map(function (v) { return "<td>" + esc(v) + "</td>"; }).join("") + "</tr>";
    }).join("");
    var posTable = '<div class="aig-tablewrap"><table class="aig-table"><thead>' +
      tableHead("面向", nm) + "</thead><tbody>" + posRows + "</tbody></table></div>";

    // profile cards
    var profiles = a.profiles.cards.map(function (c) {
      var secs = c.sections.map(function (s) {
        var items = s.items.map(function (it) { return "<li>" + esc(it) + "</li>"; }).join("");
        return '<div class="aig-pf-sec"><div class="aig-pf-lab">' + esc(s.label) + "</div><ol>" + items + "</ol></div>";
      }).join("");
      return '<div class="aig-profile"><div class="aig-pf-nm">《' + esc(c.name) + "》</div>" +
        '<p class="aig-pf-lead">' + esc(c.lead) + "</p>" + secs + "</div>";
    }).join("");

    // overall layers + combo
    var ov = a.overall;
    var layers = ov.layers.items.map(function (t, i) {
      return '<div class="aig-layer"><span class="aig-layer-n">' + (i + 1) + "</span><span>" + esc(t) + "</span></div>";
    }).join("");
    var combo = ov.combo.items.map(function (t) { return "<li>" + esc(t) + "</li>"; }).join("");

    // summary table
    var sumRows = ov.summary.rows.map(function (r) {
      return "<tr><th>" + esc(r[0]) + "</th>" + r.slice(1).map(function (v) { return "<td>" + esc(v) + "</td>"; }).join("") + "</tr>";
    }).join("");
    var sumTable = '<div class="aig-tablewrap"><table class="aig-table"><thead>' +
      tableHead(ov.summary.head[0], ov.summary.head.slice(1)) + "</thead><tbody>" + sumRows + "</tbody></table></div>";

    var html =
      '<div class="aig">' +
      '<div class="aig-hero alt"><div class="aig-kick">✦ 智能體分析</div>' +
      '<h1 class="aig-title">' + esc(a.title) + "</h1>" +
      a.intro.map(function (p) { return '<p class="aig-intro">' + esc(p) + "</p>"; }).join("") + "</div>" +

      '<section class="aig-sec"><h2 class="aig-h2"><span class="n">一</span>定位比較</h2>' + posTable + "</section>" +

      '<section class="aig-sec"><h2 class="aig-h2"><span class="n">二</span>各智能體的特色、優點、適合用途</h2>' +
      '<div class="aig-profiles">' + profiles + "</div></section>" +

      '<section class="aig-sec"><h2 class="aig-h2"><span class="n">三</span>整體比較</h2>' +
      '<div class="aig-card"><div class="aig-card-t">' + esc(ov.layers.title) + "</div>" +
      '<div class="aig-layers">' + layers + "</div></div>" +
      '<div class="aig-card"><div class="aig-card-t">' + esc(ov.combo.title) + "</div>" +
      '<ol class="aig-combo">' + combo + "</ol></div>" +
      '<div class="aig-card"><div class="aig-card-t">' + esc(ov.summary.title) + "</div>" + sumTable + "</div>" +
      '<p class="aig-disclaimer"><b>備註：</b>' + esc(ov.note) + "</p></section>" +
      "</div>";

    showDetail("智能體分析", html);
  }
  function renderCategoryDetail(catId, targetGid) {
    var c = CATS[catId]; if (!c) return;
    var groups = groupsOf(catId);
    var html = groups.map(function (g) {
      if (g.id === AI_GUIDE_GID && AIGUIDE) {
        return '<button class="dgroup aig-promo" data-aig-open="1">' +
          '<span class="aig-promo-ic">✦</span>' +
          '<span class="aig-promo-tx"><b>南區 AI 使用指引</b>' +
          '<span>信仰型智能體、策略小組報告與智能體分析</span></span>' +
          '<svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></button>';
      }
      if (g.id === PMEDIA_GID && PMEDIA) {
        return '<button class="dgroup aig-promo pm-promo" data-pm-open="1">' +
          '<span class="aig-promo-ic">▶</span>' +
          '<span class="aig-promo-tx"><b>傳道影音專區</b>' +
          '<span>靈糧分享、靈修小語、傳道者聖經講座</span></span>' +
          '<svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></button>';
      }
      if (g.id === CAMPUS_GID && CAMPUS) {
        return '<button class="dgroup aig-promo cf-promo" data-cf-open="1">' +
          '<span class="aig-promo-ic">🎓</span>' +
          '<span class="aig-promo-tx"><b>校園團契</b>' +
          '<span>南區大專團契所屬院校、牧養教會與查詢系統</span></span>' +
          '<svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></button>';
      }
      if (g.id === SERVICES_GID && SERVICES) {
        return '<button class="dgroup aig-promo sv-promo" data-sv-open="1">' +
          '<span class="aig-promo-ic">🏷️</span>' +
          '<span class="aig-promo-tx"><b>信徒服務</b>' +
          '<span>南區同靈商家・服務通訊錄（產品／技術／服務類）</span></span>' +
          '<svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></button>';
      }
      if (DOCS[g.id]) {
        var dd = DOCS[g.id], def = docDef(g.id);
        return '<button class="dgroup aig-promo dt-promo" data-doc-open="' + esc(g.id) + '">' +
          '<span class="aig-promo-ic">' + (def && def.icon ? def.icon : "📑") + "</span>" +
          '<span class="aig-promo-tx"><b>' + esc(dd.title) + "</b>" +
          "<span>" + esc((def && def.sub) || dd.subtitle || "") + "</span></span>" +
          '<svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></button>';
      }
      var head = '<div class="dgroup-h"><span class="gt">' + esc(g.title) + '</span><span class="gc">' +
        gsize(g) + (g.kind === "directory" ? " 間" : " 項") + "</span></div>";
      var inner;
      if (g.kind === "schedule") {
        var shead = '<div class="dgroup-h"><span class="gt">' + esc(g.title) +
          '</span><span class="gc">' + g.months.length + " 個月</span></div>";
        var sbody = '<div class="sched">' + g.months.map(function (m) {
          var has = m.files && m.files.length;
          var files = has ? m.files.map(function (f) {
            return '<a class="chip" ' + attrs(f.url) + ">" + esc(f.kind) + "</a>";
          }).join("") : '<span class="sched-none">尚未公告</span>';
          return '<div class="sched-m' + (has ? "" : " empty") + '"><div class="sched-mon">' +
            esc(m.label) + '</div><div class="sched-files">' + files + "</div></div>";
        }).join("") + "</div>";
        inner = shead + (g.verse ? '<blockquote class="dgroup-verse">' + esc(g.verse) + "</blockquote>" : "") + sbody;
      } else if (g.kind === "directory") {
        var btns = (g.districts || []).map(function (d, i) {
          return '<button class="viewall dir-btn" data-dir="' + esc(g.id) + '" data-di="' + i +
            '">' + esc(d.name) + '<span class="db-n">' + d.churches.length + " 間</span>　›</button>";
        }).join("");
        inner = head + '<div class="dir-btns">' + btns + "</div>";
      } else if (g.paginated && g.links.length > 12) {
        inner = head + '<ul class="links">' + g.links.slice(0, 5).map(linkRow).join("") + "</ul>" +
          '<button class="viewall" data-group="' + esc(g.id) + '">查看全部 ' + g.links.length + " 項　›</button>";
      } else {
        inner = head + '<ul class="links">' + g.links.map(linkRow).join("") + "</ul>";
      }
      if (g.note) inner += '<p class="dgroup-note">' + esc(g.note) + "</p>";
      return '<div class="dgroup" data-gid="' + esc(g.id) + '">' + inner + "</div>";
    }).join("");
    showDetail(c.name + "（" + countOf(catId) + "）", html, function () {
      var aigBtn = $("#detailBody").querySelector("[data-aig-open]");
      if (aigBtn) aigBtn.addEventListener("click", function () { pushDetail(renderAiGuideDetail); });
      var pmBtn = $("#detailBody").querySelector("[data-pm-open]");
      if (pmBtn) pmBtn.addEventListener("click", function () { pushDetail(renderPreacherMediaDetail); });
      var cfBtn = $("#detailBody").querySelector("[data-cf-open]");
      if (cfBtn) cfBtn.addEventListener("click", function () { pushDetail(renderCampusDetail); });
      var svBtn = $("#detailBody").querySelector("[data-sv-open]");
      if (svBtn) svBtn.addEventListener("click", function () { pushDetail(renderServicesDetail); });
      $("#detailBody").querySelectorAll("[data-doc-open]").forEach(function (docBtn) {
        docBtn.addEventListener("click", function () {
          var gid = docBtn.getAttribute("data-doc-open");
          pushDetail(function () { renderDocPageDetail(gid); });
        });
      });
      $("#detailBody").querySelectorAll("[data-group]").forEach(function (b) {
        b.addEventListener("click", function () { pushDetail(function () { renderGroupDetail(b.getAttribute("data-group")); }); });
      });
      $("#detailBody").querySelectorAll("[data-dir]").forEach(function (b) {
        b.addEventListener("click", function () {
          var id = b.getAttribute("data-dir"), di = +b.getAttribute("data-di");
          pushDetail(function () { renderChurchDetail(id, di); });
        });
      });
      if (targetGid) {
        var el = Array.prototype.filter.call($("#detailBody").querySelectorAll(".dgroup"), function (d) {
          return d.getAttribute("data-gid") === targetGid;
        })[0];
        if (el) { el.scrollIntoView({ block: "start" }); el.classList.add("flash"); }
      }
    });
  }
  function renderGroupDetail(groupId) {
    var g = (DATA.groups || []).filter(function (x) { return x.id === groupId; })[0]; if (!g) return;
    showDetail(g.title + "（" + g.links.length + "）",
      '<div class="dgroup"><ul class="links">' + g.links.map(linkRow).join("") + "</ul></div>");
  }
  function renderChurchDetail(groupId, di) {
    var g = (DATA.groups || []).filter(function (x) { return x.id === groupId; })[0];
    if (!g) return;
    var dist = g.districts ? g.districts[di || 0] : { name: g.title, churches: g.churches || [] };
    if (!dist) return;
    var cards = dist.churches.map(function (c) {
      var chips = (c.links || []).map(function (l) { return '<a class="chip" ' + attrs(l.url) + ">" + esc(l.label) + "</a>"; }).join("");
      var meta = [];
      if (c.address) meta.push("📍 " + esc(c.address));
      if (c.phone) meta.push('☎ <a href="tel:' + esc(c.phone.replace(/[^0-9+]/g, "")) + '">' + esc(c.phone) + "</a>");
      return '<div class="ch-card"><div class="ch-name">' + esc(c.name) + "</div>" +
        (meta.length ? '<div class="ch-meta">' + meta.join("　") + "</div>" : "") +
        '<div class="blinks">' + chips + "</div></div>";
    }).join("");
    showDetail(dist.name + "教會通訊錄（" + dist.churches.length + " 間）", '<div class="ch-grid">' + cards + "</div>");
  }

  /* ---------- Drawer open/close ---------- */
  function openDrawer() { $("#drawer").hidden = false; $("#scrim").hidden = false; $("#menuBtn").setAttribute("aria-expanded", "true"); }
  function closeDrawer() { $("#drawer").hidden = true; $("#scrim").hidden = true; $("#menuBtn").setAttribute("aria-expanded", "false"); }
  $("#menuBtn").addEventListener("click", openDrawer);
  $("#drawerClose").addEventListener("click", closeDrawer);
  $("#scrim").addEventListener("click", closeDrawer);

  /* ---------- Search ---------- */
  var searchT;
  $("#searchBtn").addEventListener("click", function () {
    $("#searchOverlay").hidden = false; $("#searchInput").value = ""; $("#searchResults").innerHTML = "";
    setTimeout(function () { $("#searchInput").focus(); }, 50);
  });
  $("#searchClose").addEventListener("click", function () { $("#searchOverlay").hidden = true; });
  $("#searchInput").addEventListener("input", function () { clearTimeout(searchT); searchT = setTimeout(runSearch, 120); });
  function runSearch() {
    var q = $("#searchInput").value.trim(), box = $("#searchResults");
    if (!q) { box.innerHTML = ""; return; }
    var res = window.TJCSearch.search(INDEX, q, 100);
    if (!res.length) { box.innerHTML = '<p class="search-empty">找不到「' + esc(q) + "」相關連結</p>"; return; }
    box.innerHTML = res.map(function (l) {
      return '<a class="link" ' + attrs(l.url) + '><span class="ttl">' + window.TJCSearch.highlight(l.text, q) +
        '</span><span class="res-cat">' + esc(l.catName) + "</span>" + badge(l.type) + "</a>";
    }).join("");
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { $("#searchOverlay").hidden = true; $("#detailOverlay").hidden = true; closeDrawer(); }
  });
})();
