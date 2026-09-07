"""Procurement PR / PO with actionable pending + partial receive."""

from __future__ import annotations

from typing import Any


def build_procurement(vendors: list[dict], skus: list[dict]) -> dict[str, Any]:
    prs = []
    statuses = (
        ["approved"] * 6
        + ["pending"] * 3
        + ["rejected"]
    )
    for i, status in enumerate(statuses):
        ven = vendors[i % len(vendors)]
        sku = skus[i % len(skus)]
        prs.append(
            {
                "id": f"pr-{1001 + i}",
                "title": f"ขอซื้อ {sku['name']} — {ven['name']}",
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
    po_states = (
        ["received"] * 4
        + ["partial"] * 2
        + ["pending"]
    )
    for i, status in enumerate(po_states):
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
                "qty_ordered": qty,
                "qty_received": received,
                "total": qty * sku["cost"],
                "currency": "THB",
            }
        )

    inbox_items = [
        {"id": f"wf-{pr['id']}", "title": f"อนุมัติ {pr['id']}: {pr['title']}", "status": "pending"}
        for pr in prs
        if pr["status"] == "pending"
    ]
    workflow_inbox = {"count": len(inbox_items), "items": inbox_items}

    return {
        "PROCUREMENT_PRS": prs,
        "PURCHASE_ORDERS": pos,
        "WORKFLOW_INBOX": workflow_inbox,
    }
