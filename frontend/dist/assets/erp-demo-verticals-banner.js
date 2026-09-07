/**
 * Show industry verticals status: Resto = demo-ready, others = pending.
 * SPA has no React source in-repo — enhance DOM after mount.
 */
(function () {
  var PANEL_ID = "erp-demo-verticals-panel";
  var CACHE = null;

  function token() {
    try {
      return localStorage.getItem("erp_access_token") || "";
    } catch (e) {
      return "";
    }
  }

  function fetchBusinesses(cb) {
    if (CACHE) {
      cb(CACHE);
      return;
    }
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/api/demo/businesses");
    xhr.setRequestHeader("Authorization", "Bearer " + token());
    xhr.onload = function () {
      try {
        CACHE = JSON.parse(xhr.responseText || "{}");
      } catch (e) {
        CACHE = { items: [] };
      }
      cb(CACHE);
    };
    xhr.onerror = function () {
      cb({ items: [] });
    };
    xhr.send();
  }

  function statusBadge(status) {
    if (status === "demo") {
      return '<span style="display:inline-block;padding:0.15rem 0.45rem;border-radius:4px;background:#0f766e;color:#ecfdf5;font-size:0.72rem;font-weight:600">demo</span>';
    }
    return '<span style="display:inline-block;padding:0.15rem 0.45rem;border-radius:4px;background:#475569;color:#e2e8f0;font-size:0.72rem;font-weight:600">pending</span>';
  }

  function renderPanel(data) {
    var items = data.items || [];
    if (!items.length) return null;
    var panel = document.createElement("div");
    panel.id = PANEL_ID;
    panel.style.cssText =
      "margin:0.75rem 0 1rem;padding:0.85rem 1rem;border:1px solid #334155;border-radius:8px;background:rgba(15,23,42,0.55)";
    var rows = items
      .map(function (v) {
        var muted = v.status === "pending" ? "opacity:0.72;" : "";
        return (
          '<div style="display:flex;flex-wrap:wrap;gap:0.5rem;align-items:baseline;margin:0.35rem 0;' +
          muted +
          '">' +
          "<div style=\"min-width:7rem;font-weight:600\">" +
          (v.label || v.id) +
          " <span style=\"font-weight:400;color:#94a3b8;font-size:0.85rem\">" +
          (v.label_th || "") +
          "</span></div>" +
          statusBadge(v.status) +
          '<div style="flex:1;min-width:12rem;font-size:0.82rem;color:#94a3b8">' +
          (v.summary || "") +
          "</div></div>"
        );
      })
      .join("");
    panel.innerHTML =
      '<div style="font-weight:600;margin-bottom:0.25rem">ธุรกิจใน ERP-Demo</div>' +
      '<p style="margin:0 0 0.5rem;font-size:0.85rem;color:#94a3b8">' +
      (data.note_th ||
        "ตอนนี้ทดสอบ demo ได้เฉพาะ Resto — ธุรกิจอื่นขึ้นสถานะ pending ไว้ก่อน") +
      "</p>" +
      rows;
    return panel;
  }

  function findAnchor() {
    var path = (location.pathname || "").replace(/\/+$/, "") || "/";
    // Prefer main page header areas on home / marketing / resto-menu.
    if (path === "/" || path === "/dashboard" || path === "/marketing" || path === "/resto-menu") {
      var h1 = document.querySelector("main h1, main h2, .page-header h1, h1");
      if (h1) return h1;
      var at = document.querySelector("main .card, main");
      if (at) return at;
    }
    return null;
  }

  function tryInject() {
    if (document.getElementById(PANEL_ID)) return;
    var anchor = findAnchor();
    if (!anchor) return;
    fetchBusinesses(function (data) {
      if (document.getElementById(PANEL_ID)) return;
      var panel = renderPanel(data);
      if (!panel) return;
      var host = anchor.parentElement || anchor;
      if (anchor.tagName === "H1" || anchor.tagName === "H2") {
        anchor.insertAdjacentElement("afterend", panel);
      } else {
        host.insertBefore(panel, host.firstChild);
      }
    });
  }

  var obs = new MutationObserver(function () {
    tryInject();
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", tryInject);
  } else {
    tryInject();
  }
  window.addEventListener("popstate", function () {
    var old = document.getElementById(PANEL_ID);
    if (old) old.remove();
    setTimeout(tryInject, 50);
  });
})();
