"""Warehouses, lots, movements, stock alerts."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def build_stock(skus: list[dict], branches: list[dict]) -> dict[str, Any]:
    warehouses = [
        {
            "id": "wh-hq",
            "name": "HQ Warehouse Silom",
            "code": "WH-HQ",
            "branch_id": "branch-hq",
        },
        {
            "id": "wh-ask",
            "name": "Asok Branch Warehouse",
            "code": "WH-ASK",
            "branch_id": "branch-asok",
        },
        {
            "id": "wh-cold",
            "name": "Cold Storage Bangna",
            "code": "WH-COLD",
            "branch_id": "branch-hq",
        },
    ]
    today = date(2026, 9, 7)
    lots = []
    movements = []
    for i, sku in enumerate(skus):
        if not sku.get("lot_tracked"):
            continue
        exp = today + timedelta(days=60 + i * 3)
        lots.append(
            {
                "id": f"lot-{i + 1:02d}",
                "sku_id": sku["id"],
                "lot_code": f"L{today.year}{i + 1:03d}",
                "qty": max(sku["qty_on_hand"], 1),
                "expiry_date": exp.isoformat(),
                "warehouse_id": warehouses[i % len(warehouses)]["id"],
            }
        )
    for d in range(50):
        day = today - timedelta(days=d)
        sku = skus[d % len(skus)]
        movements.append(
            {
                "id": f"mov-{d + 1:03d}",
                "date": day.isoformat(),
                "sku_id": sku["id"],
                "type": ["in", "out", "adjust"][d % 3],
                "qty": 2 + (d % 9),
                "warehouse_id": warehouses[d % len(warehouses)]["id"],
                "note": "synth movement",
            }
        )

    low = [s for s in skus if 0 < s["qty_on_hand"] <= s["reorder_point"]]
    out = [s for s in skus if s["qty_on_hand"] <= 0]
    alerts = {
        "low_stock": [{"sku_id": s["id"], "sku": s["sku"], "qty": s["qty_on_hand"]} for s in low[:5]],
        "out_of_stock": [{"sku_id": s["id"], "sku": s["sku"]} for s in out[:2]],
    }
    return {
        "WAREHOUSES": warehouses,
        "LOTS": lots,
        "STOCK_MOVEMENTS": movements,
        "STOCK_ALERTS": alerts,
    }
