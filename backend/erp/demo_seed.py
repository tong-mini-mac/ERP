"""Simulated tenant data for ERP-Demo sandbox only.

Not linked to company ATLAS / production ERP tenants.
"""

from __future__ import annotations

DEMO_PASSWORD = "demo-erp-2026"
DEMO_EMAIL = "demo@erp.demo"

USERS: dict[str, dict] = {
    DEMO_EMAIL: {
        "email": DEMO_EMAIL,
        "password": DEMO_PASSWORD,
        "full_name": "ERP Demo User",
        "shop_name": "ERP Demo Sandbox",
        "role": "owner",
    }
}

TENANT = {
    "id": "tenant-demo-001",
    "name": "ERP Demo Sandbox",
    "plan_tier": "micro",
    "country_code": "TH",
    "environment": "demo",
    "isolated_from_production_erp": True,
}

TIERS = [
    {"tier": "solo", "name": "Solo", "price_thb": 990},
    {"tier": "micro", "name": "Micro", "price_thb": 2990},
    {"tier": "small", "name": "Small", "price_thb": 6990},
]

BRANCHES = [
    {
        "id": "branch-hq",
        "name": "สาขาทดสอบ (HQ)",
        "code": "HQ",
        "city": "Bangkok",
        "is_primary": True,
    }
]

DEPARTMENTS = [
    {"id": "dept-finance", "name": "Finance", "code": "FIN"},
    {"id": "dept-hr", "name": "HR", "code": "HR"},
    {"id": "dept-ops", "name": "Operations", "code": "OPS"},
]

MEMBERS = [
    {
        "id": "mem-1",
        "email": DEMO_EMAIL,
        "full_name": "ERP Demo User",
        "role": "owner",
        "department_id": "dept-ops",
    },
    {
        "id": "mem-2",
        "email": "finance@erp.demo",
        "full_name": "สมหญิง บัญชี",
        "role": "finance",
        "department_id": "dept-finance",
    },
]

EMPLOYEES = [
    {
        "id": "emp-1",
        "code": "E001",
        "full_name": "สมชาย ใจดี",
        "title": "Store Manager",
        "status": "active",
        "department": "Operations",
    },
    {
        "id": "emp-2",
        "code": "E002",
        "full_name": "สมหญิง บัญชี",
        "title": "Accountant",
        "status": "active",
        "department": "Finance",
    },
    {
        "id": "emp-3",
        "code": "E003",
        "full_name": "วิชัย สต็อก",
        "title": "Warehouse",
        "status": "active",
        "department": "Operations",
    },
]

SKUS = [
    {
        "id": "sku-1",
        "sku": "DRINK-001",
        "name": "น้ำดื่ม 600ml",
        "barcode": "8850999000001",
        "unit": "bottle",
        "qty_on_hand": 120,
        "cost": 5.5,
        "price": 10.0,
    },
    {
        "id": "sku-2",
        "sku": "SNACK-014",
        "name": "ขนมถุงทดสอบ",
        "barcode": "8850999000014",
        "unit": "pack",
        "qty_on_hand": 48,
        "cost": 12.0,
        "price": 25.0,
    },
    {
        "id": "sku-3",
        "sku": "PKG-BOX",
        "name": "กล่องพัสดุ S",
        "barcode": "8850999000099",
        "unit": "pcs",
        "qty_on_hand": 200,
        "cost": 3.0,
        "price": 8.0,
    },
]

WAREHOUSES = [
    {"id": "wh-1", "name": "คลังหลัก (Demo)", "code": "MAIN", "branch_id": "branch-hq"}
]

PROCUREMENT_PRS = [
    {
        "id": "pr-1001",
        "title": "สั่งน้ำดื่มรอบ Demo",
        "status": "approved",
        "vendor": "Demo Supplier Co.",
        "total": 5500,
        "currency": "THB",
    },
    {
        "id": "pr-1002",
        "title": "กล่องพัสดุสำรอง",
        "status": "draft",
        "vendor": "Pack Demo Ltd.",
        "total": 1800,
        "currency": "THB",
    },
]

FINANCE_COUNTRIES = [
    {"code": "TH", "name": "Thailand", "currency": "THB", "vat_rate": 0.07}
]

MENUS = [
    {
        "id": "menu-1",
        "name": "เมนูทดสอบร้านอาหาร",
        "items": [
            {"id": "mi-1", "name": "ข้าวผัดกุ้ง", "price": 89},
            {"id": "mi-2", "name": "ต้มยำกุ้ง", "price": 129},
        ],
    }
]

INGREDIENTS = [
    {"id": "ing-1", "name": "ข้าวสวย", "unit": "kg", "on_hand": 40},
    {"id": "ing-2", "name": "กุ้ง", "unit": "kg", "on_hand": 8},
]

CAMPAIGNS_PRE = [
    {
        "id": "camp-1",
        "name": "โปรเปิดสาขา Demo",
        "status": "draft",
        "channel": "facebook",
    }
]

CAMPAIGNS_POST = [
    {
        "id": "camp-2",
        "name": "รีวิวหลังใช้ Demo",
        "status": "scheduled",
        "channel": "line",
    }
]

WORKFLOW_INBOX = {"count": 1, "items": [{"id": "wf-1", "title": "อนุมัติ PR-1002", "status": "pending"}]}

ONBOARDING = {
    "completed": True,
    "items": [
        {"key": "shop", "label": "ตั้งค่าหน้าร้าน", "done": True},
        {"key": "sku", "label": "เพิ่มสินค้าตัวอย่าง", "done": True},
        {"key": "warehouse", "label": "สร้างคลัง", "done": True},
    ],
}
