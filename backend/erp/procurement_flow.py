"""Procurement budget bands (demo).

A) ≤ 10,000 THB — petty cash (float 50,000; max 10,000/receipt)
   PR+TOR → buy → collect receipts → clear advance with accounting → month-end reconcile

B) > 10,000 and ≤ 100,000 THB — mid value
   PR+TOR → online market-price research → ≥3 registered quotes
   (optional public board if time) → then same award/PO/delivery/AP as high-value

C) > 100,000 THB — high value (public board + AI award + manager …)
   PO if < 1M; contract if ≥ 1M
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

PETTY_MAX_THB = 10_000
PETTY_FLOAT_THB = 50_000
HIGH_VALUE_THB = 100_000
CONTRACT_THB = 1_000_000

# Runtime demo state (reset with seed).
VENDOR_REGISTRY: list[dict[str, Any]] = []
TENDERS: list[dict[str, Any]] = []
PUBLIC_BOARD: list[dict[str, Any]] = []
ACCOUNTING_ALERTS: list[dict[str, Any]] = []
VENDOR_INVOICES: list[dict[str, Any]] = []
PETTY_CASH: dict[str, Any] = {}
_seq = {
    "ven": 100,
    "tender": 100,
    "bid": 100,
    "inv": 100,
    "alert": 100,
    "petty": 100,
    "clear": 100,
    "recon": 100,
}


def band_for_budget(budget: float) -> str:
    if budget <= PETTY_MAX_THB:
        return "petty"
    if budget <= HIGH_VALUE_THB:
        return "mid_value"
    return "high_value"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _next(kind: str) -> int:
    _seq[kind] = _seq.get(kind, 100) + 1
    return _seq[kind]


def reset_flow(vendors: list[dict[str, Any]], skus: list[dict[str, Any]]) -> None:
    """Seed high + mid tenders and a petty-cash float with sample receipts."""
    global VENDOR_REGISTRY, TENDERS, PUBLIC_BOARD, ACCOUNTING_ALERTS, VENDOR_INVOICES, PETTY_CASH
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
    mid_sku = skus[2] if len(skus) > 2 else sku
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

    mid_id = "tender-mid-001"
    mid_bids = []
    mid_quotes = [
        (invitees[0], 42_000, True, "ครบตาม TOR"),
        (invitees[1], 38_500, True, "ครบตาม TOR"),
        (invitees[2], 41_200, True, "ครบตาม TOR"),
    ]
    for ven, amount, ok, note in mid_quotes:
        mid_bids.append(
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
            "kind": "goods",
            "threshold": "high_value",
            "status": "quoting",
            "invitees": [v["id"] for v in invitees],
            "min_quotes": 3,
            "bids": bids,
            "market_research": None,
            "board": {
                "published": False,
                "opens_at": None,
                "closes_at": None,
                "url_path": f"/procurement/board/{tender_id}",
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
        },
        {
            "id": mid_id,
            "title": f"จัดซื้อ{mid_sku['name']} (งบกลาง 10k–100k)",
            "department": "Admin",
            "pr_id": "pr-mid-1001",
            "tor": {
                "summary": f"จัดหา {mid_sku['name']} จำนวน 40 หน่วย ตามความต้องการหน่วยงาน",
                "specs": [
                    f"SKU อ้างอิง: {mid_sku.get('sku') or mid_sku['id']}",
                    "คุณภาพมาตรฐานตลาด",
                    "ส่งมอบภายใน 7 วัน",
                ],
                "qty": 40,
                "sku_id": mid_sku["id"],
                "sku_name": mid_sku["name"],
                "unit": mid_sku.get("unit") or "pcs",
            },
            "budget": 45_000,
            "currency": "THB",
            "kind": "goods",
            "threshold": "mid_value",
            "status": "quoting",
            "invitees": [v["id"] for v in invitees],
            "min_quotes": 3,
            "bids": mid_bids,
            "market_research": {
                "researched_at": _now(),
                "sources": [
                    {"site": "shopee.demo", "price": 39_900, "url": "https://shopee.demo/item/1"},
                    {"site": "lazada.demo", "price": 41_500, "url": "https://lazada.demo/item/2"},
                    {"site": "market.demo", "price": 40_200, "url": "https://market.demo/item/3"},
                ],
                "market_median": 40_200.0,
                "market_min": 39_900.0,
                "market_max": 41_500.0,
                "note_th": "ค้นหาราคาออนไลน์เพื่อหาราคากลาง/ราคาตลาด",
            },
            "board": {
                "published": False,
                "opens_at": None,
                "closes_at": None,
                "url_path": f"/procurement/board/{mid_id}",
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
        },
    ]
    PUBLIC_BOARD = []
    ACCOUNTING_ALERTS = []
    VENDOR_INVOICES = []
    PETTY_CASH = {
        "float_thb": PETTY_FLOAT_THB,
        "balance_thb": PETTY_FLOAT_THB - 8_500,
        "per_bill_max_thb": PETTY_MAX_THB,
        "currency": "THB",
        "purchases": [
            {
                "id": "petty-101",
                "pr_id": "pr-petty-1001",
                "title": "ซื้อวัสดุสำนักงานด่วน",
                "department": "Admin",
                "tor_summary": "ปากกา/แฟ้ม ตาม TOR หน่วยงาน",
                "amount": 3_200,
                "receipt_no": "RC-8801",
                "vendor_name": "ร้านอุปกรณ์ใกล้เคียง",
                "purchased_at": _now(),
                "status": "pending_clearance",
                "cleared_batch_id": None,
            },
            {
                "id": "petty-102",
                "pr_id": "pr-petty-1002",
                "title": "ซื้อแบตเตอรี่สำรอง",
                "department": "IT",
                "tor_summary": "แบต UPS สำรอง ตาม TOR",
                "amount": 5_300,
                "receipt_no": "RC-8802",
                "vendor_name": "IT Corner",
                "purchased_at": _now(),
                "status": "pending_clearance",
                "cleared_batch_id": None,
            },
        ],
        "clearance_batches": [],
        "month_reconciles": [],
    }
    _seq.update(
        {
            "ven": 100,
            "tender": 100,
            "bid": 300,
            "inv": 100,
            "alert": 100,
            "petty": 110,
            "clear": 100,
            "recon": 100,
        }
    )


def thresholds() -> dict[str, Any]:
    return {
        "petty_max_thb": PETTY_MAX_THB,
        "petty_float_thb": PETTY_FLOAT_THB,
        "high_value_thb": HIGH_VALUE_THB,
        "contract_thb": CONTRACT_THB,
        "min_quotes": 3,
        "bands": [
            {
                "id": "petty",
                "th": "≤ 10,000 — เงินสดยืมถือ (float 50,000 / บิลไม่เกิน 10,000)",
                "steps": [
                    {"n": 1, "id": "pr_tor", "th": "รับ PR + TOR จากหน่วยงาน"},
                    {"n": 2, "id": "buy_cash", "th": "ซื้อด้วยเงินสดยืม (≤10,000/บิล)"},
                    {"n": 3, "id": "collect_receipts", "th": "รวบรวมบิล/ใบเสร็จ ส่งบัญชีเคลียร์ยอดยืม"},
                    {"n": 4, "id": "month_reconcile", "th": "กระทบยอดค่าใช้จ่ายทุกสิ้นเดือน"},
                ],
            },
            {
                "id": "mid_value",
                "th": "> 10,000 และ ≤ 100,000",
                "steps": [
                    {"n": 1, "id": "pr_tor", "th": "ได้ PR + TOR"},
                    {"n": 2, "id": "market_research", "th": "ค้นหาราคาตลาดออนไลน์ (ราคากลาง)"},
                    {
                        "n": 3,
                        "id": "quotes_or_board",
                        "th": "ขอราคา ≥3 รายที่ลงทะเบียน หรือเปิด bidding สาธารณะถ้ามีเวลา",
                    },
                    {"n": 4, "id": "same_as_high", "th": "จากนั้นทำตามขั้นตอนเหมือนงบ >100,000"},
                ],
            },
            {
                "id": "high_value",
                "th": "> 100,000",
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
            },
        ],
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
    band = band_for_budget(budget)
    if band == "petty":
        raise ValueError("budget_petty_use_petty_cash_api")
    # Mid: >10k and ≤100k; High: >100k
    if band not in ("mid_value", "high_value"):
        raise ValueError("budget_out_of_range")
    prefix = "tender-mid" if band == "mid_value" else "tender-hv"
    tid = f"{prefix}-{_next('tender')}"
    kind = str(body.get("kind") or "goods")
    if kind not in ("goods", "hire"):
        kind = "goods"
    row = {
        "id": tid,
        "title": str(body.get("title") or "งานจัดซื้อ/จ้าง").strip(),
        "department": str(body.get("department") or "Operations").strip(),
        "pr_id": str(body.get("pr_id") or f"pr-{band[:3]}-{_next('tender')}"),
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
        "threshold": band,
        "status": "received",
        "invitees": [],
        "min_quotes": 3,
        "bids": [],
        "market_research": None,
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


def research_market_price(tender_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Mock online market-price research → median / min / max (mid-tier step 2)."""
    t = get_tender(tender_id)
    if not t:
        raise ValueError("tender_not_found")
    body = body or {}
    sources = body.get("sources")
    if not sources:
        base = float(t.get("budget") or 40_000) * 0.9
        sources = [
            {
                "site": "shopee.demo",
                "price": round(base * 0.98, 2),
                "url": f"https://shopee.demo/search?q={t['id']}",
            },
            {
                "site": "lazada.demo",
                "price": round(base * 1.05, 2),
                "url": f"https://lazada.demo/search?q={t['id']}",
            },
            {
                "site": "market.demo",
                "price": round(base * 1.01, 2),
                "url": f"https://market.demo/search?q={t['id']}",
            },
        ]
    prices = [float(s["price"]) for s in sources if float(s.get("price") or 0) > 0]
    if len(prices) < 2:
        raise ValueError("need_at_least_2_online_prices")
    research = {
        "researched_at": _now(),
        "sources": sources,
        "market_median": _median(prices),
        "market_min": min(prices),
        "market_max": max(prices),
        "note_th": str(body.get("note_th") or "ค้นหาราคาออนไลน์เพื่อหาราคากลาง/ราคาตลาด"),
    }
    t["market_research"] = research
    if t.get("status") in ("received", "quoting"):
        t["status"] = "market_researched" if not t.get("invitees") else "quoting"
    _touch(t)
    return deepcopy(research)


def ai_evaluate(tender_id: str) -> dict[str, Any]:
    t = get_tender(tender_id)
    if not t:
        raise ValueError("tender_not_found")
    bids = t.get("bids") or []
    if len(bids) < int(t.get("min_quotes") or 3):
        raise ValueError("need_at_least_3_quotes")
    # Mid-tier must research online market price first
    if t.get("threshold") == "mid_value" and not t.get("market_research"):
        raise ValueError("market_research_required")

    compliant = [b for b in bids if b.get("tor_compliant")]
    amounts = [float(b["amount"]) for b in bids]
    mid = _median(amounts)
    market_mid = (t.get("market_research") or {}).get("market_median")

    ranked = []
    for b in bids:
        ok = bool(b.get("tor_compliant"))
        amount = float(b["amount"])
        # Lower price better among compliant; non-compliant heavily penalized
        score = (1_000_000 - amount) if ok else -amount
        detail = {
            "tor_match": ok,
            "vs_median_pct": round((amount - mid) / mid * 100, 2) if mid else 0,
            "vs_market_pct": (
                round((amount - market_mid) / market_mid * 100, 2) if market_mid else None
            ),
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

    market_note = ""
    if market_mid:
        market_note = f" เทียบราคากลางออนไลน์ {market_mid:,.0f} THB"

    award = {
        "evaluated_at": _now(),
        "median_price": mid,
        "market_median": market_mid,
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
            f"ราคากลางจากใบเสนอ {mid:,.0f} THB{market_note} — รอผู้จัดการอนุมัติ"
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


def petty_cash_status() -> dict[str, Any]:
    pc = PETTY_CASH or {}
    pending = [p for p in pc.get("purchases", []) if p.get("status") == "pending_clearance"]
    spent = sum(float(p["amount"]) for p in pc.get("purchases", []) if p.get("status") != "void")
    return {
        "float_thb": pc.get("float_thb", PETTY_FLOAT_THB),
        "balance_thb": pc.get("balance_thb", PETTY_FLOAT_THB),
        "per_bill_max_thb": pc.get("per_bill_max_thb", PETTY_MAX_THB),
        "currency": "THB",
        "pending_clearance_count": len(pending),
        "pending_clearance_amount": sum(float(p["amount"]) for p in pending),
        "spent_thb": spent,
        "purchases": deepcopy(pc.get("purchases") or []),
        "clearance_batches": deepcopy(pc.get("clearance_batches") or []),
        "month_reconciles": deepcopy(pc.get("month_reconciles") or []),
    }


def petty_purchase(body: dict[str, Any]) -> dict[str, Any]:
    """Buy with petty cash: PR+TOR required, each bill ≤ 10,000."""
    global PETTY_CASH
    if not PETTY_CASH:
        raise ValueError("petty_cash_not_initialized")
    amount = float(body.get("amount") or 0)
    if amount <= 0:
        raise ValueError("amount_required")
    if amount > PETTY_MAX_THB:
        raise ValueError("amount_exceeds_10000_use_mid_or_high_flow")
    if amount > float(PETTY_CASH.get("balance_thb") or 0):
        raise ValueError("insufficient_petty_cash_balance")
    tor = str(body.get("tor_summary") or body.get("tor") or "").strip()
    pr_id = str(body.get("pr_id") or "").strip()
    title = str(body.get("title") or body.get("subject") or "").strip()
    if not tor or not title:
        raise ValueError("pr_tor_required")
    if not pr_id:
        pr_id = f"pr-petty-{_next('petty')}"
    row = {
        "id": f"petty-{_next('petty')}",
        "pr_id": pr_id,
        "title": title,
        "department": str(body.get("department") or "Operations").strip(),
        "tor_summary": tor,
        "amount": amount,
        "receipt_no": str(body.get("receipt_no") or f"RC-{_next('petty')}"),
        "vendor_name": str(body.get("vendor_name") or "ร้านค้าเงินสด").strip(),
        "purchased_at": _now(),
        "status": "pending_clearance",
        "cleared_batch_id": None,
    }
    PETTY_CASH["balance_thb"] = float(PETTY_CASH["balance_thb"]) - amount
    PETTY_CASH["purchases"].insert(0, row)
    return deepcopy(row)


def petty_submit_clearance(body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Bundle pending receipts → send to accounting to clear cash advance."""
    global PETTY_CASH
    body = body or {}
    pending = [p for p in PETTY_CASH.get("purchases", []) if p.get("status") == "pending_clearance"]
    ids = body.get("purchase_ids")
    if ids:
        idset = set(ids)
        pending = [p for p in pending if p["id"] in idset]
    if not pending:
        raise ValueError("no_pending_receipts")
    total = sum(float(p["amount"]) for p in pending)
    batch = {
        "id": f"clear-{_next('clear')}",
        "submitted_at": _now(),
        "purchase_ids": [p["id"] for p in pending],
        "receipt_nos": [p["receipt_no"] for p in pending],
        "amount": total,
        "currency": "THB",
        "status": "sent_to_accounting",
        "note_th": str(
            body.get("note_th")
            or "รวบรวมบิล/ใบเสร็จ ส่งบัญชีเพื่อเคลียร์ยอดเงินยืม"
        ),
        "accounting_ref": f"ADV-CLR-{_next('clear')}",
    }
    for p in pending:
        p["status"] = "cleared"
        p["cleared_batch_id"] = batch["id"]
    PETTY_CASH.setdefault("clearance_batches", []).insert(0, batch)
    ACCOUNTING_ALERTS.insert(
        0,
        {
            "id": f"acct-alert-{_next('alert')}",
            "tender_id": None,
            "petty_clearance_id": batch["id"],
            "title": "เคลียร์เงินสดยืมจัดซื้อ",
            "amount": total,
            "vendor_name": None,
            "message_th": (
                f"ฝ่ายจัดซื้อส่งบิล/ใบเสร็จ {len(pending)} รายการ "
                f"รวม {total:,.0f} THB เพื่อเคลียร์ยอดเงินยืม"
            ),
            "created_at": _now(),
            "status": "open",
            "kind": "petty_clearance",
        },
    )
    return deepcopy(batch)


def petty_month_reconcile(body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Month-end expense reconciliation for petty cash float."""
    global PETTY_CASH
    body = body or {}
    month = str(body.get("month") or _now()[:7])  # YYYY-MM
    float_thb = float(PETTY_CASH.get("float_thb") or PETTY_FLOAT_THB)
    balance = float(PETTY_CASH.get("balance_thb") or 0)
    purchases = [
        p
        for p in PETTY_CASH.get("purchases", [])
        if str(p.get("purchased_at") or "").startswith(month) and p.get("status") != "void"
    ]
    spent = sum(float(p["amount"]) for p in purchases)
    pending = [p for p in purchases if p.get("status") == "pending_clearance"]
    cleared = [p for p in purchases if p.get("status") == "cleared"]
    expected_balance = float_thb - spent
    ok = abs(expected_balance - balance) < 0.01 and len(pending) == 0
    row = {
        "id": f"recon-{_next('recon')}",
        "month": month,
        "reconciled_at": _now(),
        "float_thb": float_thb,
        "balance_thb": balance,
        "spent_thb": spent,
        "expected_balance_thb": expected_balance,
        "purchase_count": len(purchases),
        "cleared_count": len(cleared),
        "pending_count": len(pending),
        "balanced": ok,
        "note_th": str(
            body.get("note_th")
            or (
                "กระทบยอดค่าใช้จ่ายสิ้นเดือนครบถ้วน"
                if ok
                else "ยังมียอดค้างเคลียร์หรือยอดไม่ตรง — ตรวจสอบบิล/ใบเสร็จ"
            )
        ),
        "status": "balanced" if ok else "variance",
    }
    PETTY_CASH.setdefault("month_reconciles", []).insert(0, row)
    return deepcopy(row)


def refill_petty_cash(body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Restore petty cash float to configured ceiling (after accounting clears)."""
    global PETTY_CASH
    body = body or {}
    target = float(body.get("float_thb") or PETTY_CASH.get("float_thb") or PETTY_FLOAT_THB)
    before = float(PETTY_CASH.get("balance_thb") or 0)
    PETTY_CASH["float_thb"] = target
    PETTY_CASH["balance_thb"] = target
    return {
        "before_thb": before,
        "after_thb": target,
        "topped_up_thb": target - before,
        "at": _now(),
    }
