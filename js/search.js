/* Client-side search over the flattened link index (spec §3, §4). */
(function (global) {
  "use strict";

  function normalize(s) {
    return (s || "").toLowerCase().replace(/\s+/g, "");
  }

  // Build a flat index: [{text, url, type, groupTitle, catName}]
  function buildIndex(data) {
    var catName = {};
    (data.categories || []).forEach(function (c) { catName[c.id] = c.name; });
    var idx = [];
    (data.groups || []).forEach(function (g) {
      var cn = catName[g.category] || "";
      (g.links || []).forEach(function (l) {
        idx.push({
          text: l.text, url: l.url, type: l.type,
          groupTitle: g.title, catName: cn,
          _k: normalize(l.text) + " " + normalize(g.title) + " " + normalize(cn)
        });
      });
      // church directory: index each church's links with its name for context
      var churches = g.churches || [];
      (g.districts || []).forEach(function (d) { churches = churches.concat(d.churches || []); });
      churches.forEach(function (c) {
        (c.links || []).forEach(function (l) {
          var label = c.name + " " + l.label;
          idx.push({
            text: label, url: l.url, type: "external",
            groupTitle: g.title, catName: cn,
            _k: normalize(label) + " " + normalize(g.title) + " " + normalize(cn)
          });
        });
      });
    });
    return idx;
  }

  // Filter index by query; returns up to `limit` matches.
  function search(index, query, limit) {
    var q = normalize(query);
    if (!q) return [];
    var terms = q.split(/\s+/).filter(Boolean);
    var out = [];
    for (var i = 0; i < index.length && out.length < (limit || 80); i++) {
      var item = index[i];
      var ok = terms.every(function (t) { return item._k.indexOf(t) !== -1; });
      if (ok) out.push(item);
    }
    return out;
  }

  // Highlight matched substring in display text.
  function highlight(text, query) {
    var q = (query || "").trim();
    if (!q) return escapeHtml(text);
    var terms = q.split(/\s+/).filter(Boolean).map(escapeReg);
    if (!terms.length) return escapeHtml(text);
    var re = new RegExp("(" + terms.join("|") + ")", "gi");
    return escapeHtml(text).replace(re, '<span class="hl">$1</span>');
  }

  function escapeHtml(s) {
    return (s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function escapeReg(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

  global.TJCSearch = { buildIndex: buildIndex, search: search, highlight: highlight, escapeHtml: escapeHtml };
})(window);
