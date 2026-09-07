/**
 * Inject Upload Logo / Upload Template buttons on เอกสารบัญชี page.
 * SPA has no React source in this repo — enhance DOM after mount.
 */
(function () {
  var PANEL_ID = "erp-demo-upload-panel";

  function token() {
    try {
      return localStorage.getItem("erp_access_token") || "";
    } catch (e) {
      return "";
    }
  }

  function findTemplateSelect() {
    var labels = document.querySelectorAll("label");
    for (var i = 0; i < labels.length; i++) {
      if ((labels[i].textContent || "").trim() === "เลือกเทมเพลต") {
        var el = labels[i].nextElementSibling;
        if (el && el.tagName === "SELECT") return el;
      }
    }
    // fallback: select that has options with "(v"
    var selects = document.querySelectorAll("select");
    for (var j = 0; j < selects.length; j++) {
      var opts = selects[j].options || [];
      for (var k = 0; k < opts.length; k++) {
        if ((opts[k].textContent || "").indexOf("(v") >= 0) return selects[j];
      }
    }
    return null;
  }

  function selectedTemplateId() {
    var sel = findTemplateSelect();
    return sel && sel.value ? sel.value : "";
  }

  function selectedDocType() {
    var labels = document.querySelectorAll("label");
    for (var i = 0; i < labels.length; i++) {
      if ((labels[i].textContent || "").indexOf("ประเภทเอกสาร") >= 0) {
        var el = labels[i].nextElementSibling;
        if (el && el.tagName === "SELECT") return el.value || "invoice";
      }
    }
    return "invoice";
  }

  function setStatus(panel, msg, isErr) {
    var s = panel.querySelector("[data-upload-status]");
    if (!s) return;
    s.textContent = msg || "";
    s.style.color = isErr ? "#b91c1c" : "var(--muted, #666)";
  }

  function refreshPreviewFromHtml(html) {
    var frame = document.querySelector("iframe.doc-preview-frame, iframe[title='preview']");
    if (frame && html) {
      frame.srcdoc = html;
      return;
    }
    // trigger existing Preview button if present
    var buttons = document.querySelectorAll("button");
    for (var i = 0; i < buttons.length; i++) {
      if ((buttons[i].textContent || "").trim() === "ดูตัวอย่าง") {
        buttons[i].click();
        break;
      }
    }
  }

  async function uploadLogo(panel, file) {
    var tid = selectedTemplateId();
    if (!tid) {
      setStatus(panel, "เลือกเทมเพลตก่อนอัปโหลดโลโก้", true);
      return;
    }
    var fd = new FormData();
    fd.append("file", file);
    setStatus(panel, "กำลังอัปโหลดโลโก้…");
    var res = await fetch("/api/accounting-docs/templates/" + encodeURIComponent(tid) + "/upload-logo", {
      method: "POST",
      headers: { Authorization: "Bearer " + token() },
      body: fd,
    });
    var data = await res.json().catch(function () { return {}; });
    if (!res.ok) {
      setStatus(panel, data.detail || "อัปโหลดโลโก้ไม่สำเร็จ", true);
      return;
    }
    setStatus(panel, "ใส่โลโก้แล้ว — " + (data.logo_url || ""));
    if (data.preview_html) refreshPreviewFromHtml(data.preview_html);
  }

  async function uploadTemplate(panel, file) {
    var fd = new FormData();
    fd.append("file", file);
    fd.append("doc_type", selectedDocType());
    fd.append("name", "อัปโหลด: " + file.name);
    setStatus(panel, "กำลังอัปโหลดเทมเพลต/ไฟล์…");
    var res = await fetch("/api/accounting-docs/uploads", {
      method: "POST",
      headers: { Authorization: "Bearer " + token() },
      body: fd,
    });
    var data = await res.json().catch(function () { return {}; });
    if (!res.ok) {
      setStatus(panel, data.detail || "อัปโหลดไม่สำเร็จ", true);
      return;
    }
    setStatus(panel, "อัปโหลดสำเร็จ — รีเฟรชรายการเทมเพลตหรือกดดูตัวอย่าง");
    if (data.preview_html) refreshPreviewFromHtml(data.preview_html);
    // Best-effort: reload page section by clicking templates tab context
    setTimeout(function () {
      location.reload();
    }, 600);
  }

  function mountPanel(anchor) {
    if (document.getElementById(PANEL_ID)) return;
    var panel = document.createElement("div");
    panel.id = PANEL_ID;
    panel.style.cssText =
      "margin-top:1rem;padding:0.75rem;border:1px dashed #94a3b8;border-radius:8px;background:rgba(15,118,110,0.06)";
    panel.innerHTML =
      '<div style="font-weight:600;margin-bottom:0.35rem">อัปโหลดของลูกค้า</div>' +
      '<p style="font-size:0.85rem;color:var(--muted,#64748b);margin:0 0 0.5rem">รองรับโลโก้ (PNG/JPG/SVG/WebP) หรือไฟล์เทมเพลต (HTML/JSON/PDF/รูป)</p>' +
      '<div style="display:flex;flex-wrap:wrap;gap:0.5rem;align-items:center">' +
      '<label class="btn btn-ghost" style="cursor:pointer;display:inline-block;padding:0.4rem 0.7rem;border:1px solid #cbd5e1;border-radius:6px">' +
      'อัปโหลดโลโก้<input type="file" accept="image/*,.svg" data-upload="logo" hidden /></label>' +
      '<label class="btn btn-ghost" style="cursor:pointer;display:inline-block;padding:0.4rem 0.7rem;border:1px solid #cbd5e1;border-radius:6px">' +
      'อัปโหลดเทมเพลต<input type="file" accept="image/*,.html,.htm,.json,.pdf" data-upload="template" hidden /></label>' +
      "</div>" +
      '<div data-upload-status style="font-size:0.8rem;margin-top:0.5rem;min-height:1.2em"></div>';

    var host =
      anchor.closest(".card") ||
      anchor.parentElement ||
      document.querySelector(".grid-2 .card");
    if (!host) return;
    host.appendChild(panel);

    panel.addEventListener("change", function (ev) {
      var input = ev.target;
      if (!input || input.tagName !== "INPUT" || input.type !== "file") return;
      var file = input.files && input.files[0];
      if (!file) return;
      var kind = input.getAttribute("data-upload");
      (kind === "logo" ? uploadLogo(panel, file) : uploadTemplate(panel, file)).catch(function (err) {
        setStatus(panel, String(err && err.message ? err.message : err), true);
      });
      input.value = "";
    });
  }

  function tryInject() {
    if (document.getElementById(PANEL_ID)) return;
    var nodes = document.querySelectorAll("h3,p,label,button");
    for (var i = 0; i < nodes.length; i++) {
      var t = (nodes[i].textContent || "").trim();
      if (t === "Template Design BOT" || t.indexOf("บอก BOT") === 0 || t === "ดูตัวอย่าง") {
        mountPanel(nodes[i]);
        return;
      }
    }
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
})();
