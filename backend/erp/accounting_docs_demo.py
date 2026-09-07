"""Accounting-docs demo API helpers matching the Vite SPA contract.

Frontend expects wrapped payloads:
  GET /types -> { types: [{ id, label_th, ... }] }
  GET /templates -> { items: [{ id, name, version, doc_type, ... }] }
  GET /documents -> { items: [...] }
  POST /templates/{id}/preview -> HTML text
  POST /templates/{id}/bot/chat -> { reply, preview_html? }
"""

from __future__ import annotations

import copy
import uuid
from typing import Any

from erp import demo_seed as seed

_DOC_TYPE_META = [
    {"id": "invoice", "label_th": "ใบแจ้งหนี้ / Tax Invoice", "label_en": "Tax Invoice"},
    {"id": "billing_note", "label_th": "ใบวางบิล", "label_en": "Billing Note"},
    {"id": "receipt", "label_th": "ใบเสร็จรับเงิน", "label_en": "Receipt"},
    {"id": "credit_note", "label_th": "ใบลดหนี้", "label_en": "Credit Note"},
    {"id": "debit_note", "label_th": "ใบเพิ่มหนี้", "label_en": "Debit Note"},
    {"id": "delivery_note", "label_th": "ใบส่งของ", "label_en": "Delivery Note"},
    {"id": "po", "label_th": "ใบสั่งซื้อ (PO)", "label_en": "Purchase Order"},
]

# Mutable runtime templates (seed + user-created in this process).
_TEMPLATES: list[dict[str, Any]] | None = None
_DOCUMENTS: list[dict[str, Any]] | None = None


def _ensure_templates() -> list[dict[str, Any]]:
    global _TEMPLATES
    if _TEMPLATES is None:
        _TEMPLATES = []
        for row in getattr(seed, "ACCOUNTING_TEMPLATES", []):
            _TEMPLATES.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "doc_type": row.get("type") or row.get("doc_type") or "invoice",
                    "version": int(row.get("version") or 1),
                    "theme_color": row.get("theme_color") or "#0f766e",
                    "show_vat": True,
                    "logo_url": row.get("logo_url") or "",
                    "footer": row.get("footer") or "ThaiTrade Solutions Co., Ltd. — Demo Template",
                }
            )
        # Ensure every doc type has at least one selectable template.
        have = {t["doc_type"] for t in _TEMPLATES}
        for meta in _DOC_TYPE_META:
            if meta["id"] in have:
                continue
            _TEMPLATES.append(
                {
                    "id": f"tpl-{meta['id']}-th",
                    "name": f"{meta['label_th']} (มาตรฐาน)",
                    "doc_type": meta["id"],
                    "version": 1,
                    "theme_color": "#0f766e",
                    "show_vat": True,
                    "logo_url": "",
                    "footer": "ThaiTrade Solutions Co., Ltd. — Demo Template",
                }
            )
    return _TEMPLATES


def _ensure_documents() -> list[dict[str, Any]]:
    global _DOCUMENTS
    if _DOCUMENTS is None:
        _DOCUMENTS = []
        for row in getattr(seed, "ACCOUNTING_DOCUMENTS", []):
            _DOCUMENTS.append(
                {
                    "id": row["id"],
                    "title": row.get("title") or row.get("number") or row["id"],
                    "status": row.get("status") or "draft",
                    "doc_type": row.get("type") or row.get("doc_type") or "invoice",
                    "total": row.get("total"),
                    "customer_name": row.get("customer_name"),
                    "due_date": row.get("due_date"),
                    "html_ready": True,
                    "pdf_ready": True,
                }
            )
    return _DOCUMENTS


def reset_runtime() -> None:
    global _TEMPLATES, _DOCUMENTS
    _TEMPLATES = None
    _DOCUMENTS = None


def list_types() -> dict[str, Any]:
    return {"types": list(_DOC_TYPE_META)}


def list_templates(doc_type: str | None = None) -> dict[str, Any]:
    items = _ensure_templates()
    if doc_type:
        items = [t for t in items if t["doc_type"] == doc_type]
    return {"items": copy.deepcopy(items)}


def get_template(template_id: str) -> dict[str, Any]:
    for t in _ensure_templates():
        if t["id"] == template_id:
            return copy.deepcopy(t)
    raise KeyError(template_id)


def create_template(body: dict[str, Any]) -> dict[str, Any]:
    doc_type = str(body.get("doc_type") or body.get("type") or "invoice")
    name = str(body.get("name") or f"เทมเพลตใหม่ ({doc_type})")
    item = {
        "id": f"tpl-{uuid.uuid4().hex[:8]}",
        "name": name,
        "doc_type": doc_type,
        "version": 1,
        "theme_color": "#0f766e",
        "show_vat": True,
        "logo_url": "",
        "footer": "ThaiTrade Solutions Co., Ltd. — Demo Template",
    }
    _ensure_templates().append(item)
    return copy.deepcopy(item)


def list_documents(doc_type: str | None = None) -> dict[str, Any]:
    items = _ensure_documents()
    if doc_type:
        items = [d for d in items if d.get("doc_type") == doc_type]
    return {"items": copy.deepcopy(items)}


def issue_document(body: dict[str, Any]) -> dict[str, Any]:
    payload = body.get("payload") or {}
    company = (payload.get("company") or {}).get("name") or seed.COMPANY.get("legal_name")
    party = (payload.get("party_to") or {}).get("name") or "ลูกค้า Demo"
    totals = payload.get("totals") or {}
    doc = {
        "id": f"doc-{uuid.uuid4().hex[:8]}",
        "title": f"DOC-{uuid.uuid4().hex[:6].upper()}",
        "status": "issued",
        "doc_type": body.get("doc_type") or "invoice",
        "template_id": body.get("template_id"),
        "company_name": company,
        "customer_name": party,
        "total": totals.get("grand_total"),
        "html_ready": True,
        "pdf_ready": bool(body.get("generate_pdf", True)),
        "payload": payload,
    }
    _ensure_documents().insert(0, doc)
    return copy.deepcopy(doc)


def render_preview_html(template_id: str, payload: dict[str, Any] | None = None) -> str:
    tpl = get_template(template_id)
    company = seed.COMPANY
    payload = payload or {}
    company_name = (payload.get("company") or {}).get("name") or company.get("legal_name")
    party_name = (payload.get("party_to") or {}).get("name") or "ลูกค้าตัวอย่าง"
    lines = payload.get("lines") or [
        {"description": "สินค้า/บริการตัวอย่าง", "qty": 1, "unit_price": 1000, "amount": 1000}
    ]
    totals = payload.get("totals") or {}
    subtotal = totals.get("subtotal")
    if subtotal is None:
        subtotal = sum(float(x.get("amount") or 0) for x in lines)
    tax = totals.get("tax")
    if tax is None:
        tax = round(float(subtotal) * 0.07, 2) if tpl.get("show_vat") else 0
    grand = totals.get("grand_total")
    if grand is None:
        grand = float(subtotal) + float(tax)
    color = tpl.get("theme_color") or "#0f766e"
    rows = "".join(
        f"<tr><td>{x.get('description','')}</td><td style='text-align:right'>{x.get('qty',1)}</td>"
        f"<td style='text-align:right'>{float(x.get('unit_price') or 0):,.2f}</td>"
        f"<td style='text-align:right'>{float(x.get('amount') or 0):,.2f}</td></tr>"
        for x in lines
    )
    logo = (
        f"<img src='{tpl['logo_url']}' alt='logo' style='max-height:48px;margin-bottom:8px'/>"
        if tpl.get("logo_url")
        else ""
    )
    vat_block = (
        f"<div>VAT 7%: {float(tax):,.2f} THB</div>" if tpl.get("show_vat") else ""
    )
    return f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8"/>
<title>{tpl['name']}</title>
<style>
body{{font-family:Sarabun,Segoe UI,sans-serif;color:#111;margin:24px}}
.hdr{{border-bottom:3px solid {color};padding-bottom:12px;margin-bottom:16px}}
h1{{color:{color};margin:0 0 4px;font-size:22px}}
table{{width:100%;border-collapse:collapse;margin-top:16px}}
th,td{{border:1px solid #ddd;padding:8px;font-size:13px}}
th{{background:{color};color:#fff;text-align:left}}
.tot{{margin-top:12px;text-align:right}}
.foot{{margin-top:28px;color:#666;font-size:12px;border-top:1px dashed #ccc;padding-top:8px}}
</style></head><body>
<div class="hdr">{logo}
<h1>{tpl['name']}</h1>
<div>ประเภท: {tpl['doc_type']} · v{tpl['version']}</div>
</div>
<p><strong>จาก:</strong> {company_name}<br/>
Tax ID: {company.get('tax_id')}<br/>
{company.get('address')}</p>
<p><strong>ถึง:</strong> {party_name}</p>
<table>
<thead><tr><th>รายการ</th><th>จำนวน</th><th>ราคา/หน่วย</th><th>รวม</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<div class="tot">
<div>ยอดก่อนภาษี: {float(subtotal):,.2f} THB</div>
{vat_block}
<div><strong>รวมทั้งสิ้น: {float(grand):,.2f} THB</strong></div>
</div>
<div class="foot">{tpl.get('footer') or ''}</div>
</body></html>"""


def bot_chat(template_id: str, message: str) -> dict[str, Any]:
    tpl = get_template(template_id)
    msg = (message or "").strip().lower()
    reply_bits = []
    if "#" in message:
        # crude color extract
        for part in message.replace(",", " ").split():
            if part.startswith("#") and len(part) >= 4:
                tpl["theme_color"] = part[:7]
                reply_bits.append(f"ตั้งสีหลักเป็น {tpl['theme_color']}")
                break
    if "ซ่อนภาษี" in message or "hide vat" in msg or "no vat" in msg:
        tpl["show_vat"] = False
        reply_bits.append("ซ่อนแถว VAT แล้ว")
    if "แสดงภาษี" in message or "show vat" in msg:
        tpl["show_vat"] = True
        reply_bits.append("แสดง VAT แล้ว")
    if "logo" in msg or "โลโก้" in message:
        for part in message.split():
            if part.startswith("http"):
                tpl["logo_url"] = part
                reply_bits.append("ใส่โลโก้แล้ว")
                break
        else:
            reply_bits.append("ส่ง URL โลโก้มาด้วย เช่น https://...")
    if not reply_bits:
        reply_bits.append(
            "ปรับเทมเพลตจำลองแล้ว — ลองสั่งเช่น 'เปลี่ยนสีเป็น #16a34a' หรือ 'ซ่อนภาษี'"
        )
    tpl["version"] = int(tpl.get("version") or 1) + 1
    # persist mutation
    for i, row in enumerate(_ensure_templates()):
        if row["id"] == template_id:
            _ensure_templates()[i] = tpl
            break
    html = render_preview_html(template_id)
    return {"reply": " · ".join(reply_bits), "preview_html": html, "template": copy.deepcopy(tpl)}
