"""Company master identity for ThaiTrade Solutions."""

from __future__ import annotations

from typing import Any


def build_master() -> dict[str, Any]:
    company = {
        "legal_name": "ThaiTrade Solutions Co., Ltd.",
        "legal_name_th": "บริษัท ไทยเทรด โซลูชันส์ จำกัด",
        "tax_id": "0105566012345",
        "address": "88/8 Silom Complex Bldg., Silom Rd., Bangkok 10500",
        "phone": "02-635-8800",
        "business": "Import-Export + Retail",
        "story": "Living fictional company for portfolio ERP-Demo (synth only).",
    }
    tenant = {
        "id": "tenant-thaitrade-001",
        "name": company["legal_name"],
        "name_th": company["legal_name_th"],
        "plan_tier": "micro",
        "country_code": "TH",
        "environment": "demo",
        "tax_id": company["tax_id"],
        "address": company["address"],
        "phone": company["phone"],
        "isolated_from_production_erp": True,
        # Unlock Marketing → ร้านอาหาร (resto) leg in the SPA. Other verticals stay pending.
        "features": ["marketing", "resto_platform"],
        "demo_business": "resto",
    }
    branches = [
        {
            "id": "branch-hq",
            "name": "สำนักงานใหญ่ สีลม",
            "code": "HQ",
            "city": "Bangkok",
            "address": company["address"],
            "is_primary": True,
        },
        {
            "id": "branch-asok",
            "name": "สาขาอโศก",
            "code": "ASK",
            "city": "Bangkok",
            "address": "Asok Montri Rd., Bangkok 10110",
            "is_primary": False,
        },
    ]
    departments = [
        {"id": "dept-finance", "name": "Accounting", "code": "ACC", "name_th": "บัญชี"},
        {"id": "dept-hr", "name": "HR", "code": "HR", "name_th": "ทรัพยากรบุคคล"},
        {"id": "dept-wh", "name": "Warehouse", "code": "WH", "name_th": "คลังสินค้า"},
        {"id": "dept-purch", "name": "Purchasing", "code": "PUR", "name_th": "จัดซื้อ"},
        {"id": "dept-mkt", "name": "Marketing", "code": "MKT", "name_th": "การตลาด"},
    ]
    # Slim Thai GAAP-flavoured chart of accounts for demo statements.
    chart_of_accounts = [
        {"code": "1100", "name": "Cash", "name_th": "เงินสด", "type": "asset"},
        {"code": "1200", "name": "Accounts receivable", "name_th": "ลูกหนี้การค้า", "type": "asset"},
        {"code": "1300", "name": "Inventory", "name_th": "สินค้าคงเหลือ", "type": "asset"},
        {"code": "2100", "name": "Accounts payable", "name_th": "เจ้าหนี้การค้า", "type": "liability"},
        {"code": "2200", "name": "VAT payable", "name_th": "ภาษีขาย", "type": "liability"},
        {"code": "3100", "name": "Share capital", "name_th": "ทุนจดทะเบียน", "type": "equity"},
        {"code": "4100", "name": "Sales revenue", "name_th": "รายได้จากการขาย", "type": "income"},
        {"code": "5100", "name": "COGS", "name_th": "ต้นทุนขาย", "type": "expense"},
        {"code": "5200", "name": "Salary expense", "name_th": "เงินเดือน", "type": "expense"},
        {"code": "5300", "name": "Operating expense", "name_th": "ค่าใช้จ่ายดำเนินงาน", "type": "expense"},
    ]
    tiers = [
        {"tier": "solo", "name": "Solo", "price_thb": 990},
        {"tier": "micro", "name": "Micro", "price_thb": 2990},
        {"tier": "small", "name": "Small", "price_thb": 6990},
    ]
    return {
        "COMPANY": company,
        "TENANT": tenant,
        "BRANCHES": branches,
        "DEPARTMENTS": departments,
        "CHART_OF_ACCOUNTS": chart_of_accounts,
        "TIERS": tiers,
        "FINANCE_COUNTRIES": [
            {"code": "TH", "name": "Thailand", "currency": "THB", "vat_rate": 0.07}
        ],
    }
