/**
 * ERP-Demo UX layer (no React source in-repo):
 * - TH/EN language toggle (top-right) for the whole UI
 * - Home → https://www.inz.lol
 * - Hide raw JSON payload fields / pretty-print result cards
 * - Manual document entry when OCR/scanner unavailable (failover)
 * - Present-campaign mock tab
 * - CFO Scope/Role/Department dropdowns + visible answer
 * - Stock manual barcode hint (scanner failover)
 */
(function () {
  var HOME = "https://www.inz.lol";
  var LANG_KEY = "erp_ui_lang";
  var applyingLang = false;

  // Longer keys first when applying (sorted at runtime).
  var TH_TO_EN = {
    "เมนู & ต้นทุนอาหาร": "Menu & Food Cost",
    "เมนู & ต้นทุน": "Menu & Cost",
    "เอกสารบัญชี": "Accounting Docs",
    "ส่งคำขออนุมัติ": "Submit approval request",
    "ส่งเข้าคิวอนุมัติทันที": "Submit to approval queue now",
    "ทดสอบ / พิมพ์ Barcode แล้ว Enter": "Failover: type barcode + Enter if scanner is broken",
    "โหมด (Context-aware)": "Mode (context-aware)",
    "ยอดขาย (คั่นด้วย comma)": "Sales (comma-separated)",
    "สแกนและดึงข้อมูล": "Scan & extract",
    "รายชื่อพนักงาน": "Employees",
    "เพิ่มพนักงาน": "Add employee",
    "ประวัติการสแกน": "Scan history",
    "อัปโหลด Invoice": "Upload Invoice",
    "ประเภทเอกสาร": "Document type",
    "คลังสินค้า": "Warehouse",
    "ข้อมูลร้าน": "Shop Info",
    "สแกน Barcode": "Scan Barcode",
    "ค้นหา SKU": "Lookup SKU",
    "รับเข้า (+1)": "Stock in (+1)",
    "จ่ายออก (-1)": "Stock out (-1)",
    "นับสต็อก (-1)": "Stocktake (-1)",
    "— ยังไม่มีคลัง —": "— No warehouse yet —",
    "คำถาม CFO": "CFO question",
    "คำตอบ CFO": "CFO answer",
    "ถาม CFO": "Ask CFO",
    "ถาม Athena": "Ask Athena",
    "สร้าง Brief": "Create brief",
    "รัน Pre-campaign": "Run Pre-campaign",
    "Payload (JSON)": "Details (plain text — no JSON required)",
    "ยังไม่ตั้งค่า": "Not configured",
    "เติมสต็อก": "Restock",
    "วัตถุดิบ": "Ingredients",
    "สมาชิก": "Members",
    "เงินเดือน": "Salary",
    "ร้านอาหาร": "Restaurant",
    "โมดูล": "Modules",
    "คำถาม": "Question",
    "แผนก": "Department",
    "หัวข้อ": "Title",
    "ส่งคำขอ": "Submit request",
    "ชื่อ": "Name",
    "ลา": "Leave",
    "เวลางาน": "Attendance",
    "พนักงาน": "Employees",
    "เมนู & สูตร": "Menu & Recipe",
    "บันทึกวัตถุดิบ": "Save ingredient",
    "เพิ่มวัตถุดิบ": "Add ingredient",
    "ดูตัวอย่าง": "Preview",
    "ออกเอกสาร": "Issue document",
    "ประวัติ": "History",
    "เทมเพลต + BOT": "Template + BOT",
    "เลือกเทมเพลต": "Select template",
    "สร้างเทมเพลตใหม่": "Create new template",
    "ตัวอย่างเอกสาร": "Document preview",
    "อนุมัติ": "Approve",
    "ปฏิเสธ": "Reject",
    "บันทึก": "Save",
    "ยกเลิก": "Cancel",
    "ค้นหา": "Search",
    "ตั้งค่า": "Settings",
    "องค์กร": "Organization",
    "องค์กร (Organization)": "Organization",
  };

  var EN_TO_TH = {};
  Object.keys(TH_TO_EN).forEach(function (th) {
    EN_TO_TH[TH_TO_EN[th]] = th;
  });

  var TH_KEYS = Object.keys(TH_TO_EN).sort(function (a, b) {
    return b.length - a.length;
  });
  var EN_KEYS = Object.keys(EN_TO_TH).sort(function (a, b) {
    return b.length - a.length;
  });

  function getLang() {
    try {
      var v = localStorage.getItem(LANG_KEY);
      if (v === "en" || v === "th") return v;
    } catch (e) {}
    return "th";
  }

  function setLang(lang) {
    try {
      localStorage.setItem(LANG_KEY, lang);
    } catch (e) {}
  }

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

  function tPair(th, en) {
    return getLang() === "en" ? en : th;
  }

  function mapString(str, toEn) {
    if (!str) return str;
    var out = str;
    var keys = toEn ? TH_KEYS : EN_KEYS;
    var dict = toEn ? TH_TO_EN : EN_TO_TH;
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      if (out.indexOf(k) >= 0) out = out.split(k).join(dict[k]);
    }
    return out;
  }

  function translateTextNode(node, toEn) {
    if (!node || node.nodeType !== 3) return;
    var p = node.parentElement;
    if (p && (p.id === "erp-demo-lang-toggle" || (p.closest && p.closest("#erp-demo-lang-toggle")))) return;
    if (p && (p.tagName === "SCRIPT" || p.tagName === "STYLE" || p.tagName === "CODE" || p.tagName === "PRE")) return;

    var raw = node.nodeValue;
    if (!raw || !raw.trim()) return;

    // Thai chars mean SPA refreshed the label — keep original in sync.
    if (/[\u0E00-\u0E7F]/.test(raw)) node.__erpOrig = raw;
    if (node.__erpOrig == null) node.__erpOrig = raw;

    if (toEn) {
      var en = mapString(node.__erpOrig, true);
      if (en !== node.nodeValue) node.nodeValue = en;
    } else if (node.nodeValue !== node.__erpOrig) {
      node.nodeValue = node.__erpOrig;
    }
  }

  function translateAttr(el, attr, toEn) {
    var cur = el.getAttribute(attr);
    if (cur == null) return;
    var key = "__erpOrig_" + attr;
    if (el[key] == null) el[key] = cur;
    if (toEn) el.setAttribute(attr, mapString(el[key], true));
    else el.setAttribute(attr, el[key]);
  }

  function translateTree(root, toEn, onlyNew) {
    if (!root) return;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    var n;
    while ((n = walker.nextNode())) {
      if (onlyNew && n.__erpOrig != null && !/[\u0E00-\u0E7F]/.test(n.nodeValue || "")) continue;
      translateTextNode(n, toEn);
    }
    if (root.querySelectorAll) {
      root.querySelectorAll("input[placeholder], textarea[placeholder], [title]").forEach(function (el) {
        if (el.closest && el.closest("#erp-demo-lang-toggle")) return;
        if (onlyNew && el.__erpOrig_placeholder != null) return;
        translateAttr(el, "placeholder", toEn);
        translateAttr(el, "title", toEn);
      });
    }
  }

  function injectLangToggle() {
    var box = document.getElementById("erp-demo-lang-toggle");
    if (!box) {
      box = document.createElement("div");
      box.id = "erp-demo-lang-toggle";
      box.setAttribute("role", "group");
      box.setAttribute("aria-label", "Language");
      box.style.cssText =
        "position:fixed;top:12px;right:12px;z-index:2147483647;display:flex;gap:0;border:1px solid #475569;border-radius:8px;overflow:hidden;background:#0f172a;box-shadow:0 4px 16px rgba(0,0,0,.35);font-family:system-ui,sans-serif;pointer-events:auto";
      ["th", "en"].forEach(function (code) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.setAttribute("data-lang", code);
        btn.textContent = code.toUpperCase();
        btn.style.cssText =
          "border:0;padding:0.45rem 0.85rem;cursor:pointer;font-weight:700;font-size:0.85rem;pointer-events:auto";
        box.appendChild(btn);
      });
      document.body.appendChild(box);

      function onPick(lang) {
        if (lang !== "th" && lang !== "en") return;
        setLang(lang);
        lastAppliedLang = null;
        applyLanguage(true);
      }

      box.addEventListener(
        "click",
        function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          var el = ev.target;
          if (el && el.nodeType === 3) el = el.parentElement;
          while (el && el !== box && !(el.getAttribute && el.getAttribute("data-lang"))) {
            el = el.parentElement;
          }
          if (!el || el === box) return;
          onPick(el.getAttribute("data-lang"));
        },
        true
      );

      window.__erpSetLang = onPick;
    }
    var lang = getLang();
    box.querySelectorAll("[data-lang]").forEach(function (btn) {
      var on = btn.getAttribute("data-lang") === lang;
      btn.style.background = on ? "#0f766e" : "transparent";
      btn.style.color = on ? "#ecfdf5" : "#94a3b8";
    });
  }

  function injectHome() {
    var side = document.querySelector("aside, nav, .sidebar");
    if (!side) return;
    var a = document.getElementById("erp-demo-home-link");
    if (!a) {
      a = document.createElement("a");
      a.id = "erp-demo-home-link";
      a.href = HOME;
      a.target = "_top";
      a.rel = "noopener";
      a.style.cssText =
        "display:block;margin:0.5rem 0.75rem 0.75rem;padding:0.45rem 0.65rem;border-radius:6px;background:#0f766e;color:#ecfdf5;text-decoration:none;font-weight:600;font-size:0.9rem;text-align:center";
      side.insertBefore(a, side.firstChild);
    }
    a.textContent = tPair("หน้าแรก · inz.lol", "Home · inz.lol");
  }

  function hideJsonPayloadFields() {
    document.querySelectorAll("label").forEach(function (lab) {
      var t = (lab.textContent || "").trim();
      if (t === "Payload (JSON)" || t.indexOf("Payload") === 0 || t.indexOf("Details (plain text") === 0) {
        if (lab.__erpOrig == null) lab.__erpOrig = "Payload (JSON)";
        lab.textContent = tPair(
          "รายละเอียด (ข้อความธรรมดา ไม่ต้องใช้ JSON)",
          "Details (plain text — no JSON required)"
        );
        var area = lab.nextElementSibling;
        if (area && area.tagName === "TEXTAREA") {
          area.placeholder = tPair(
            "หมายเหตุสำหรับผู้อนุมัติ (ภาษาปกติ)",
            "Optional notes for approvers (plain language)"
          );
          if ((area.value || "").trim() === "{}") area.value = "";
        }
      }
    });
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
    var hint = document.getElementById("erp-demo-barcode-hint");
    if (!hint) {
      var labels = document.querySelectorAll("label");
      for (var i = 0; i < labels.length; i++) {
        var t = labels[i].textContent || "";
        if (t.indexOf("Barcode") >= 0 || t.indexOf("barcode") >= 0 || t.indexOf("พิมพ์") >= 0) {
          hint = document.createElement("p");
          hint.id = "erp-demo-barcode-hint";
          hint.style.cssText = "font-size:0.85rem;color:#94a3b8;margin:0.35rem 0 0.75rem";
          labels[i].parentElement.insertBefore(hint, labels[i].nextSibling);
          break;
        }
      }
    }
    if (!hint) return;
    hint.textContent = tPair(
      "หลัก: สแกนด้วยเครื่อง USB/Bluetooth (HID) · สำรอง: ถ้าเครื่องเสีย ให้พิมพ์บาร์โค้ดด้านล่างแล้วกด Enter — งานต้องเดินต่อได้",
      "Primary: USB/Bluetooth scanner (HID). Failover: if the scanner is broken or offline, type the barcode below and press Enter — operations must not stop."
    );
  }

  function enhanceCfoDropdowns() {
    if (!/\/cfo/.test(location.pathname)) return;
    function upgrade(labelText, options) {
      var labels = document.querySelectorAll("label");
      for (var i = 0; i < labels.length; i++) {
        var t = (labels[i].textContent || "").trim();
        var en = TH_TO_EN[labelText] || labelText;
        if (t !== labelText && t !== en) continue;
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

  function isDocumentsPage() {
    var path = (location.pathname || "").replace(/\/+$/, "") || "/";
    // Exact OCR Documents page only — NOT /accounting-docs
    return path === "/documents";
  }

  function isRestoMenuPage() {
    var path = (location.pathname || "").replace(/\/+$/, "") || "/";
    return path === "/resto-menu";
  }

  function enhanceDocumentsManual(rebuild) {
    rebuild = !!rebuild;
    var existing = document.getElementById("erp-demo-manual-doc");
    if (!isDocumentsPage()) {
      if (existing) existing.remove();
      return;
    }
    if (existing) return;
    var main = document.querySelector("main") || document.querySelector("#root");
    if (!main) return;
    var card = document.createElement("div");
    card.id = "erp-demo-manual-doc";
    card.className = "card";
    card.style.cssText = "margin:1rem 0;padding:1rem;border:1px dashed #64748b;border-radius:8px";
    card.innerHTML =
      "<h3 style='margin-top:0'>Documents — scan upload + manual failover</h3>" +
      "<p style='color:#94a3b8;font-size:0.85rem;margin-top:0'>Primary: upload a scan file. Failover: if the scanner/OCR is broken, fill the manual form below.</p>" +
      "<div style='padding:0.75rem;margin-bottom:1rem;border:1px solid #334155;border-radius:8px;background:rgba(15,23,42,0.45)'>" +
      "<div style='font-weight:600;margin-bottom:0.35rem'>1) Upload file scan</div>" +
      "<label>Scan file (PNG, JPEG, WebP, PDF)</label>" +
      "<input type='file' accept='image/png,image/jpeg,image/webp,application/pdf' data-scan-file />" +
      "<div style='margin-top:0.5rem'><button type='button' class='btn btn-primary' data-scan-upload>Upload &amp; extract</button>" +
      "<span data-scan-status style='margin-left:0.75rem;font-size:0.85rem;color:#94a3b8'></span></div>" +
      "</div>" +
      "<div style='font-weight:600;margin-bottom:0.35rem'>2) Manual entry (scanner / OCR failover)</div>" +
      "<label>Document type</label>" +
      "<select data-f='doc_type'><option value='invoice'>Invoice</option><option value='tor'>TOR</option><option value='contract'>Contract</option></select>" +
      "<label>Vendor</label><input data-f='vendor' required placeholder='Vendor name' />" +
      "<label>Invoice / ref no.</label><input data-f='invoice_number' placeholder='INV-2026-0001' />" +
      "<label>Total (THB)</label><input data-f='total' type='number' step='0.01' placeholder='0' />" +
      "<label>Line description</label><input data-f='line_desc' placeholder='What was purchased' />" +
      "<label>Notes</label><textarea data-f='notes' rows='2' placeholder='Optional notes'></textarea>" +
      "<div style='margin-top:0.75rem'><button type='button' class='btn btn-primary' data-manual-save>Save manual entry</button>" +
      "<span data-manual-status style='margin-left:0.75rem;font-size:0.85rem;color:#94a3b8'></span></div>";

    // Prefer placing under Document Intelligence header; avoid leaking into other modules.
    var host = main.querySelector(".page") || main;
    var title = null;
    host.querySelectorAll("h1,h2").forEach(function (h) {
      var t = (h.textContent || "").trim();
      if (!title && (t.indexOf("Document") >= 0 || t.indexOf("เอกสาร") >= 0)) title = h;
    });
    if (title && title.parentElement) title.insertAdjacentElement("afterend", card);
    else host.insertBefore(card, host.firstChild);

    card.querySelector("[data-scan-upload]").addEventListener("click", function () {
      var input = card.querySelector("[data-scan-file]");
      var st = card.querySelector("[data-scan-status]");
      var file = input && input.files && input.files[0];
      if (!file) {
        st.textContent = "Choose a scan file first";
        st.style.color = "#b91c1c";
        return;
      }
      var fd = new FormData();
      fd.append("file", file);
      st.textContent = "Uploading scan…";
      st.style.color = "#94a3b8";
      fetch("/api/documents/scan", {
        method: "POST",
        headers: { Authorization: "Bearer " + token() },
        body: fd,
      })
        .then(function (r) {
          return r.json().then(function (d) {
            return { ok: r.ok, d: d };
          });
        })
        .then(function (res) {
          if (!res.ok) {
            st.textContent = res.d.detail || "Upload failed";
            st.style.color = "#b91c1c";
            return;
          }
          st.textContent = "Scan saved " + (res.d.id || "") + " (" + (res.d.status || "parsed") + ")";
          st.style.color = "#0f766e";
        })
        .catch(function (err) {
          st.textContent = String(err);
          st.style.color = "#b91c1c";
        });
    });

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

  function enhanceAddIngredientToDb() {
    var existing = document.getElementById("erp-demo-add-ingredient");
    if (!isRestoMenuPage()) {
      if (existing) existing.remove();
      return;
    }
    if (existing) return;
    var main = document.querySelector("main") || document.querySelector("#root");
    if (!main) return;
    var card = document.createElement("div");
    card.id = "erp-demo-add-ingredient";
    card.className = "card";
    card.style.cssText =
      "margin:1rem 0;padding:1rem;border:1px dashed #0f766e;border-radius:8px;background:rgba(15,118,110,0.08)";
    card.innerHTML =
      "<h3 style='margin-top:0'>Add ingredient to database</h3>" +
      "<p style='color:#94a3b8;font-size:0.85rem;margin-top:0'>Not the same as “+ add line” in a recipe. Use this when the ingredient is missing from the dropdown / database.</p>" +
      "<label>Ingredient name</label><input data-ing='name' required placeholder='e.g. Holy basil' />" +
      "<label>Unit</label><select data-ing='unit'><option>g</option><option>kg</option><option>ml</option><option>l</option><option>pcs</option></select>" +
      "<label>Yield % (usable after prep)</label><input data-ing='yield_pct' type='number' min='1' max='100' step='0.1' value='100' />" +
      "<label>Purchase price / unit (THB)</label><input data-ing='purchase_price' type='number' min='0' step='0.01' value='0' />" +
      "<label>Notes</label><input data-ing='notes' placeholder='Optional' />" +
      "<div style='margin-top:0.75rem'><button type='button' class='btn btn-primary' data-ing-save>+ Add ingredient to database</button>" +
      "<span data-ing-status style='margin-left:0.75rem;font-size:0.85rem;color:#94a3b8'></span></div>";

    var anchor =
      Array.prototype.find.call(document.querySelectorAll("h3,h2,label,button"), function (el) {
        var t = (el.textContent || "").trim();
        return (
          t.indexOf("Ingredients") >= 0 ||
          t.indexOf("วัตถุดิบ") >= 0 ||
          t.indexOf("เพิ่มบรรทัด") >= 0 ||
          t.indexOf("เมนู") >= 0
        );
      }) || main.querySelector(".card") || main;
    var host = anchor.closest(".card") || anchor.parentElement || main;
    host.appendChild(card);

    card.querySelector("[data-ing-save]").addEventListener("click", function () {
      var body = {};
      card.querySelectorAll("[data-ing]").forEach(function (el) {
        body[el.getAttribute("data-ing")] = el.value;
      });
      var st = card.querySelector("[data-ing-status]");
      if (!body.name) {
        st.textContent = "Name required";
        st.style.color = "#b91c1c";
        return;
      }
      st.textContent = "Saving ingredient…";
      st.style.color = "#94a3b8";
      fetch("/api/resto/ingredients", {
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
          st.textContent =
            "Added to database: " +
            (res.d.name || body.name) +
            " (" +
            (res.d.id || "") +
            ") — reload / reopen Ingredients to see it in dropdowns";
          st.style.color = "#0f766e";
        })
        .catch(function (err) {
          st.textContent = String(err);
          st.style.color = "#b91c1c";
        });
    });
  }

    function enhancePresentCampaign(rebuild) {
    if (!/\/marketing/.test(location.pathname)) return;
    var tabs = document.querySelector(".tabs");
    if (!tabs) return;
    var btn = document.getElementById("erp-demo-present-tab");
    if (!btn) {
      btn = document.createElement("button");
      btn.type = "button";
      btn.id = "erp-demo-present-tab";
      btn.className = "tab";
      if (tabs.children.length >= 1) tabs.insertBefore(btn, tabs.children[1] || null);
      else tabs.appendChild(btn);

      var panel = document.createElement("div");
      panel.id = "erp-demo-present-panel";
      panel.style.display = "none";
      panel.className = "card";
      panel.style.cssText += ";margin-top:1rem;padding:1rem";
      var host = tabs.parentElement || document.querySelector("main");
      host.appendChild(panel);

      btn.addEventListener("click", function () {
        Array.prototype.forEach.call(tabs.querySelectorAll(".tab"), function (t) {
          t.classList.remove("tab-active");
        });
        btn.classList.add("tab-active");
        host.querySelectorAll("form.card").forEach(function (f) {
          f.style.display = "none";
        });
        panel.style.display = "block";
      });

      panel.addEventListener("click", function (ev) {
        if (!ev.target.matches("[data-present-run]")) return;
        var out = panel.querySelector("[data-present-out]");
        out.textContent = tPair("กำลังโหลด…", "Loading…");
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
              lines.push("- " + c.name + " | " + c.channel + " | CTR " + c.ctr + " | spend " + c.spend);
            });
            out.textContent = lines.join("\n");
          })
          .catch(function (err) {
            out.textContent = String(err);
          });
      });
    }

    btn.textContent = tPair("Present-campaign", "Present-campaign");
    var panel = document.getElementById("erp-demo-present-panel");
    if (panel && panel.style.display !== "none") {
      // keep content if open; rebuild labels lightly only when empty structure
    }
    if (panel && !panel.querySelector("[data-present-run]")) {
      panel.innerHTML =
        "<h3 style='margin-top:0'>" +
        tPair("Present-campaign (สถานะแคมเปญสด)", "Present-campaign (live pulse)") +
        "</h3>" +
        "<p style='color:#94a3b8;font-size:0.85rem'>" +
        tPair("ม็อคติดตามแคมเปญขณะกำลังรัน", "Mock live monitoring while a campaign is running.") +
        "</p>" +
        "<label>" +
        tPair("ช่องทาง", "Focus channel") +
        "</label>" +
        "<select data-present-channel><option>facebook</option><option>line</option><option>instagram</option><option>tiktok</option></select>" +
        "<label>" +
        tPair("หมายเหตุ", "Note") +
        "</label><textarea data-present-note rows='2' placeholder='" +
        tPair("สัปดาห์นี้ควรจับตาอะไร?", "What should we watch this week?") +
        "'></textarea>" +
        "<div style='margin-top:0.75rem'><button type='button' class='btn btn-primary' data-present-run>" +
        tPair("รัน Present pulse", "Run present pulse") +
        "</button></div>" +
        "<pre data-present-out style='white-space:pre-wrap;font-family:inherit;margin-top:1rem'></pre>";
    } else if (panel && panel.querySelector("h3")) {
      panel.querySelector("h3").textContent = tPair(
        "Present-campaign (สถานะแคมเปญสด)",
        "Present-campaign (live pulse)"
      );
    }
  }

  var lastAppliedLang = null;
  var debounceTimer = null;

  function applyLanguage(force) {
    if (applyingLang) return;
    applyingLang = true;
    try {
      var lang = getLang();
      var toEn = lang === "en";
      var langChanged = lastAppliedLang !== lang;
      document.documentElement.lang = lang;
      injectLangToggle();
      injectHome();
      // Full-tree translate only on lang change or forced navigation refresh.
      if (force || langChanged) {
        translateTree(document.body, toEn, false);
        lastAppliedLang = lang;
      } else {
        // Light pass: only unmarked text nodes (new SPA mounts).
        translateTree(document.body, toEn, true);
      }
      hideJsonPayloadFields();
      enhanceStockManualHint();
      enhanceCfoDropdowns();
      // Rebuild injected forms only when language changes (avoid Mutation loops).
      if (force || langChanged) {
        enhanceDocumentsManual(true);
        enhanceAddIngredientToDb();
        enhancePresentCampaign(true);
      } else {
        enhanceDocumentsManual(false);
        enhanceAddIngredientToDb();
        enhancePresentCampaign(false);
      }
    } finally {
      applyingLang = false;
    }
  }

  function scheduleApply() {
    if (applyingLang) return;
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function () {
      applyLanguage(false);
    }, 250);
  }

  var obs = new MutationObserver(function () {
    if (applyingLang) return;
    scheduleApply();
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () {
    applyLanguage(true);
  });
  else applyLanguage(true);
  window.addEventListener("popstate", function () {
    setTimeout(function () {
      applyLanguage(true);
    }, 80);
  });
})();
