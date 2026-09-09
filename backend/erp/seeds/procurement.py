"""Procurement PR / PO with actionable pending + partial receive."""

from __future__ import annotations

from typing import Any


def build_procurement(vendors: list[dict], skus: list[dict]) -> dict[str, Any]:
    prs = []
    for i in range(50):
        status = (
            "pending" if i < 8 else "rejected" if i == 8 else "approved"
        )
        ven = vendors[i % len(vendors)]
        sku = skus[i % len(skus)]
        prs.append(
            {
                "id": f"pr-{1001 + i}",
                "title": f"PR {sku['name']} — {ven['name']}",
                "status": status,
                "vendor": ven["name"],
                "vendor_id": ven["id"],
                "sku_id": sku["id"],
                "qty": 20 + i * 2,
                "total": (20 + i * 2) * sku["cost"],
                "currency": "THB",
            }
        )

    pos = []
    for i in range(50):
        status = "partial" if i < 5 else "pending" if i < 10 else "received"
        ven = vendors[(i + 2) % len(vendors)]
        sku = skus[(i + 5) % len(skus)]
        qty = 30 + i * 5
        received = qty if status == "received" else (qty // 2 if status == "partial" else 0)
        pos.append(
            {
                "id": f"po-{2001 + i}",
                "number": f"PO-2026-{i + 1:03d}",
                "status": status,
                "vendor": ven["name"],
                "vendor_id": ven["id"],
                "sku_id": sku["id"],
                "qty": qty,
                "qty_received": received,
                "total": qty * sku["cost"],
                "currency": "THB",
            }
        )

    inbox = []
    for i, pr in enumerate(prs):
        if pr["status"] != "pending":
            continue
        inbox.append(
            {
                "id": f"wf-{i + 1:02d}",
                "title": pr["title"],
                "type": "purchase_request",
                "status": "pending",
                "resource_type": "pr",
                "resource_id": pr["id"],
                "amount": pr["total"],
            }
        )
    # Pad workflow inbox to 50 generic approval items for demo volume.
    while len(inbox) < 50:
        n = len(inbox) + 1
        inbox.append(
            {
                "id": f"wf-{n:02d}",
                "title": f"Generic approval request #{n}",
                "type": "generic",
                "status": "pending" if n % 3 else "approved",
                "resource_type": "document",
                "resource_id": f"doc-{n:02d}",
                "amount": 1000 + n * 50,
            }
        )

    # One high-value PR (>100k) that feeds the tender workflow UI.
    hv_sku = skus[5] if len(skus) > 5 else skus[0]
    hv_ven = vendors[0]
    prs.insert(
        0,
        {
            "id": "pr-hv-1001",
            "title": f"PR สูงบ — {hv_sku['name']} (TOR แนบ)",
            "status": "pending",
            "vendor": hv_ven["name"],
            "vendor_id": hv_ven["id"],
            "sku_id": hv_sku["id"],
            "qty": 500,
            "total": 220_000,
            "currency": "THB",
            "budget": 220_000,
            "band": "high_value",
            "high_value": True,
            "has_tor": True,
        },
    )
    mid_sku = skus[2] if len(skus) > 2 else hv_sku
    prs.insert(
        0,
        {
            "id": "pr-mid-1001",
            "title": f"PR งบกลาง — {mid_sku['name']} (TOR แนบ)",
            "status": "pending",
            "vendor": "",
            "vendor_id": None,
            "sku_id": mid_sku["id"],
            "qty": 40,
            "total": 45_000,
            "currency": "THB",
            "budget": 45_000,
            "band": "mid_value",
            "mid_value": True,
            "has_tor": True,
        },
    )
    prs.insert(
        0,
        {
            "id": "pr-petty-1001",
            "title": "PR เงินสดยืม — วัสดุสำนักงานด่วน",
            "status": "approved",
            "vendor": "ร้านอุปกรณ์ใกล้เคียง",
            "vendor_id": None,
            "sku_id": None,
            "qty": 1,
            "total": 3_200,
            "currency": "THB",
            "budget": 3_200,
            "band": "petty",
            "petty": True,
            "has_tor": True,
        },
    )

    # ≥50 mock PRs per budget band for testing
    for i in range(50):
        sku = skus[i % len(skus)]
        ven = vendors[i % len(vendors)]
        prs.append(
            {
                "id": f"pr-petty-mock-{i + 1:03d}",
                "title": f"PR เงินสดยืม mock #{i + 1:02d} — {sku['name']}",
                "status": "approved" if i % 3 else "pending",
                "vendor": ven["name"] if i % 2 else "ร้านเงินสด",
                "vendor_id": ven["id"] if i % 2 else None,
                "sku_id": sku["id"],
                "qty": 1 + (i % 5),
                "total": 1_000 + (i * 170) % 9_000,
                "currency": "THB",
                "budget": 1_000 + (i * 170) % 9_000,
                "band": "petty",
                "petty": True,
                "has_tor": True,
            }
        )
        prs.append(
            {
                "id": f"pr-mid-mock-{i + 1:03d}",
                "title": f"PR งบกลาง mock #{i + 1:02d} — {sku['name']}",
                "status": "pending" if i % 4 else "approved",
                "vendor": "",
                "vendor_id": None,
                "sku_id": sku["id"],
                "qty": 5 + (i % 20),
                "total": 12_000 + (i * 1_500) % 80_000,
                "currency": "THB",
                "budget": 12_000 + (i * 1_500) % 80_000,
                "band": "mid_value",
                "mid_value": True,
                "has_tor": True,
            }
        )
        prs.append(
            {
                "id": f"pr-hv-mock-{i + 1:03d}",
                "title": f"PR งบสูง mock #{i + 1:02d} — {sku['name']}",
                "status": "pending" if i % 5 else "approved",
                "vendor": ven["name"],
                "vendor_id": ven["id"],
                "sku_id": sku["id"],
                "qty": 20 + i,
                "total": 120_000 + (i * 8_000) % 900_000,
                "currency": "THB",
                "budget": 120_000 + (i * 8_000) % 900_000,
                "band": "high_value",
                "high_value": True,
                "has_tor": True,
            }
        )

    return {
        "PROCUREMENT_PRS": prs,
        "PURCHASE_ORDERS": pos,
        "WORKFLOW_INBOX": inbox,
    }
