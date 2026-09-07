/**
 * ERP-Demo UX layer (no React source in-repo):
 * - Home → https://www.inz.lol
 * - English labels overlay
 * - Hide raw JSON payload fields / pretty-print result cards
 * - Manual document entry when OCR/scanner unavailable
 * - Present-campaign mock tab
 * - CFO Scope/Role/Department dropdowns + visible answer
 * - Stock manual barcode hint
 */
(function () {
  var HOME = "https://www.inz.lol";

  var TH_TO_EN = {
    "โมดูล": "Modules",
    "เอกสารบัญชี": "Accounting Docs",
    "เมนู & ต้นทุน": "Menu & Cost",
    "เมนู & ต้นทุนอาหาร": "Menu & Food Cost",
    "วัตถุดิบ": "Ingredients",
    "เติมสต็อก": "Restock",
    "สมาชิก": "Members",
    "ข้อมูลร้าน": "Shop Info",
    "สแกน Barcode": "Scan Barcode",
    "คลังสินค้า": "Warehouse",
    "โหมด (Context-aware)": "Mode (context-aware)",
    "ค้นหา SKU": "Lookup SKU",
    "รับเข้า (+1)": "Stock in (+1)",
    "จ่ายออก (-1)": "Stock out (-1)",
    "นับสต็อก (-1)": "Stocktake (-1)",
    "— ยังไม่มีคลัง —": "— No warehouse yet —",
    "ทดสอบ / พิมพ์ Barcode แล้ว Enter": "Type barcode then press Enter (no scanner needed)",
    "ถาม CFO": "Ask CFO",
    "คำถาม CFO": "CFO question",
    "คำถาม": "Question",
    "คำตอบ CFO": "CFO answer",
    "ยอดขาย (คั่นด้วย comma)": "Sales (comma-separated)",
    "แผนก": "Department",
    "ส่งคำขออนุมัติ": "Submit approval request",
    "ประเภทเอกสาร": "Document type",
    "หัวข้อ": "Title",
    "Payload (JSON)": "Details (plain text — no JSON required)",
    "ส่งเข้าคิวอนุมัติทันที": "Submit to approval queue now",
    "ส่งคำขอ": "Submit request",
    "อัปโหลด Invoice": "Upload Invoice",
    "สแกนและดึงข้อมูล": "Scan & extract",
    "ประวัติการสแกน": "Scan history",
    "ยังไม่ตั้งค่า": "Not configured",
    "เพิ่มพนักงาน": "Add employee",
    "รายชื่อพนักงาน": "Employees",
    "ชื่อ": "Name",
    "เงินเดือน": "Salary",
    "ร้านอาหาร": "Restaurant",
    "รัน Pre-campaign": "Run Pre-campaign",
    "สร้าง Brief": "Create brief",
    "ถาม Athena": "Ask Athena",
  };

  function token() {
    try {
      return localStorage.getItem("erp_access_token") || "";
    } catch (e) {
      return "";
    }
  }

  function authHeaders() {
    return { Authorization: "Bearer " + token(), "Content-Type": "application/json" };
  }

  function injectHome() {
    if (document.getElementById("erp-demo-home-link")) return;
    var side = document.querySelector("aside, nav, .sidebar");
    if (!side) return;
    var a = document.createElement("a");
    a.id = "erp-demo-home-link";
    a.href = HOME;
    a.target = "_top";
    a.rel = "noopener";
    a.textContent = "Home · inz.lol";
    a.style.cssText =
      "display:block;margin:0.5rem 0.75rem 0.75rem;padding:0.45rem 0.65rem;border-radius:6px;background:#0f766e;color:#ecfdf5;text-decoration:none;font-weight:600;font-size:0.9rem;text-align:center";
    side.insertBefore(a, side.firstChild);
  }

  function translateTextNode(node) {
    if (!node || node.nodeType !== 3) return;
    var raw = node.nodeValue;
    if (!raw || !raw.trim()) return;
    var t = raw;
    Object.keys(TH_TO_EN).forEach(function (th) {
      if (t.indexOf(th) >= 0) t = t.split(th).join(TH_TO_EN[th]);
    });
    if (t !== raw) node.nodeValue = t;
  }

  function translateTree(root) {
    if (!root) return;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    var n;
    while ((n = walker.nextNode())) translateTextNode(n);
    // placeholders / titles
    root.querySelectorAll &&
      root.querySelectorAll("input[placeholder], textarea[placeholder], [title]").forEach(function (el) {
        ["placeholder", "title"].forEach(function (attr) {
          var v = el.getAttribute(attr);
          if (!v) return;
          Object.keys(TH_TO_EN).forEach(function (th) {
            if (v.indexOf(th) >= 0) v = v.split(th).join(TH_TO_EN[th]);
          });
          el.setAttribute(attr, v);
        });
      });
  }

  function hideJsonPayloadFields() {
    document.querySelectorAll("label").forEach(function (lab) {
      var t = (lab.textContent || "").trim();
      if (t === "Payload (JSON)" || t.indexOf("Payload") === 0) {
        lab.textContent = "Details (plain text — no JSON required)";
        var area = lab.nextElementSibling;
        if (area && area.tagName === "TEXTAREA") {
          area.placeholder = "Optional notes for approvers (plain language)";
          if ((area.value || "").trim() === "{}") area.value = "";
        }
      }
    });
    // Pretty-print result cards that dump JSON
    document.querySelectorAll(".result-panel pre, pre").forEach(function (pre) {
      if (pre.getAttribute("data-erp-pretty")) return;
      var txt = (pre.textContent || "").trim();
      if (!txt || txt[0] !== "{") return;
      try {
        var obj = JSON.parse(txt);
        var answer = obj.answer || obj.summary || obj.message || obj.reply;
        if (answer) {
          pre.textContent = String(answer);
          pre.style.whiteSpace = "pre-wrap";
          pre.style.fontFamily = "inherit";
          pre.setAttribute("data-erp-pretty", "1");
          return;
        }
        // flatten short key/values without showing braces
        var lines = Object.keys(obj)
          .filter(function (k) {
            return typeof obj[k] !== "object";
          })
          .map(function (k) {
            return k + ": " + obj[k];
          });
        if (lines.length) {
          pre.textContent = lines.join("\n");
          pre.style.whiteSpace = "pre-wrap";
          pre.style.fontFamily = "inherit";
          pre.setAttribute("data-erp-pretty", "1");
        }
      } catch (e) {}
    });
  }

  function enhanceStockManualHint() {
    if (!/\/stock/.test(location.pathname)) return;
    if (document.getElementById("erp-demo-barcode-hint")) return;
    var labels = document.querySelectorAll("label");
    for (var i = 0; i < labels.length; i++) {
      var t = labels[i].textContent || "";
      if (t.indexOf("Barcode") >= 0 || t.indexOf("barcode") >= 0 || t.indexOf("พิมพ์") >= 0) {
        var hint = document.createElement("p");
        hint.id = "erp-demo-barcode-hint";
        hint.style.cssText = "font-size:0.85rem;color:#94a3b8;margin:0.35rem 0 0.75rem";
        hint.textContent =
          "No USB/Bluetooth scanner? Type the barcode in the field below and press Enter — manual entry is fully supported.";
        labels[i].parentElement.insertBefore(hint, labels[i].nextSibling);
        break;
      }
    }
  }

  function enhanceCfoDropdowns() {
    if (!/\/cfo/.test(location.pathname)) return;
    function upgrade(labelText, options) {
      var labels = document.querySelectorAll("label");
      for (var i = 0; i < labels.length; i++) {
        var t = (labels[i].textContent || "").trim();
        if (t !== labelText && TH_TO_EN[labelText] !== t && t !== TH_TO_EN[labelText]) continue;
        var input = labels[i].nextElementSibling;
        if (!input || input.tagName !== "INPUT" || input.getAttribute("data-erp-select")) continue;
        var sel = document.createElement("select");
        sel.className = input.className || "";
        options.forEach(function (opt) {
          var o = document.createElement("option");
          o.value = opt;
          o.textContent = opt;
          if (String(input.value || "").toUpperCase() === opt.toUpperCase()) o.selected = true;
          sel.appendChild(o);
        });
        sel.addEventListener("change", function () {
          input.value = sel.value;
          input.dispatchEvent(new Event("input", { bubbles: true }));
          input.dispatchEvent(new Event("change", { bubbles: true }));
        });
        input.type = "hidden";
        input.setAttribute("data-erp-select", "1");
        input.value = sel.value;
        labels[i].parentElement.insertBefore(sel, input.nextSibling);
      }
    }
    upgrade("Scope", ["ALL", "HQ", "BRANCH", "RESTO", "FINANCE"]);
    upgrade("Role", ["CFO", "Owner", "Finance Manager", "Store Manager", "Analyst"]);
    upgrade("Department", ["Finance", "HR", "Warehouse", "Purchasing", "Marketing", "Operations"]);
    upgrade("แผนก", ["Finance", "HR", "Warehouse", "Purchasing", "Marketing", "Operations"]);
  }

  function enhanceDocumentsManual() {
    if (!/\/documents/.test(location.pathname)) return;
    if (document.getElementById("erp-demo-manual-doc")) return;
    var main = document.querySelector("main") || document.querySelector("#root");
    if (!main) return;
    var card = document.createElement("div");
    card.id = "erp-demo-manual-doc";
    card.className = "card";
    card.style.cssText = "margin:1rem 0;padding:1rem;border:1px dashed #64748b;border-radius:8px";
    card.innerHTML =
      "<h3 style='margin-top:0'>Manual document entry</h3>" +
      "<p style='color:#94a3b8;font-size:0.85rem'>Scanner or OCR unavailable? Enter invoice / TOR / contract details here.</p>" +
      "<label>Document type</label>" +
      "<select data-f='doc_type'><option value='invoice'>Invoice</option><option value='tor'>TOR</option><option value='contract'>Contract</option></select>" +
      "<label>Vendor</label><input data-f='vendor' required placeholder='Vendor name' />" +
      "<label>Invoice / ref no.</label><input data-f='invoice_number' placeholder='INV-2026-0001' />" +
      "<label>Total (THB)</label><input data-f='total' type='number' step='0.01' placeholder='0' />" +
      "<label>Line description</label><input data-f='line_desc' placeholder='What was purchased' />" +
      "<label>Notes</label><textarea data-f='notes' rows='2' placeholder='Optional notes'></textarea>" +
      "<div style='margin-top:0.75rem'><button type='button' class='btn btn-primary' data-manual-save>Save manual entry</button>" +
      "<span data-manual-status style='margin-left:0.75rem;font-size:0.85rem;color:#94a3b8'></span></div>";
    var anchor = main.querySelector("form.card") || main.querySelector(".card") || main;
    anchor.parentElement.insertBefore(card, anchor.nextSibling);
    card.querySelector("[data-manual-save]").addEventListener("click", function () {
      var body = {};
      card.querySelectorAll("[data-f]").forEach(function (el) {
        body[el.getAttribute("data-f")] = el.value;
      });
      var st = card.querySelector("[data-manual-status]");
      st.textContent = "Saving…";
      fetch("/api/documents/manual", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(body),
      })
        .then(function (r) {
          return r.json().then(function (d) {
            return { ok: r.ok, d: d };
          });
        })
        .then(function (res) {
          if (!res.ok) {
            st.textContent = res.d.detail || "Save failed";
            st.style.color = "#b91c1c";
            return;
          }
          st.textContent = "Saved " + (res.d.id || "") + " — refresh history if needed";
          st.style.color = "#0f766e";
        })
        .catch(function (err) {
          st.textContent = String(err);
          st.style.color = "#b91c1c";
        });
    });
  }

  function enhancePresentCampaign() {
    if (!/\/marketing/.test(location.pathname)) return;
    if (document.getElementById("erp-demo-present-tab")) return;
    var tabs = document.querySelector(".tabs");
    if (!tabs) return;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.id = "erp-demo-present-tab";
    btn.className = "tab";
    btn.textContent = "Present-campaign";
    // Insert after Pre-campaign if possible
    if (tabs.children.length >= 1) tabs.insertBefore(btn, tabs.children[1] || null);
    else tabs.appendChild(btn);

    var panel = document.createElement("div");
    panel.id = "erp-demo-present-panel";
    panel.style.display = "none";
    panel.className = "card";
    panel.style.cssText += ";margin-top:1rem;padding:1rem";
    panel.innerHTML =
      "<h3 style='margin-top:0'>Present-campaign (live pulse)</h3>" +
      "<p style='color:#94a3b8;font-size:0.85rem'>Mock live monitoring while a campaign is running.</p>" +
      "<label>Focus channel</label>" +
      "<select data-present-channel><option>facebook</option><option>line</option><option>instagram</option><option>tiktok</option></select>" +
      "<label>Note</label><textarea data-present-note rows='2' placeholder='What should we watch this week?'></textarea>" +
      "<div style='margin-top:0.75rem'><button type='button' class='btn btn-primary' data-present-run>Run present pulse</button></div>" +
      "<pre data-present-out style='white-space:pre-wrap;font-family:inherit;margin-top:1rem'></pre>";
    var host = tabs.parentElement || document.querySelector("main");
    host.appendChild(panel);

    btn.addEventListener("click", function () {
      Array.prototype.forEach.call(tabs.querySelectorAll(".tab"), function (t) {
        t.classList.remove("tab-active");
      });
      btn.classList.add("tab-active");
      // Hide sibling SPA forms lightly
      host.querySelectorAll("form.card").forEach(function (f) {
        f.style.display = "none";
      });
      panel.style.display = "block";
    });

    panel.querySelector("[data-present-run]").addEventListener("click", function () {
      var out = panel.querySelector("[data-present-out]");
      out.textContent = "Loading…";
      fetch("/api/marketing/campaigns/present", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          channel: panel.querySelector("[data-present-channel]").value,
          note: panel.querySelector("[data-present-note]").value,
        }),
      })
        .then(function (r) {
          return r.json();
        })
        .then(function (d) {
          var lines = [d.summary || "Present campaign pulse"];
          (d.alerts || []).forEach(function (a) {
            lines.push("• " + a);
          });
          (d.live_campaigns || []).slice(0, 5).forEach(function (c) {
            lines.push(
              "- " +
                c.name +
                " | " +
                c.channel +
                " | CTR " +
                c.ctr +
                " | spend " +
                c.spend
            );
          });
          out.textContent = lines.join("\n");
        })
        .catch(function (err) {
          out.textContent = String(err);
        });
    });
  }

  function tick() {
    document.documentElement.lang = "en";
    injectHome();
    translateTree(document.body);
    hideJsonPayloadFields();
    enhanceStockManualHint();
    enhanceCfoDropdowns();
    enhanceDocumentsManual();
    enhancePresentCampaign();
  }

  var obs = new MutationObserver(function () {
    tick();
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", tick);
  else tick();
  window.addEventListener("popstate", function () {
    setTimeout(tick, 80);
  });
})();
