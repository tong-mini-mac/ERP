"""Build ThaiTrade synthetic namespace for ERP-Demo."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from erp.seeds.catalog import build_catalog
from erp.seeds.finance import build_finance
from erp.seeds.hr import build_hr
from erp.seeds.master import build_master
from erp.seeds.people import build_people
from erp.seeds.procurement import build_procurement
from erp.seeds.scenarios import build_scenarios
from erp.seeds.stock import build_stock

# Keep resto/marketing stubs so older UI routes still resolve.
_LEGACY = {
    "MENUS": [
        {
            "id": "menu-1",
            "name": "เมนูทดสอบร้านอาหาร (ThaiTrade cafe corner)",
            "items": [
                {"id": "mi-1", "name": "ข้าวผัดกุ้ง", "price": 89},
                {"id": "mi-2", "name": "ต้มยำกุ้ง", "price": 129},
            ],
        }
    ],
    "INGREDIENTS": [
        {"id": "ing-1", "name": "ข้าวสวย", "unit": "kg", "on_hand": 40},
        {"id": "ing-2", "name": "กุ้ง", "unit": "kg", "on_hand": 8},
    ],
    "CAMPAIGNS_PRE": [
        {
            "id": "camp-1",
            "name": "โปรเปิดสาขาอโศก",
            "status": "draft",
            "channel": "facebook",
        }
    ],
    "CAMPAIGNS_POST": [
        {
            "id": "camp-2",
            "name": "รีวิวหลังส่งของ",
            "status": "scheduled",
            "channel": "line",
        }
    ],
    "ONBOARDING": {
        "completed": True,
        "items": [
            {"key": "shop", "label": "ตั้งค่าบริษัท ThaiTrade", "done": True},
            {"key": "sku", "label": "โหลด 50 SKU จำลอง", "done": True},
            {"key": "warehouse", "label": "คลัง HQ + Asok", "done": True},
            {"key": "finance", "label": "ใบแจ้งหนี้ + overdue scenarios", "done": True},
        ],
    },
}


def build_all() -> dict[str, Any]:
    master = build_master()
    people = build_people()
    catalog = build_catalog()
    stock = build_stock(catalog["SKUS"], master["BRANCHES"])
    finance = build_finance(catalog["CUSTOMERS"])
    procurement = build_procurement(catalog["VENDORS"], catalog["SKUS"])
    hr = build_hr(people["EMPLOYEES"])
    scenarios = build_scenarios(
        finance["INVOICES"],
        stock["STOCK_ALERTS"],
        procurement["PROCUREMENT_PRS"],
        procurement["PURCHASE_ORDERS"],
        hr["HR_DASHBOARD"],
    )
    out: dict[str, Any] = {}
    out.update(master)
    out.update(people)
    out.update(catalog)
    out.update(stock)
    out.update(finance)
    out.update(procurement)
    out.update(hr)
    out.update(scenarios)
    out.update(_LEGACY)
    return out


def as_namespace(data: dict[str, Any] | None = None) -> SimpleNamespace:
    return SimpleNamespace(**(data or build_all()))
