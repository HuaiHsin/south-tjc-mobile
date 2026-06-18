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

  var DATA = null, INDEX = null, CATS = {}, BULLETIN = null;

  Promise.all([
    fetch("data/links.json").then(function (r) { return r.json(); }),
    fetch("data/announcements.json").then(function (r) { return r.json(); }).catch(function () { return null; })
  ]).then(function (res) {
    DATA = res[0]; BULLETIN = res[1];
    (DATA.categories || []).forEach(function (c) { CATS[c.id] = c; });
    INDEX = window.TJCSearch.buildIndex(DATA);
    renderTopnav();
    renderHero();
    renderActivityStrip();
    renderBulletin();
    renderDrawer();
    renderCategories();
    renderFooter();
  }).catch(function (e) {
    $("#catList").innerHTML = '<p style="padding:16px;color:#c0392b">資料載入失敗：' + esc(String(e)) + "</p>";
  });

  function groupsOf(catId) { return (DATA.groups || []).filter(function (g) { return g.category === catId; }); }
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
        openCategoryDetail(a.getAttribute("data-cat"), a.getAttribute("data-gid"));
      });
    });
    $("#topnav").querySelectorAll(".td-all").forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault(); closeAllDrops(); openCategoryDetail(a.getAttribute("data-cat"));
      });
    });
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
        openCategoryDetail(a.getAttribute("data-cat"), a.getAttribute("data-gid"));
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

  function openCategoryDetail(catId, targetGid) {
    detailStack = [];
    pushDetail(function () { renderCategoryDetail(catId, targetGid); });
  }
  function renderCategoryDetail(catId, targetGid) {
    var c = CATS[catId]; if (!c) return;
    var groups = groupsOf(catId);
    var html = groups.map(function (g) {
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
        inner = shead + sbody;
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
      return '<div class="dgroup" data-gid="' + esc(g.id) + '">' + inner + "</div>";
    }).join("");
    showDetail(c.name + "（" + countOf(catId) + "）", html, function () {
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
