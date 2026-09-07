"""Industry verticals for ERP-Demo.

Only Resto is demo-ready in this sandbox. Clinic / Beauty / Ecommerce / Trading
are listed as pending so portfolio reviewers see the roadmap without empty modules.
"""

from __future__ import annotations

from typing import Any

BUSINESS_VERTICALS: list[dict[str, Any]] = [
    {
        "id": "resto",
        "label": "Resto",
        "label_th": "ร้านอาหาร",
        "status": "demo",
        "summary": "Menus, recipe cost, dine-in, table sessions, delivery platforms",
        "summary_th": "เมนู ต้นทุนสูตร dine-in / delivery platforms",
        "routes": ["/resto-menu", "/marketing"],
        "api_prefix": ["/api/resto", "/api/marketing/legs/resto"],
    },
    {
        "id": "clinic",
        "label": "Clinic",
        "label_th": "คลินิก",
        "status": "pending",
        "summary": "Appointments, pets, mode (pet/dental)",
        "summary_th": "นัดหมาย สัตว์เลี้ยง โหมด pet/dental",
        "routes": [],
        "api_prefix": [],
    },
    {
        "id": "beauty",
        "label": "Beauty",
        "label_th": "ความงาม",
        "status": "pending",
        "summary": "Clients, rooms, appointments, media upload",
        "summary_th": "ลูกค้า ห้อง นัดหมาย อัปโหลดสื่อ",
        "routes": [],
        "api_prefix": [],
    },
    {
        "id": "ecommerce",
        "label": "Ecommerce",
        "label_th": "อีคอมเมิร์ซ",
        "status": "pending",
        "summary": "Catalog, channel orders, marketplace ingest",
        "summary_th": "แคตตาล็อกออเดอร์ช่องทาง marketplace",
        "routes": [],
        "api_prefix": [],
    },
    {
        "id": "trading",
        "label": "Trading",
        "label_th": "เทรดดิ้ง",
        "status": "pending",
        "summary": "Customers, price lists, quotations, payment reminders",
        "summary_th": "ลูกค้า ราคา ใบเสนอราคา เตือนชำระเงิน",
        "routes": [],
        "api_prefix": [],
    },
]


def list_businesses() -> dict[str, Any]:
    demo = [v for v in BUSINESS_VERTICALS if v["status"] == "demo"]
    pending = [v for v in BUSINESS_VERTICALS if v["status"] == "pending"]
    return {
        "items": list(BUSINESS_VERTICALS),
        "demo_ready": [v["id"] for v in demo],
        "pending": [v["id"] for v in pending],
        "note": "ERP-Demo currently ships Resto only; other industry legs are pending.",
        "note_th": "ตอนนี้ทดสอบ demo ได้เฉพาะ Resto — ธุรกิจอื่นขึ้นสถานะ pending ไว้ก่อน",
    }
