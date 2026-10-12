// Cascade docs search: loads search-index.json on first use and matches every word of the query
// against each section's page, heading and text. No dependencies.
(function () {
  var input = document.getElementById("q");
  var list = document.getElementById("results");
  if (!input || !list) return;
  var index = null, loading = null, active = -1, items = [];

  function load() {
    if (index || loading) return loading;
    loading = fetch("search-index.json").then(function (r) { return r.json(); })
      .then(function (data) {
        index = data.map(function (e) {
          return { e: e, h: e.h.toLowerCase(), p: e.p.toLowerCase(), x: e.x.toLowerCase() };
        });
      }).catch(function () { index = []; });
    return loading;
  }

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }

  function snippet(text, terms) {
    var low = text.toLowerCase(), at = -1;
    for (var i = 0; i < terms.length && at < 0; i++) at = low.indexOf(terms[i]);
    var start = Math.max(0, at - 40);
    var s = (start > 0 ? "…" : "") + text.slice(start, start + 140) + (text.length > start + 140 ? "…" : "");
    s = esc(s);
    var safe = terms.filter(function (t) {
      return t.length >= 2 && /^[\w-]+$/.test(t) && !/^(amp|lt|gt|quot)$/.test(t);   // never touch entities
    });
    if (safe.length) s = s.replace(new RegExp("(" + safe.join("|") + ")", "ig"), "<mark>$1</mark>");   // one pass
    return s;
  }

  function search(q) {
    var terms = q.toLowerCase().split(/[\s.()]+/).filter(Boolean);
    if (!terms.length) return [];
    var out = [];
    index.forEach(function (d) {
      var score = 0;
      for (var i = 0; i < terms.length; i++) {
        var t = terms[i], s = 0;
        if (d.h.indexOf(t) >= 0) s += d.h === t ? 12 : 6;
        if (d.p.indexOf(t) >= 0) s += 3;
        var n = d.x.split(t).length - 1;
        if (n) s += Math.min(n, 5);
        if (!s) return;          // every word must match somewhere
        score += s;
      }
      out.push({ d: d, score: score });
    });
    out.sort(function (a, b) { return b.score - a.score; });
    return out.slice(0, 10).map(function (r) { return { e: r.d.e, terms: terms }; });
  }

  function render() {
    var q = input.value.trim();
    if (!q || !index) { list.hidden = true; list.innerHTML = ""; items = []; return; }
    var res = search(q);
    active = res.length ? 0 : -1;
    list.innerHTML = res.length ? res.map(function (r, i) {
      return '<li role="option"' + (i === 0 ? ' aria-selected="true"' : "") + '><a href="' + esc(r.e.u) + '">' +
        '<span class="rp">' + esc(r.e.p) + '</span><span class="rh">' + esc(r.e.h) + '</span>' +
        (r.e.x ? '<span class="rx">' + snippet(r.e.x, r.terms) + "</span>" : "") + "</a></li>";
    }).join("") : '<li class="none">No results</li>';
    items = list.querySelectorAll("li[role=option]");
    list.hidden = false;
  }

  function move(d) {
    if (!items.length) return;
    if (active >= 0) items[active].removeAttribute("aria-selected");
    active = (active + d + items.length) % items.length;
    items[active].setAttribute("aria-selected", "true");
    items[active].scrollIntoView({ block: "nearest" });
  }

  input.addEventListener("focus", load);
  input.addEventListener("input", function () { load().then(render); });
  input.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
    else if (e.key === "Enter" && active >= 0 && items[active]) { location.href = items[active].querySelector("a").href; }
    else if (e.key === "Escape") { input.value = ""; render(); input.blur(); }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "/" && document.activeElement !== input && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
      e.preventDefault(); input.focus();
    }
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".search")) list.hidden = true;
  });
})();
