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

    return {
        "PROCUREMENT_PRS": prs,
        "PURCHASE_ORDERS": pos,
        "WORKFLOW_INBOX": inbox,
    }
