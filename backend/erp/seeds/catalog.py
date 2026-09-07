"""Customers, vendors, SKUs."""

from __future__ import annotations

from typing import Any

from erp.seeds._fake_data import barcode, company_name, phone, tax_id

CUSTOMER_BASES = [
    "ซิโลม รีเทล", "อโศก มาร์ท", "สาทร ซัพพลาย", "บางนา เทรดดิ้ง", "ลาดพร้าว สโตร์",
    "พระรามเก้า ดิสทริบิวชัน", "หัวลำโพง อิมปอร์ต", "เจริญกรุง คอมเมิร์ซ", "รัชดา โฮลเซล",
    "อ่อนนุช เซ็นเตอร์", "บางกะปิ เซอร์วิส", "ดินแดง พาร์ทเนอร์", "คลองเตย โลจิสติกส์",
    "ยานนาวา ซัพพลาย", "บางคอแหลม ค้าปลีก",
]

VENDOR_BASES = [
    "Shanghai Export House", "Osaka Parts Co", "Busan Marine Goods",
    "Local Pack Thailand", "Chiang Mai Agro", "Eastern Plastics",
    "Gulf Logistics TH", "Northern Cold Chain", "Bangkok Carton", "ASEAN Spice Hub",
]

SKU_CATALOG = [
    ("DRINK", "น้ำดื่ม", "bottle", 5.5, 10.0),
    ("SNACK", "ขนมถุง", "pack", 12.0, 25.0),
    ("PKG", "กล่องพัสดุ", "pcs", 3.0, 8.0),
    ("ELEC", "สายชาร์จ USB-C", "pcs", 45.0, 99.0),
    ("HOME", "ผ้าเช็ดตัว", "pcs", 60.0, 129.0),
    ("FOOD", "ข้าวสาร 5kg", "bag", 95.0, 145.0),
    ("CHEM", "น้ำยาทำความสะอาด", "bottle", 35.0, 79.0),
    ("TOOL", "เทปใส", "roll", 8.0, 20.0),
    ("COSM", "ครีมบำรุง", "pcs", 120.0, 259.0),
    ("OFF", "กระดาษ A4", "ream", 85.0, 120.0),
]


def build_catalog() -> dict[str, Any]:
    customers = []
    for i, base in enumerate(CUSTOMER_BASES):
        customers.append(
            {
                "id": f"cus-{i + 1:02d}",
                "name": company_name(i, base),
                "tax_id": tax_id(2000 + i),
                "type": ["company", "partnership", "retail"][i % 3],
                "phone": phone(i + 10),
                "city": "Bangkok",
                "credit_limit": 100000 + i * 15000,
                "currency": "THB",
            }
        )

    vendors = []
    for i, base in enumerate(VENDOR_BASES):
        vendors.append(
            {
                "id": f"ven-{i + 1:02d}",
                "name": base if i < 3 else company_name(i, base),
                "tax_id": tax_id(3000 + i),
                "origin": "overseas" if i < 3 else "local",
                "phone": phone(i + 40),
                "currency": "USD" if i < 3 else "THB",
                "lead_days": 21 if i < 3 else 5,
            }
        )

    skus = []
    for i in range(50):
        prefix, label, unit, cost, price = SKU_CATALOG[i % len(SKU_CATALOG)]
        # Story: first 5 low stock, next 2 out of stock, rest healthy.
        if i < 5:
            qty = 3 + i  # near reorder
        elif i < 7:
            qty = 0
        else:
            qty = 40 + (i * 7) % 180
        skus.append(
            {
                "id": f"sku-{i + 1:02d}",
                "sku": f"{prefix}-{i + 1:03d}",
                "name": f"{label} #{i + 1:02d}",
                "barcode": barcode(i + 1),
                "unit": unit,
                "qty_on_hand": qty,
                "reorder_point": 10,
                "cost": cost + (i % 5),
                "price": price + (i % 7) * 2,
                "currency": "THB",
                "lot_tracked": i % 3 == 0,
            }
        )

    return {"CUSTOMERS": customers, "VENDORS": vendors, "SKUS": skus}
