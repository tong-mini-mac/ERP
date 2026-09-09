"""High-value procurement workflow (budget > 100,000 THB).

Steps (demo):
0 vendor register → 1 PR+TOR → 2 invite ≥3 quotes → 3 public board
→ 4 AI award + manager approve → 5 PO (<1M) / contract (≥1M)
→ 6 delivery/accept + stock → 7 accounting notify
→ 8 vendor invoice → AP → stock issue already via Stock module
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

HIGH_VALUE_THB = 100_000
CONTRACT_THB = 1_000_000

# Runtime demo state (reset with seed).
VENDOR_REGISTRY: list[dict[str, Any]] = []
TENDERS: list[dict[str, Any]] = []
PUBLIC_BOARD: list[dict[str, Any]] = []
ACCOUNTING_ALERTS: list[dict[str, Any]] = []
VENDOR_INVOICES: list[dict[str, Any]] = []
_seq = {"ven": 100, "tender": 100, "bid": 100, "inv": 100, "alert": 100}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _next(kind: str) -> int:
    _seq[kind] = _seq.get(kind, 100) + 1
    return _seq[kind]


def reset_flow(vendors: list[dict[str, Any]], skus: list[dict[str, Any]]) -> None:
    """Seed a walkthrough high-value tender with 3 invitees + board slot."""
    global VENDOR_REGISTRY, TENDERS, PUBLIC_BOARD, ACCOUNTING_ALERTS, VENDOR_INVOICES
    VENDOR_REGISTRY = []
    for i, v in enumerate(vendors[:8]):
        VENDOR_REGISTRY.append(
            {
                "id": v["id"],
                "name": v["name"],
                "tax_id": v.get("tax_id") or "",
                "phone": v.get("phone") or "",
                "email": f"sales@{v['id']}.demo",
                "categories": ["goods", "services"][i % 2 : ][:1] or ["goods"],
                "registered_at": _now(),
                "status": "active",
                "origin": v.get("origin") or "local",
            }
        )

    sku = skus[5] if len(skus) > 5 else skus[0]
    invitees = VENDOR_REGISTRY[:3]
    tender_id = "tender-hv-001"
    bids = []
    # Three quotes: one non-compliant, two compliant (lowest wins)
    quotes = [
        (invitees[0], 185_000, True, "ครบตาม TOR"),
        (invitees[1], 172_500, True, "ครบตาม TOR + ส่งเร็วกว่า"),
        (invitees[2], 155_000, False, "ขาดเอกสารรับรองคุณภาพ"),
    ]
    for ven, amount, ok, note in quotes:
        bids.append(
            {
                "id": f"bid-{_next('bid')}",
                "vendor_id": ven["id"],
                "vendor_name": ven["name"],
                "amount": amount,
                "currency": "THB",
                "submitted_at": _now(),
                "channel": "invite",
                "tor_compliant": ok,
                "notes": note,
                "score_detail": {},
            }
        )

    TENDERS = [
        {
            "id": tender_id,
            "title": f"จัดซื้อ{sku['name']} สำหรับคลังกลาง (งบสูง)",
            "department": "Operations",
            "pr_id": "pr-hv-1001",
            "tor": {
                "summary": f"จัดหา {sku['name']} ตามสเปกคุณภาพมาตรฐาน จำนวน 500 หน่วย",
                "specs": [
                    f"SKU อ้างอิง: {sku.get('sku') or sku['id']}",
                    "รับประกันอย่างน้อย 12 เดือน",
                    "ส่งมอบภายใน 14 วันหลังออก PO",
                    "มีเอกสารรับรองคุณภาพ",
                ],
                "qty": 500,
                "sku_id": sku["id"],
                "sku_name": sku["name"],
                "unit": sku.get("unit") or "pcs",
            },
            "budget": 220_000,
            "currency": "THB",
            "kind": "goods",  # goods | hire
            "threshold": "high_value",  # >= 100k
            "status": "quoting",  # see STATUS flow
            "invitees": [v["id"] for v in invitees],
            "min_quotes": 3,
            "bids": bids,
            "board": {
                "published": False,
                "opens_at": None,
                "closes_at": None,
                "url_path": f"/procurement/board/{tender_id}",
            },
            "ai_award": None,
            "manager_award_approved": False,
            "manager_award_by": None,
            "document": None,  # PO or contract
            "manager_doc_approved": False,
            "delivery": None,
            "accounting_notified": False,
            "created_at": _now(),
            "updated_at": _now(),
        }
    ]
    PUBLIC_BOARD = []
    ACCOUNTING_ALERTS = []
    VENDOR_INVOICES = []
    _seq.update({"ven": 100, "tender": 100, "bid": 200, "inv": 100, "alert": 100})


def thresholds() -> dict[str, Any]:
    return {
        "high_value_thb": HIGH_VALUE_THB,
        "contract_thb": CONTRACT_THB,
        "min_quotes": 3,
        "steps": [
            {"n": 0, "id": "vendor_register", "th": "ผู้ประกอบการลงทะเบียน"},
            {"n": 1, "id": "pr_tor", "th": "รับใบ PR + TOR"},
            {"n": 2, "id": "invite_quotes", "th": "เชิญเสนอราคา ≥ 3 ราย"},
            {"n": 3, "id": "public_board", "th": "ประกาศบอร์ดสาธารณะ"},
            {"n": 4, "id": "ai_award", "th": "AI พิจารณา + ผู้จัดการอนุมัติ"},
            {"n": 5, "id": "issue_doc", "th": "ออก PO / สัญญา"},
            {"n": 6, "id": "delivery", "th": "ส่งมอบ + ตรวจรับ"},
            {"n": 7, "id": "accounting_notify", "th": "แจ้งบัญชี"},
            {"n": 8, "id": "vendor_invoice", "th": "ใบแจ้งหนี้ → ตั้งเจ้าหนี้"},
        ],
    }


def list_vendors() -> list[dict[str, Any]]:
    return deepcopy(VENDOR_REGISTRY)


def register_vendor(body: dict[str, Any]) -> dict[str, Any]:
    name = str(body.get("name") or "").strip()
    if len(name) < 2:
        raise ValueError("name_required")
    row = {
        "id": f"ven-reg-{_next('ven')}",
        "name": name,
        "tax_id": str(body.get("tax_id") or "").strip(),
        "phone": str(body.get("phone") or "").strip(),
        "email": str(body.get("email") or "").strip(),
        "categories": body.get("categories") or ["goods"],
        "registered_at": _now(),
        "status": "active",
        "origin": "local",
    }
    VENDOR_REGISTRY.insert(0, row)
    return deepcopy(row)


def list_tenders() -> list[dict[str, Any]]:
    return deepcopy(TENDERS)


def get_tender(tender_id: str) -> dict[str, Any] | None:
    for t in TENDERS:
        if t["id"] == tender_id:
            return t
    return None


def create_tender(body: dict[str, Any]) -> dict[str, Any]:
    budget = float(body.get("budget") or 0)
    # User rule: งบประมาณ สูงกว่า 100,000 บาท
    if budget <= HIGH_VALUE_THB:
        raise ValueError("budget_must_be_over_100000")
    tid = f"tender-hv-{_next('tender')}"
    kind = str(body.get("kind") or "goods")
    if kind not in ("goods", "hire"):
        kind = "goods"
    row = {
        "id": tid,
        "title": str(body.get("title") or "งานจัดซื้อ/จ้าง").strip(),
        "department": str(body.get("department") or "Operations").strip(),
        "pr_id": str(body.get("pr_id") or f"pr-hv-{_next('tender')}"),
        "tor": {
            "summary": str(body.get("tor_summary") or "").strip() or "TOR",
            "specs": body.get("tor_specs")
            or [s.strip() for s in str(body.get("tor_text") or "").split("\n") if s.strip()]
            or ["ตามรายละเอียดหน่วยงาน"],
            "qty": int(body.get("qty") or 1),
            "sku_id": body.get("sku_id"),
            "sku_name": body.get("sku_name"),
            "unit": body.get("unit") or "unit",
        },
        "budget": budget,
        "currency": "THB",
        "kind": kind,
        "threshold": "high_value",
        "status": "received",
        "invitees": [],
        "min_quotes": 3,
        "bids": [],
        "board": {
            "published": False,
            "opens_at": None,
            "closes_at": None,
            "url_path": f"/procurement/board/{tid}",
        },
        "ai_award": None,
        "manager_award_approved": False,
        "manager_award_by": None,
        "document": None,
        "manager_doc_approved": False,
        "delivery": None,
        "accounting_notified": False,
        "created_at": _now(),
        "updated_at": _now(),
    }
    TENDERS.insert(0, row)
    return deepcopy(row)


def _touch(t: dict[str, Any]) -> None:
    t["updated_at"] = _now()


def invite_vendors(tender_id: str, vendor_ids: list[str]) -> dict[str, Any]:
    t = get_tender(tender_id)
    if not t:
        raise ValueError("tender_not_found")
    known = {v["id"] for v in VENDOR_REGISTRY}
    add = [vid for vid in vendor_ids if vid in known]
    if not add:
        raise ValueError("vendors_required")
    merged = list(dict.fromkeys([*(t.get("invitees") or []), *add]))
    t["invitees"] = merged
    t["status"] = "quoting"
    _touch(t)
    return deepcopy(t)


def publish_board(tender_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    t = get_tender(tender_id)
    if not t:
        raise ValueError("tender_not_found")
    body = body or {}
    opens = str(body.get("opens_at") or _now())
    closes = str(body.get("closes_at") or _now())
    t["board"] = {
        "published": True,
        "opens_at": opens,
        "closes_at": closes,
        "url_path": f"/procurement/board/{tender_id}",
    }
    t["status"] = "board_open"
    _touch(t)
    # Upsert public board card
    card = {
        "tender_id": t["id"],
        "title": t["title"],
        "budget": t["budget"],
        "kind": t["kind"],
        "opens_at": opens,
        "closes_at": closes,
        "tor_summary": t["tor"]["summary"],
        "bid_count": len(t["bids"]),
    }
    PUBLIC_BOARD[:] = [c for c in PUBLIC_BOARD if c["tender_id"] != t["id"]]
    PUBLIC_BOARD.insert(0, card)
    return deepcopy(t)


def list_board() -> list[dict[str, Any]]:
    out = []
    for t in TENDERS:
        if t.get("board", {}).get("published"):
            out.append(
                {
                    "tender_id": t["id"],
                    "title": t["title"],
                    "budget": t["budget"],
                    "kind": t["kind"],
                    "opens_at": t["board"].get("opens_at"),
                    "closes_at": t["board"].get("closes_at"),
                    "tor_summary": t["tor"]["summary"],
                    "bid_count": len(t["bids"]),
                    "status": t["status"],
                }
            )
    return out


def submit_bid(tender_id: str, body: dict[str, Any]) -> dict[str, Any]:
    t = get_tender(tender_id)
    if not t:
        raise ValueError("tender_not_found")
    if t["status"] not in ("quoting", "board_open", "evaluating"):
        raise ValueError("bidding_closed")
    vendor_id = str(body.get("vendor_id") or "").strip()
    ven = next((v for v in VENDOR_REGISTRY if v["id"] == vendor_id), None)
    if not ven:
        raise ValueError("vendor_not_found")
    amount = float(body.get("amount") or 0)
    if amount <= 0:
        raise ValueError("amount_required")
    # Replace prior bid from same vendor
    t["bids"] = [b for b in t["bids"] if b["vendor_id"] != vendor_id]
    bid = {
        "id": f"bid-{_next('bid')}",
        "vendor_id": vendor_id,
        "vendor_name": ven["name"],
        "amount": amount,
        "currency": "THB",
        "submitted_at": _now(),
        "channel": str(body.get("channel") or "board"),
        "tor_compliant": bool(body.get("tor_compliant", True)),
        "notes": str(body.get("notes") or "").strip(),
        "score_detail": {},
    }
    t["bids"].append(bid)
    _touch(t)
    return deepcopy(bid)


def _median(vals: list[float]) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    if n % 2:
        return float(s[mid])
    return float((s[mid - 1] + s[mid]) / 2)


def ai_evaluate(tender_id: str) -> dict[str, Any]:
    t = get_tender(tender_id)
    if not t:
        raise ValueError("tender_not_found")
    bids = t.get("bids") or []
    if len(bids) < int(t.get("min_quotes") or 3):
        raise ValueError("need_at_least_3_quotes")

    compliant = [b for b in bids if b.get("tor_compliant")]
    amounts = [float(b["amount"]) for b in bids]
    mid = _median(amounts)

    ranked = []
    for b in bids:
        ok = bool(b.get("tor_compliant"))
        amount = float(b["amount"])
        # Lower price better among compliant; non-compliant heavily penalized
        score = (1_000_000 - amount) if ok else -amount
        detail = {
            "tor_match": ok,
            "vs_median_pct": round((amount - mid) / mid * 100, 2) if mid else 0,
            "reason": (
                "ตรงตาม TOR"
                if ok
                else (b.get("notes") or "ไม่ตรงตาม TOR")
            ),
        }
        b["score_detail"] = detail
        ranked.append({**deepcopy(b), "score": score})

    ranked.sort(key=lambda x: (-1 if x["score_detail"]["tor_match"] else 0, x["amount"]))
    winner = next((r for r in ranked if r["score_detail"]["tor_match"]), None)
    if not winner:
        raise ValueError("no_compliant_bid")

    award = {
        "evaluated_at": _now(),
        "median_price": mid,
        "compliant_count": len(compliant),
        "bid_count": len(bids),
        "winner_bid_id": winner["id"],
        "winner_vendor_id": winner["vendor_id"],
        "winner_vendor_name": winner["vendor_name"],
        "winner_amount": winner["amount"],
        "rationale_th": (
            f"AI คัดผู้เสนอที่ตรงตาม TOR และราคาต่ำสุด "
            f"({winner['vendor_name']} @ {winner['amount']:,.0f} THB) "
            f"จากทั้งหมด {len(bids)} ราย (ตรง TOR {len(compliant)} ราย) "
            f"ราคากลางโดยประมาณ {mid:,.0f} THB — รอผู้จัดการอนุมัติ"
        ),
        "ranking": ranked,
    }
    t["ai_award"] = award
    t["status"] = "awaiting_manager_award"
    t["manager_award_approved"] = False
    _touch(t)
    return deepcopy(award)


def manager_approve_award(tender_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    t = get_tender(tender_id)
    if not t:
        raise ValueError("tender_not_found")
    if not t.get("ai_award"):
        raise ValueError("evaluate_first")
    body = body or {}
    if body.get("approve") is False:
        t["status"] = "award_rejected"
        t["manager_award_approved"] = False
        _touch(t)
        return deepcopy(t)
    t["manager_award_approved"] = True
    t["manager_award_by"] = str(body.get("manager") or "procurement_manager")
    t["status"] = "award_approved"
    _touch(t)
    return deepcopy(t)


def issue_document(tender_id: str) -> dict[str, Any]:
    t = get_tender(tender_id)
    if not t:
        raise ValueError("tender_not_found")
    if not t.get("manager_award_approved") or not t.get("ai_award"):
        raise ValueError("manager_award_required")
    amount = float(t["ai_award"]["winner_amount"])
    winner_id = t["ai_award"]["winner_vendor_id"]
    winner_name = t["ai_award"]["winner_vendor_name"]
    if amount >= CONTRACT_THB:
        doc = {
            "type": "contract",
            "number": f"CT-2026-{_next('tender'):04d}",
            "amount": amount,
            "currency": "THB",
            "vendor_id": winner_id,
            "vendor_name": winner_name,
            "issued_at": _now(),
            "status": "awaiting_manager",
            "note_th": "มูลค่า ≥ 1 ล้านบาท — ออกสัญญาซื้อ/จ้าง รอผู้จัดการอนุมัติ",
        }
        t["status"] = "awaiting_manager_doc"
    else:
        doc = {
            "type": "po",
            "number": f"PO-2026-{_next('tender'):04d}",
            "amount": amount,
            "currency": "THB",
            "vendor_id": winner_id,
            "vendor_name": winner_name,
            "issued_at": _now(),
            "status": "issued",
            "note_th": "มูลค่า < 1 ล้านบาท — AI ออกใบ PO/ใบสั่งจ้าง ส่งให้ผู้ชนะได้เลย",
        }
        t["status"] = "doc_issued"
        t["manager_doc_approved"] = True
    t["document"] = doc
    _touch(t)
    return deepcopy(t)


def manager_approve_document(tender_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    t = get_tender(tender_id)
    if not t:
        raise ValueError("tender_not_found")
    doc = t.get("document")
    if not doc:
        raise ValueError("document_missing")
    body = body or {}
    if body.get("approve") is False:
        doc["status"] = "rejected"
        t["status"] = "doc_rejected"
        t["manager_doc_approved"] = False
        _touch(t)
        return deepcopy(t)
    doc["status"] = "issued"
    t["manager_doc_approved"] = True
    t["status"] = "doc_issued"
    _touch(t)
    return deepcopy(t)


def accept_delivery(
    tender_id: str,
    body: dict[str, Any] | None,
    stock_hook: Any | None = None,
) -> dict[str, Any]:
    t = get_tender(tender_id)
    if not t:
        raise ValueError("tender_not_found")
    if t["status"] not in ("doc_issued", "delivering", "accepted_pending_manager"):
        raise ValueError("document_not_ready")
    body = body or {}
    officer = str(body.get("officer") or "receiving_officer")
    qty = int(body.get("qty") or t["tor"].get("qty") or 1)
    delivery = {
        "received_at": _now(),
        "officer": officer,
        "qty": qty,
        "kind": t["kind"],
        "manager_approved": False,
        "stock_posted": False,
        "note": str(body.get("note") or "").strip(),
    }
    t["delivery"] = delivery
    t["status"] = "accepted_pending_manager"
    _touch(t)

    # Goods: stage stock movement when manager approves (step 6 final)
    if stock_hook and t["kind"] == "goods":
        delivery["_stock_hook_ready"] = True
    return deepcopy(t)


def manager_approve_delivery(
    tender_id: str,
    body: dict[str, Any] | None = None,
    stock_hook: Any | None = None,
) -> dict[str, Any]:
    t = get_tender(tender_id)
    if not t:
        raise ValueError("tender_not_found")
    d = t.get("delivery")
    if not d:
        raise ValueError("delivery_missing")
    body = body or {}
    if body.get("approve") is False:
        t["status"] = "delivery_rejected"
        d["manager_approved"] = False
        _touch(t)
        return deepcopy(t)
    d["manager_approved"] = True
    d["manager_by"] = str(body.get("manager") or "procurement_manager")
    t["status"] = "delivered"
    if stock_hook and t["kind"] == "goods" and not d.get("stock_posted"):
        stock_hook(t)
        d["stock_posted"] = True
    _touch(t)
    # Auto accounting notify (step 7)
    notify_accounting(tender_id)
    return deepcopy(t)


def notify_accounting(tender_id: str) -> dict[str, Any]:
    t = get_tender(tender_id)
    if not t:
        raise ValueError("tender_not_found")
    if t["status"] not in ("delivered", "invoiced", "ap_posted"):
        # allow notify after delivery
        if not (t.get("delivery") or {}).get("manager_approved"):
            raise ValueError("delivery_not_approved")
    alert = {
        "id": f"acct-alert-{_next('alert')}",
        "tender_id": t["id"],
        "title": t["title"],
        "amount": (t.get("ai_award") or {}).get("winner_amount") or t["budget"],
        "vendor_name": (t.get("ai_award") or {}).get("winner_vendor_name"),
        "message_th": (
            f"ส่งมอบงาน/สินค้าของ {t['title']} เรียบร้อยแล้ว "
            "รอใบแจ้งหนี้จากผู้ประกอบการเพื่อตั้งเจ้าหนี้"
        ),
        "created_at": _now(),
        "status": "open",
    }
    ACCOUNTING_ALERTS.insert(0, alert)
    t["accounting_notified"] = True
    if t["status"] == "delivered":
        t["status"] = "awaiting_invoice"
    _touch(t)
    return deepcopy(alert)


def list_accounting_alerts() -> list[dict[str, Any]]:
    return deepcopy(ACCOUNTING_ALERTS)


def submit_vendor_invoice(tender_id: str, body: dict[str, Any]) -> dict[str, Any]:
    t = get_tender(tender_id)
    if not t:
        raise ValueError("tender_not_found")
    if not (t.get("delivery") or {}).get("manager_approved"):
        raise ValueError("delivery_not_approved")
    amount = float(body.get("amount") or (t.get("ai_award") or {}).get("winner_amount") or 0)
    inv = {
        "id": f"vinv-{_next('inv')}",
        "tender_id": tender_id,
        "vendor_id": (t.get("ai_award") or {}).get("winner_vendor_id"),
        "vendor_name": (t.get("ai_award") or {}).get("winner_vendor_name"),
        "number": str(body.get("number") or f"INV-V-{_next('inv')}"),
        "amount": amount,
        "currency": "THB",
        "submitted_at": _now(),
        "status": "pending_procurement_check",
        "ap_posted": False,
    }
    VENDOR_INVOICES.insert(0, inv)
    t["status"] = "invoice_received"
    _touch(t)
    return deepcopy(inv)


def verify_invoice_to_ap(invoice_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    inv = next((i for i in VENDOR_INVOICES if i["id"] == invoice_id), None)
    if not inv:
        raise ValueError("invoice_not_found")
    t = get_tender(inv["tender_id"])
    if not t:
        raise ValueError("tender_not_found")
    body = body or {}
    if body.get("approve") is False:
        inv["status"] = "rejected"
        t["status"] = "invoice_rejected"
        _touch(t)
        return deepcopy(inv)

    # Match delivery amount within 1%
    expected = float((t.get("ai_award") or {}).get("winner_amount") or 0)
    if expected and abs(float(inv["amount"]) - expected) / expected > 0.01:
        raise ValueError("amount_mismatch")

    inv["status"] = "sent_to_accounting"
    inv["ap_posted"] = True
    inv["ap_ref"] = f"AP-{inv['number']}"
    inv["verified_at"] = _now()
    t["status"] = "ap_posted"
    _touch(t)
    # Close matching accounting alert
    for a in ACCOUNTING_ALERTS:
        if a["tender_id"] == t["id"] and a["status"] == "open":
            a["status"] = "closed"
    return deepcopy(inv)


def list_vendor_invoices() -> list[dict[str, Any]]:
    return deepcopy(VENDOR_INVOICES)
