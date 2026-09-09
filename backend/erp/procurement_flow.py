"""Procurement budget bands (demo).

Policy (all bands): scan documents into the system first — every step runs
from digital scans. Receipts, tax invoices, and some important originals may
be sent to accounting later for real tax filing.

A) ≤ 10,000 THB — petty cash (float 50,000; max 10,000/receipt)
B) > 10,000 and ≤ 100,000 THB — mid value (market research + ≥3 quotes)
C) > 100,000 THB — high value (public board + AI award …)
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

PETTY_MAX_THB = 10_000
PETTY_FLOAT_THB = 50_000
HIGH_VALUE_THB = 100_000
CONTRACT_THB = 1_000_000

# All cases: work from scanned docs in-system. Physical originals for tax
# (receipt / tax invoice / similar) may be sent to accounting later.
PHYSICAL_FOLLOWUP_DOC_TYPES = frozenset(
    {"receipt", "tax_invoice", "withholding_cert", "important"}
)
DOC_TYPE_LABELS_TH = {
    "pr": "ใบ PR",
    "tor": "TOR",
    "receipt": "ใบเสร็จ",
    "tax_invoice": "ใบกำกับภาษี",
    "quote": "ใบเสนอราคา",
    "po": "ใบสั่งซื้อ/สั่งจ้าง",
    "contract": "สัญญา",
    "delivery": "ใบส่งมอบ/ตรวจรับ",
    "vendor_invoice": "ใบแจ้งหนี้",
    "withholding_cert": "หนังสือรับรองหัก ณ ที่จ่าย",
    "important": "เอกสารสำคัญ",
    "other": "เอกสารอื่น",
}

# Runtime demo state (reset with seed).
VENDOR_REGISTRY: list[dict[str, Any]] = []
TENDERS: list[dict[str, Any]] = []
PUBLIC_BOARD: list[dict[str, Any]] = []
ACCOUNTING_ALERTS: list[dict[str, Any]] = []
VENDOR_INVOICES: list[dict[str, Any]] = []
PETTY_CASH: dict[str, Any] = {}
PROC_DOCUMENTS: list[dict[str, Any]] = []
_seq = {
    "ven": 100,
    "tender": 100,
    "bid": 100,
    "inv": 100,
    "alert": 100,
    "petty": 100,
    "clear": 100,
    "recon": 100,
    "doc": 100,
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


MOCK_SET_SIZE = 50


def reset_flow(vendors: list[dict[str, Any]], skus: list[dict[str, Any]]) -> None:
    """Seed ≥50 mock rows per procurement collection for testing."""
    global VENDOR_REGISTRY, TENDERS, PUBLIC_BOARD, ACCOUNTING_ALERTS, VENDOR_INVOICES, PETTY_CASH, PROC_DOCUMENTS
    VENDOR_REGISTRY = []
    PROC_DOCUMENTS = []
    n = MOCK_SET_SIZE

    # --- Vendors (≥50) ---
    for i in range(n):
        if i < len(vendors):
            v = vendors[i]
            VENDOR_REGISTRY.append(
                {
                    "id": v["id"],
                    "name": v["name"],
                    "tax_id": v.get("tax_id") or f"01055{7000000 + i}",
                    "phone": v.get("phone") or f"02-{1000 + i:04d}-{1000 + i:04d}",
                    "email": f"sales@{v['id']}.demo",
                    "categories": ["goods"] if i % 2 == 0 else ["services"],
                    "registered_at": _now(),
                    "status": "active" if i % 17 else "pending",
                    "origin": v.get("origin") or "local",
                }
            )
        else:
            VENDOR_REGISTRY.append(
                {
                    "id": f"ven-mock-{i + 1:03d}",
                    "name": f"Mock Vendor {i + 1:03d} Co., Ltd.",
                    "tax_id": f"01055{7000000 + i}",
                    "phone": f"02-{1000 + i:04d}-0000",
                    "email": f"sales{i + 1}@mock-vendor.demo",
                    "categories": ["goods"] if i % 2 == 0 else ["services"],
                    "registered_at": _now(),
                    "status": "active",
                    "origin": "local",
                }
            )

    sku = skus[5] if len(skus) > 5 else skus[0]
    mid_sku = skus[2] if len(skus) > 2 else sku
    invitees = VENDOR_REGISTRY[:3]
    departments = ["Operations", "Admin", "IT", "Finance", "Warehouse", "Marketing"]

    def _three_bids(base: float, channel: str = "invite") -> list[dict[str, Any]]:
        out = []
        spreads = [(0.08, True, "ครบตาม TOR"), (0.0, True, "ครบตาม TOR + ส่งเร็ว"), (-0.05, False, "ขาดเอกสารรับรอง")]
        for j, (spread, ok, note) in enumerate(spreads):
            ven = VENDOR_REGISTRY[j % len(VENDOR_REGISTRY)]
            out.append(
                {
                    "id": f"bid-{_next('bid')}",
                    "vendor_id": ven["id"],
                    "vendor_name": ven["name"],
                    "amount": round(base * (1 + spread), 2),
                    "currency": "THB",
                    "submitted_at": _now(),
                    "channel": channel,
                    "tor_compliant": ok,
                    "notes": note,
                    "score_detail": {},
                }
            )
        return out

    # Walkthrough anchors (kept first for UI demos)
    tender_hv = {
        "id": "tender-hv-001",
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
        "bids": [],
        "market_research": None,
        "board": {
            "published": False,
            "opens_at": None,
            "closes_at": None,
            "url_path": "/procurement/board/tender-hv-001",
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
    tender_hv["bids"] = [
        {
            "id": f"bid-{_next('bid')}",
            "vendor_id": invitees[0]["id"],
            "vendor_name": invitees[0]["name"],
            "amount": 185_000,
            "currency": "THB",
            "submitted_at": _now(),
            "channel": "invite",
            "tor_compliant": True,
            "notes": "ครบตาม TOR",
            "score_detail": {},
        },
        {
            "id": f"bid-{_next('bid')}",
            "vendor_id": invitees[1]["id"],
            "vendor_name": invitees[1]["name"],
            "amount": 172_500,
            "currency": "THB",
            "submitted_at": _now(),
            "channel": "invite",
            "tor_compliant": True,
            "notes": "ครบตาม TOR + ส่งเร็วกว่า",
            "score_detail": {},
        },
        {
            "id": f"bid-{_next('bid')}",
            "vendor_id": invitees[2]["id"],
            "vendor_name": invitees[2]["name"],
            "amount": 155_000,
            "currency": "THB",
            "submitted_at": _now(),
            "channel": "invite",
            "tor_compliant": False,
            "notes": "ขาดเอกสารรับรองคุณภาพ",
            "score_detail": {},
        },
    ]

    tender_mid = {
        "id": "tender-mid-001",
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
        "bids": [
            {
                "id": f"bid-{_next('bid')}",
                "vendor_id": invitees[0]["id"],
                "vendor_name": invitees[0]["name"],
                "amount": 42_000,
                "currency": "THB",
                "submitted_at": _now(),
                "channel": "invite",
                "tor_compliant": True,
                "notes": "ครบตาม TOR",
                "score_detail": {},
            },
            {
                "id": f"bid-{_next('bid')}",
                "vendor_id": invitees[1]["id"],
                "vendor_name": invitees[1]["name"],
                "amount": 38_500,
                "currency": "THB",
                "submitted_at": _now(),
                "channel": "invite",
                "tor_compliant": True,
                "notes": "ครบตาม TOR",
                "score_detail": {},
            },
            {
                "id": f"bid-{_next('bid')}",
                "vendor_id": invitees[2]["id"],
                "vendor_name": invitees[2]["name"],
                "amount": 41_200,
                "currency": "THB",
                "submitted_at": _now(),
                "channel": "invite",
                "tor_compliant": True,
                "notes": "ครบตาม TOR",
                "score_detail": {},
            },
        ],
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
            "url_path": "/procurement/board/tender-mid-001",
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

    TENDERS = [tender_hv, tender_mid]
    statuses = [
        "received",
        "quoting",
        "board_open",
        "awaiting_manager_award",
        "award_approved",
        "doc_issued",
        "delivered",
        "awaiting_invoice",
        "ap_posted",
    ]

    # Pad tenders to ≥50 (mix mid/high)
    for i in range(2, n):
        is_mid = i % 2 == 0
        s = skus[i % len(skus)]
        tid = f"tender-{'mid' if is_mid else 'hv'}-{i + 1:03d}"
        budget = (15_000 + (i * 1_700) % 80_000) if is_mid else (120_000 + (i * 9_500) % 800_000)
        base = budget * 0.85
        ven_ids = [VENDOR_REGISTRY[(i + k) % n]["id"] for k in range(3)]
        published = True  # mock board volume for testing
        st = statuses[i % len(statuses)]
        if i < 2:
            published = False
            st = "quoting"
        row = {
            "id": tid,
            "title": f"{'งบกลาง' if is_mid else 'งบสูง'} #{i + 1:02d} — {s['name']}",
            "department": departments[i % len(departments)],
            "pr_id": f"pr-{'mid' if is_mid else 'hv'}-{2000 + i}",
            "tor": {
                "summary": f"จัดหา {s['name']} ตาม TOR หน่วยงาน (ชุดทดสอบ #{i + 1})",
                "specs": [
                    f"SKU: {s.get('sku') or s['id']}",
                    "ตามมาตรฐานคุณภาพ",
                    f"ส่งมอบภายใน {(i % 14) + 3} วัน",
                ],
                "qty": 10 + (i % 40),
                "sku_id": s["id"],
                "sku_name": s["name"],
                "unit": s.get("unit") or "pcs",
            },
            "budget": float(budget),
            "currency": "THB",
            "kind": "hire" if i % 7 == 0 else "goods",
            "threshold": "mid_value" if is_mid else "high_value",
            "status": st,
            "invitees": ven_ids,
            "min_quotes": 3,
            "bids": _three_bids(base, channel="board" if published else "invite"),
            "market_research": (
                {
                    "researched_at": _now(),
                    "sources": [
                        {"site": "shopee.demo", "price": round(base * 0.97, 2), "url": f"https://shopee.demo/{tid}"},
                        {"site": "lazada.demo", "price": round(base * 1.03, 2), "url": f"https://lazada.demo/{tid}"},
                        {"site": "market.demo", "price": round(base, 2), "url": f"https://market.demo/{tid}"},
                    ],
                    "market_median": float(base),
                    "market_min": round(base * 0.97, 2),
                    "market_max": round(base * 1.03, 2),
                    "note_th": "mock ราคากลางออนไลน์",
                }
                if is_mid
                else None
            ),
            "board": {
                "published": published,
                "opens_at": _now() if published else None,
                "closes_at": _now() if published else None,
                "url_path": f"/procurement/board/{tid}",
            },
            "ai_award": None,
            "manager_award_approved": st in ("award_approved", "doc_issued", "delivered", "awaiting_invoice", "ap_posted"),
            "manager_award_by": "procurement_manager" if st in ("award_approved", "doc_issued", "delivered", "awaiting_invoice", "ap_posted") else None,
            "document": (
                {
                    "type": "po" if budget < CONTRACT_THB else "contract",
                    "number": f"{'PO' if budget < CONTRACT_THB else 'CT'}-MOCK-{i + 1:04d}",
                    "amount": round(base, 2),
                    "currency": "THB",
                    "vendor_id": ven_ids[1],
                    "vendor_name": next(v["name"] for v in VENDOR_REGISTRY if v["id"] == ven_ids[1]),
                    "issued_at": _now(),
                    "status": "issued",
                    "note_th": "เอกสาร mock สำหรับทดสอบ",
                }
                if st in ("doc_issued", "delivered", "awaiting_invoice", "ap_posted")
                else None
            ),
            "manager_doc_approved": st in ("doc_issued", "delivered", "awaiting_invoice", "ap_posted"),
            "delivery": (
                {
                    "received_at": _now(),
                    "officer": "receiving_officer",
                    "qty": 10 + (i % 40),
                    "kind": "goods",
                    "manager_approved": True,
                    "stock_posted": True,
                    "note": "mock GRN",
                }
                if st in ("delivered", "awaiting_invoice", "ap_posted")
                else None
            ),
            "accounting_notified": st in ("awaiting_invoice", "ap_posted"),
            "created_at": _now(),
            "updated_at": _now(),
        }
        TENDERS.append(row)

    # Public board cards (≥50)
    PUBLIC_BOARD = []
    for t in TENDERS:
        if t.get("board", {}).get("published") or len(PUBLIC_BOARD) < n:
            PUBLIC_BOARD.append(
                {
                    "tender_id": t["id"],
                    "title": t["title"],
                    "budget": t["budget"],
                    "kind": t["kind"],
                    "opens_at": t["board"].get("opens_at") or _now(),
                    "closes_at": t["board"].get("closes_at") or _now(),
                    "tor_summary": t["tor"]["summary"],
                    "bid_count": len(t["bids"]),
                    "status": t["status"],
                }
            )
        if len(PUBLIC_BOARD) >= n:
            break
    while len(PUBLIC_BOARD) < n:
        k = len(PUBLIC_BOARD) + 1
        PUBLIC_BOARD.append(
            {
                "tender_id": f"tender-board-pad-{k:03d}",
                "title": f"ประกาศบอร์ดทดสอบ #{k:02d}",
                "budget": 50_000 + k * 1000,
                "kind": "goods",
                "opens_at": _now(),
                "closes_at": _now(),
                "tor_summary": f"TOR บอร์ด mock #{k}",
                "bid_count": 3,
                "status": "board_open",
            }
        )

    # Petty cash purchases (≥50)
    purchases: list[dict[str, Any]] = []
    for i in range(n):
        amt = 1_000 + (i * 173) % 9_000
        pid = f"petty-{101 + i}"
        status = "pending_clearance" if i < 8 else "cleared"
        purchases.append(
            {
                "id": pid,
                "pr_id": f"pr-petty-{1001 + i}",
                "title": f"ซื้อวัสดุด่วน #{i + 1:02d}",
                "department": departments[i % len(departments)],
                "tor_summary": f"TOR เงินสดยืม รายการ #{i + 1}",
                "amount": float(amt),
                "receipt_no": f"RC-{8801 + i}",
                "vendor_name": VENDOR_REGISTRY[i % n]["name"] if i % 3 else f"ร้านเงินสด #{i + 1}",
                "purchased_at": _now(),
                "status": status,
                "cleared_batch_id": f"clear-{(i // 2) + 1:03d}" if status == "cleared" else None,
                "scan_complete": True,
            }
        )
    # Keep walkthrough titles on first two
    purchases[0]["title"] = "ซื้อวัสดุสำนักงานด่วน"
    purchases[0]["amount"] = 3_200.0
    purchases[0]["receipt_no"] = "RC-8801"
    purchases[0]["status"] = "pending_clearance"
    purchases[0]["cleared_batch_id"] = None
    purchases[1]["title"] = "ซื้อแบตเตอรี่สำรอง"
    purchases[1]["amount"] = 5_300.0
    purchases[1]["receipt_no"] = "RC-8802"
    purchases[1]["status"] = "pending_clearance"
    purchases[1]["cleared_batch_id"] = None

    clearance_batches = []
    for i in range(n):
        clearance_batches.append(
            {
                "id": f"clear-{i + 1:03d}",
                "submitted_at": _now(),
                "purchase_ids": [f"petty-{101 + ((i * 2) % n)}", f"petty-{101 + ((i * 2 + 1) % n)}"],
                "receipt_nos": [f"RC-{8801 + ((i * 2) % n)}", f"RC-{8801 + ((i * 2 + 1) % n)}"],
                "amount": float(2_000 + i * 110),
                "currency": "THB",
                "status": "sent_to_accounting" if i % 4 else "closed",
                "note_th": f"เคลียร์เงินสดยืมชุดที่ {i + 1} (mock)",
                "accounting_ref": f"ADV-CLR-{i + 1:03d}",
                "physical_followup_pending": i % 3 == 0,
            }
        )

    month_reconciles = []
    for i in range(n):
        y = 2022 + (i // 12)
        m = (i % 12) + 1
        month_reconciles.append(
            {
                "id": f"recon-{i + 1:03d}",
                "month": f"{y}-{m:02d}",
                "reconciled_at": _now(),
                "float_thb": PETTY_FLOAT_THB,
                "balance_thb": PETTY_FLOAT_THB - (i * 500) % 20_000,
                "spent_thb": float((i * 500) % 20_000),
                "expected_balance_thb": PETTY_FLOAT_THB - (i * 500) % 20_000,
                "purchase_count": 2 + (i % 10),
                "cleared_count": 2 + (i % 10),
                "pending_count": 0 if i % 5 else 1,
                "balanced": i % 5 != 0,
                "note_th": f"กระทบยอด mock เดือน {y}-{m:02d}",
                "status": "balanced" if i % 5 else "variance",
            }
        )

    PETTY_CASH = {
        "float_thb": PETTY_FLOAT_THB,
        "balance_thb": PETTY_FLOAT_THB - 8_500,
        "per_bill_max_thb": PETTY_MAX_THB,
        "currency": "THB",
        "purchases": purchases,
        "clearance_batches": clearance_batches,
        "month_reconciles": month_reconciles,
    }

    # Vendor invoices (≥50)
    VENDOR_INVOICES = []
    for i in range(n):
        t = TENDERS[i % len(TENDERS)]
        winner = (t.get("bids") or [{}])[1 if len(t.get("bids") or []) > 1 else 0]
        amount = float(winner.get("amount") or t.get("budget") or 10_000)
        VENDOR_INVOICES.append(
            {
                "id": f"vinv-{101 + i}",
                "tender_id": t["id"],
                "vendor_id": winner.get("vendor_id"),
                "vendor_name": winner.get("vendor_name") or VENDOR_REGISTRY[i % n]["name"],
                "number": f"INV-V-{1001 + i}",
                "amount": amount,
                "currency": "THB",
                "submitted_at": _now(),
                "status": ["pending_procurement_check", "sent_to_accounting", "rejected"][i % 3],
                "ap_posted": i % 3 == 1,
                "ap_ref": f"AP-INV-V-{1001 + i}" if i % 3 == 1 else None,
                "scan_complete": True,
                "physical_original_pending": i % 2 == 0,
            }
        )

    # Accounting alerts (≥50)
    ACCOUNTING_ALERTS = []
    for i in range(n):
        kind = ["delivery", "petty_clearance", "physical_original"][i % 3]
        ACCOUNTING_ALERTS.append(
            {
                "id": f"acct-alert-{101 + i}",
                "tender_id": TENDERS[i % len(TENDERS)]["id"] if kind != "petty_clearance" else None,
                "petty_clearance_id": f"clear-{(i % n) + 1:03d}" if kind == "petty_clearance" else None,
                "proc_doc_id": f"pdoc-{101 + i}" if kind == "physical_original" else None,
                "title": [
                    f"แจ้งส่งมอบ #{i + 1}",
                    f"เคลียร์เงินสดยืม #{i + 1}",
                    f"รอตัวจริงเอกสาร #{i + 1}",
                ][i % 3],
                "amount": float(5_000 + i * 1200),
                "vendor_name": VENDOR_REGISTRY[i % n]["name"],
                "message_th": f"ข้อความแจ้งเตือนบัญชี mock รายการที่ {i + 1}",
                "created_at": _now(),
                "status": "open" if i % 4 else "closed",
                "kind": kind,
            }
        )

    # Scanned documents (≥50 of each major type: pr, tor, receipt, tax_invoice, quote, po)
    seed_rows: list[tuple[str, str, str, str, bool]] = []
    doc_types_cycle = [
        ("pr", False),
        ("tor", False),
        ("receipt", True),
        ("tax_invoice", True),
        ("quote", False),
        ("po", False),
        ("vendor_invoice", False),
        ("delivery", False),
        ("contract", True),
        ("important", True),
    ]
    # Anchor walkthrough docs
    seed_rows.extend(
        [
            ("petty", "petty-101", "pr", "PR-petty-101.pdf", False),
            ("petty", "petty-101", "tor", "TOR-petty-101.pdf", False),
            ("petty", "petty-101", "receipt", "RC-8801.pdf", True),
            ("petty", "petty-102", "pr", "PR-petty-102.pdf", False),
            ("petty", "petty-102", "tor", "TOR-petty-102.pdf", False),
            ("petty", "petty-102", "receipt", "RC-8802.pdf", True),
            ("tender", "tender-mid-001", "pr", "PR-mid-1001.pdf", False),
            ("tender", "tender-mid-001", "tor", "TOR-mid-1001.pdf", False),
            ("tender", "tender-hv-001", "pr", "PR-hv-1001.pdf", False),
            ("tender", "tender-hv-001", "tor", "TOR-hv-1001.pdf", False),
        ]
    )
    # ≥50 per doc type
    for doc_type, physical in doc_types_cycle:
        for i in range(n):
            case_kind = "petty" if doc_type == "receipt" or i % 5 == 0 else "tender"
            case_id = (
                f"petty-{101 + (i % n)}"
                if case_kind == "petty"
                else TENDERS[i % len(TENDERS)]["id"]
            )
            seed_rows.append(
                (
                    case_kind,
                    case_id,
                    doc_type,
                    f"{doc_type.upper()}-mock-{i + 1:03d}.pdf",
                    physical,
                )
            )
    _seed_scan_docs(seed_rows)

    _seq.update(
        {
            "ven": 200,
            "tender": 200,
            "bid": 2000,
            "inv": 200,
            "alert": 200,
            "petty": 200,
            "clear": 200,
            "recon": 200,
            "doc": 5000,
        }
    )


def _seed_scan_docs(rows: list[tuple[str, str, str, str, bool]]) -> None:
    for case_kind, case_id, doc_type, filename, physical in rows:
        needs_physical = physical or doc_type in PHYSICAL_FOLLOWUP_DOC_TYPES
        PROC_DOCUMENTS.append(
            {
                "id": f"pdoc-{_next('doc')}",
                "scan_id": f"scan-proc-{_next('doc')}",
                "case_kind": case_kind,
                "case_id": case_id,
                "doc_type": doc_type,
                "doc_type_th": DOC_TYPE_LABELS_TH.get(doc_type, doc_type),
                "filename": filename,
                "scanned_at": _now(),
                "source": "upload",
                "status": "scanned",
                "requires_physical_original": needs_physical,
                "physical_status": "pending_send" if needs_physical else "not_required",
                "physical_sent_at": None,
                "physical_received_at": None,
                "note_th": (
                    "สแกนเข้าระบบแล้ว — ส่งตัวจริงให้บัญชีภายหลังเพื่อยื่นภาษี"
                    if needs_physical
                    else "สแกนเข้าระบบแล้ว ใช้ทำธุรกรรมบนระบบ"
                ),
            }
        )


def thresholds() -> dict[str, Any]:
    return {
        "petty_max_thb": PETTY_MAX_THB,
        "petty_float_thb": PETTY_FLOAT_THB,
        "high_value_thb": HIGH_VALUE_THB,
        "contract_thb": CONTRACT_THB,
        "min_quotes": 3,
        "mock_set_size": MOCK_SET_SIZE,
        "scan_first": True,
        "scan_policy_th": (
            "ทุกกรณีต้องสแกนเอกสารเข้าสู่ระบบก่อนทำรายการ "
            "ใบเสร็จ / ใบกำกับภาษี / เอกสารสำคัญบางอย่าง "
            "อาจส่งตัวจริงให้บัญชีภายหลังเพื่อยื่นภาษี"
        ),
        "physical_followup_doc_types": sorted(PHYSICAL_FOLLOWUP_DOC_TYPES),
        "bands": [
            {
                "id": "petty",
                "th": "≤ 10,000 — เงินสดยืมถือ (float 50,000 / บิลไม่เกิน 10,000)",
                "steps": [
                    {"n": 0, "id": "scan", "th": "สแกน PR+TOR+ใบเสร็จเข้าระบบ"},
                    {"n": 1, "id": "pr_tor", "th": "รับ PR + TOR จากหน่วยงาน"},
                    {"n": 2, "id": "buy_cash", "th": "ซื้อด้วยเงินสดยืม (≤10,000/บิล)"},
                    {"n": 3, "id": "collect_receipts", "th": "รวบรวมบิล/ใบเสร็จ ส่งบัญชีเคลียร์ยอดยืม"},
                    {"n": 4, "id": "month_reconcile", "th": "กระทบยอดค่าใช้จ่ายทุกสิ้นเดือน"},
                    {
                        "n": 5,
                        "id": "physical_followup",
                        "th": "ส่งตัวจริงใบเสร็จ/ใบกำกับให้บัญชีภายหลัง (ยื่นภาษี)",
                    },
                ],
            },
            {
                "id": "mid_value",
                "th": "> 10,000 และ ≤ 100,000",
                "steps": [
                    {"n": 0, "id": "scan", "th": "สแกนเอกสารทุกขั้นเข้าระบบ"},
                    {"n": 1, "id": "pr_tor", "th": "ได้ PR + TOR"},
                    {"n": 2, "id": "market_research", "th": "ค้นหาราคาตลาดออนไลน์ (ราคากลาง)"},
                    {
                        "n": 3,
                        "id": "quotes_or_board",
                        "th": "ขอราคา ≥3 รายที่ลงทะเบียน หรือเปิด bidding สาธารณะถ้ามีเวลา",
                    },
                    {"n": 4, "id": "same_as_high", "th": "จากนั้นทำตามขั้นตอนเหมือนงบ >100,000"},
                    {
                        "n": 5,
                        "id": "physical_followup",
                        "th": "ส่งตัวจริงใบเสร็จ/ใบกำกับให้บัญชีภายหลัง",
                    },
                ],
            },
            {
                "id": "high_value",
                "th": "> 100,000",
                "steps": [
                    {"n": 0, "id": "scan", "th": "สแกนเอกสารทุกขั้นเข้าระบบ"},
                    {"n": 0, "id": "vendor_register", "th": "ผู้ประกอบการลงทะเบียน"},
                    {"n": 1, "id": "pr_tor", "th": "รับใบ PR + TOR"},
                    {"n": 2, "id": "invite_quotes", "th": "เชิญเสนอราคา ≥ 3 ราย"},
                    {"n": 3, "id": "public_board", "th": "ประกาศบอร์ดสาธารณะ"},
                    {"n": 4, "id": "ai_award", "th": "AI พิจารณา + ผู้จัดการอนุมัติ"},
                    {"n": 5, "id": "issue_doc", "th": "ออก PO / สัญญา"},
                    {"n": 6, "id": "delivery", "th": "ส่งมอบ + ตรวจรับ"},
                    {"n": 7, "id": "accounting_notify", "th": "แจ้งบัญชี"},
                    {"n": 8, "id": "vendor_invoice", "th": "ใบแจ้งหนี้ → ตั้งเจ้าหนี้"},
                    {
                        "n": 9,
                        "id": "physical_followup",
                        "th": "ส่งตัวจริงใบเสร็จ/ใบกำกับภาษีให้บัญชีภายหลัง",
                    },
                ],
            },
        ],
        "steps": [
            {"n": 0, "id": "scan", "th": "สแกนเอกสารเข้าระบบก่อนทุกกรณี"},
            {"n": 0, "id": "vendor_register", "th": "ผู้ประกอบการลงทะเบียน"},
            {"n": 1, "id": "pr_tor", "th": "รับใบ PR + TOR"},
            {"n": 2, "id": "invite_quotes", "th": "เชิญเสนอราคา ≥ 3 ราย"},
            {"n": 3, "id": "public_board", "th": "ประกาศบอร์ดสาธารณะ"},
            {"n": 4, "id": "ai_award", "th": "AI พิจารณา + ผู้จัดการอนุมัติ"},
            {"n": 5, "id": "issue_doc", "th": "ออก PO / สัญญา"},
            {"n": 6, "id": "delivery", "th": "ส่งมอบ + ตรวจรับ"},
            {"n": 7, "id": "accounting_notify", "th": "แจ้งบัญชี"},
            {"n": 8, "id": "vendor_invoice", "th": "ใบแจ้งหนี้ → ตั้งเจ้าหนี้"},
            {
                "n": 9,
                "id": "physical_followup",
                "th": "ส่งตัวจริงเอกสารภาษีให้บัญชีตามหลัง",
            },
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
    # Scan-first: attach PR + TOR scans (demo auto if not provided)
    docs_in = body.get("documents") or []
    if not docs_in and body.get("auto_scan", True):
        docs_in = [
            {"doc_type": "pr", "filename": f"{row['pr_id']}.pdf"},
            {"doc_type": "tor", "filename": f"TOR-{row['pr_id']}.pdf"},
        ]
    for d in docs_in:
        register_document(
            {
                "case_kind": "tender",
                "case_id": tid,
                "doc_type": d.get("doc_type"),
                "filename": d.get("filename"),
                "scan_id": d.get("scan_id"),
                "source": d.get("source") or "upload",
            }
        )
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
    if PUBLIC_BOARD:
        return deepcopy(PUBLIC_BOARD)
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
    # Scan-first: PR + TOR must be in the system
    ensure_scanned(tender_id, ["pr", "tor"])
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
    # Scan issued PO/contract into system
    register_document(
        {
            "case_kind": "tender",
            "case_id": tender_id,
            "doc_type": "contract" if doc["type"] == "contract" else "po",
            "filename": f"{doc['number']}.pdf",
            "amount": amount,
            "source": "system",
            "requires_physical_original": doc["type"] == "contract",
            "note_th": (
                "สแกน/ออกเอกสารในระบบ — สัญญาตัวจริงอาจส่งบัญชีภายหลัง"
                if doc["type"] == "contract"
                else "ออก PO ในระบบจากเอกสารสแกน"
            ),
        }
    )
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
    # Scan tax invoice / receipt into system (physical may follow later)
    docs_in = body.get("documents") or []
    if not docs_in and body.get("auto_scan", True):
        docs_in = [
            {
                "doc_type": "tax_invoice",
                "filename": f"TAX-{tender_id}.pdf",
                "amount": amount,
            },
            {
                "doc_type": "vendor_invoice",
                "filename": f"INV-{tender_id}.pdf",
                "amount": amount,
            },
        ]
    for d in docs_in:
        register_document(
            {
                "case_kind": "tender",
                "case_id": tender_id,
                "doc_type": d.get("doc_type"),
                "filename": d.get("filename"),
                "scan_id": d.get("scan_id"),
                "amount": d.get("amount") or amount,
                "source": d.get("source") or "upload",
            }
        )
    # Need at least tax_invoice or receipt scanned for AP path
    have = {d["doc_type"] for d in _docs_for(tender_id) if d.get("status") == "scanned"}
    if "tax_invoice" not in have and "receipt" not in have:
        raise ValueError("scan_required:ใบกำกับภาษีหรือใบเสร็จ")
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
        "scan_complete": True,
        "physical_original_pending": True,
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

    have = {d["doc_type"] for d in _docs_for(inv["tender_id"]) if d.get("status") == "scanned"}
    if "tax_invoice" not in have and "receipt" not in have:
        raise ValueError("scan_required:ใบกำกับภาษีหรือใบเสร็จ")

    inv["status"] = "sent_to_accounting"
    inv["ap_posted"] = True
    inv["ap_ref"] = f"AP-{inv['number']}"
    inv["verified_at"] = _now()
    inv["physical_followup_note_th"] = (
        "ตั้งเจ้าหนี้จากเอกสารสแกนในระบบแล้ว — "
        "ตัวจริงใบกำกับภาษี/ใบเสร็จส่งให้บัญชีตามหลังเพื่อยื่นภาษี"
    )
    t["status"] = "ap_posted"
    _touch(t)
    # Close matching accounting alert
    for a in ACCOUNTING_ALERTS:
        if a["tender_id"] == t["id"] and a["status"] == "open" and a.get("kind") != "physical_original":
            a["status"] = "closed"
    return deepcopy(inv)


def list_vendor_invoices() -> list[dict[str, Any]]:
    return deepcopy(VENDOR_INVOICES)


def list_proc_documents(
    case_id: str | None = None,
    pending_physical: bool = False,
) -> list[dict[str, Any]]:
    rows = PROC_DOCUMENTS
    if case_id:
        rows = [d for d in rows if d.get("case_id") == case_id]
    if pending_physical:
        rows = [
            d
            for d in rows
            if d.get("requires_physical_original")
            and d.get("physical_status") in ("pending_send", "sent_to_accounting")
        ]
    return deepcopy(rows)


def _docs_for(case_id: str) -> list[dict[str, Any]]:
    return [d for d in PROC_DOCUMENTS if d.get("case_id") == case_id]


def ensure_scanned(case_id: str, required_types: list[str]) -> None:
    have = {
        d["doc_type"]
        for d in _docs_for(case_id)
        if d.get("status") == "scanned"
    }
    missing = [t for t in required_types if t not in have]
    if missing:
        labels = [DOC_TYPE_LABELS_TH.get(t, t) for t in missing]
        raise ValueError("scan_required:" + ",".join(labels))


def register_document(body: dict[str, Any]) -> dict[str, Any]:
    """Scan/register a document into the system (required before process steps)."""
    case_kind = str(body.get("case_kind") or "tender").strip()
    if case_kind not in ("tender", "petty"):
        case_kind = "tender"
    case_id = str(body.get("case_id") or "").strip()
    if not case_id:
        raise ValueError("case_id_required")
    doc_type = str(body.get("doc_type") or "other").strip()
    if doc_type not in DOC_TYPE_LABELS_TH:
        doc_type = "other"
    filename = str(body.get("filename") or f"{doc_type}-{case_id}.pdf").strip()
    needs_physical = bool(
        body.get("requires_physical_original")
        if body.get("requires_physical_original") is not None
        else doc_type in PHYSICAL_FOLLOWUP_DOC_TYPES
    )
    # Replace prior scan of same type for this case
    PROC_DOCUMENTS[:] = [
        d
        for d in PROC_DOCUMENTS
        if not (d.get("case_id") == case_id and d.get("doc_type") == doc_type)
    ]
    row = {
        "id": f"pdoc-{_next('doc')}",
        "scan_id": str(body.get("scan_id") or f"scan-proc-{_next('doc')}"),
        "case_kind": case_kind,
        "case_id": case_id,
        "doc_type": doc_type,
        "doc_type_th": DOC_TYPE_LABELS_TH.get(doc_type, doc_type),
        "filename": filename,
        "scanned_at": _now(),
        "source": str(body.get("source") or "upload"),
        "status": "scanned",
        "amount": float(body.get("amount") or 0) or None,
        "requires_physical_original": needs_physical,
        "physical_status": "pending_send" if needs_physical else "not_required",
        "physical_sent_at": None,
        "physical_received_at": None,
        "note_th": str(
            body.get("note_th")
            or (
                "สแกนเข้าระบบแล้ว — ส่งตัวจริงให้บัญชีภายหลังเพื่อยื่นภาษี"
                if needs_physical
                else "สแกนเข้าระบบแล้ว ใช้ทำธุรกรรมบนระบบ"
            )
        ),
    }
    PROC_DOCUMENTS.insert(0, row)
    return deepcopy(row)


def mark_physical_sent(doc_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Send physical original to accounting later (tax filing)."""
    body = body or {}
    doc = next((d for d in PROC_DOCUMENTS if d["id"] == doc_id), None)
    if not doc:
        raise ValueError("document_not_found")
    if not doc.get("requires_physical_original"):
        raise ValueError("physical_original_not_required")
    doc["physical_status"] = "sent_to_accounting"
    doc["physical_sent_at"] = _now()
    doc["courier_note"] = str(body.get("note") or body.get("courier_note") or "ส่งตัวจริงตามหลัง")
    ACCOUNTING_ALERTS.insert(
        0,
        {
            "id": f"acct-alert-{_next('alert')}",
            "tender_id": doc["case_id"] if doc["case_kind"] == "tender" else None,
            "petty_case_id": doc["case_id"] if doc["case_kind"] == "petty" else None,
            "proc_doc_id": doc["id"],
            "title": f"รับตัวจริง {doc['doc_type_th']}",
            "amount": doc.get("amount"),
            "vendor_name": None,
            "message_th": (
                f"จัดซื้อส่งตัวจริง{doc['doc_type_th']} ({doc['filename']}) "
                "เพื่อใช้ยื่นภาษี — รอฝ่ายบัญชียืนยันรับ"
            ),
            "created_at": _now(),
            "status": "open",
            "kind": "physical_original",
        },
    )
    return deepcopy(doc)


def mark_physical_received(doc_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    body = body or {}
    doc = next((d for d in PROC_DOCUMENTS if d["id"] == doc_id), None)
    if not doc:
        raise ValueError("document_not_found")
    if doc.get("physical_status") not in ("sent_to_accounting", "pending_send"):
        raise ValueError("nothing_to_receive")
    doc["physical_status"] = "received_by_accounting"
    doc["physical_received_at"] = _now()
    doc["received_by"] = str(body.get("received_by") or "accounting")
    for a in ACCOUNTING_ALERTS:
        if a.get("proc_doc_id") == doc_id and a.get("status") == "open":
            a["status"] = "closed"
    return deepcopy(doc)


def documents_summary() -> dict[str, Any]:
    pending = [
        d
        for d in PROC_DOCUMENTS
        if d.get("requires_physical_original")
        and d.get("physical_status") == "pending_send"
    ]
    in_transit = [
        d
        for d in PROC_DOCUMENTS
        if d.get("physical_status") == "sent_to_accounting"
    ]
    by_type: dict[str, int] = {}
    for d in PROC_DOCUMENTS:
        by_type[d["doc_type"]] = by_type.get(d["doc_type"], 0) + 1
    return {
        "scan_first": True,
        "policy_th": thresholds()["scan_policy_th"],
        "total_scanned": len(PROC_DOCUMENTS),
        "counts_by_type": by_type,
        "pending_physical_send": len(pending),
        "in_transit_to_accounting": len(in_transit),
        "items": deepcopy(PROC_DOCUMENTS),
        "pending_physical_items": deepcopy(pending),
        "in_transit_items": deepcopy(in_transit),
    }


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
    """Buy with petty cash: scanned PR+TOR+receipt required, each bill ≤ 10,000."""
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
        "scan_complete": False,
    }
    # Scan-first: register uploaded scans (or auto-mock for demo button flow)
    docs_in = body.get("documents") or []
    if not docs_in and body.get("auto_scan", True):
        docs_in = [
            {"doc_type": "pr", "filename": f"{pr_id}.pdf"},
            {"doc_type": "tor", "filename": f"TOR-{pr_id}.pdf"},
            {
                "doc_type": "receipt",
                "filename": f"{row['receipt_no']}.pdf",
                "amount": amount,
            },
        ]
    for d in docs_in:
        register_document(
            {
                "case_kind": "petty",
                "case_id": row["id"],
                "doc_type": d.get("doc_type"),
                "filename": d.get("filename"),
                "scan_id": d.get("scan_id"),
                "amount": d.get("amount") or amount,
                "source": d.get("source") or "upload",
            }
        )
    ensure_scanned(row["id"], ["pr", "tor", "receipt"])
    row["scan_complete"] = True
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
    for p in pending:
        ensure_scanned(p["id"], ["pr", "tor", "receipt"])
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
            or "รวบรวมบิล/ใบเสร็จ (สแกนในระบบแล้ว) ส่งบัญชีเพื่อเคลียร์ยอดเงินยืม — ตัวจริงใบเสร็จส่งตามหลัง"
        ),
        "accounting_ref": f"ADV-CLR-{_next('clear')}",
        "physical_followup_pending": True,
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
                f"รวม {total:,.0f} THB เพื่อเคลียร์ยอดเงินยืม "
                "(สแกนในระบบแล้ว — ตัวจริงส่งตามหลังเพื่อยื่นภาษี)"
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
