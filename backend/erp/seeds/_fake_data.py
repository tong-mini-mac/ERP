"""Thai fake helpers for ERP-Demo synthetic data (not SynthComm)."""

from __future__ import annotations

FIRST = [
    "สมชาย", "สมหญิง", "วิชัย", "นภา", "อารีย์", "ประเสริฐ", "กมล", "ศิริพร",
    "ธนา", "พิมพ์ใจ", "อนุชา", "วราภรณ์", "ชัยวัฒน์", "มณี", "สุรชัย", "ปิยะ",
]
LAST = [
    "ใจดี", "รักดี", "สุขสันต์", "ตั้งตรง", "มีสุข", "ทองดี", "แซ่ลี้", "วงศ์ใหญ่",
    "บุญมา", "ศรีสุข", "เจริญ", "พานิช", "อรุณ", "แสงทอง", "วัฒนา",
]

COMPANY_SUFFIX = ["จำกัด", "จำกัด (มหาชน)", "ห้างหุ้นส่วนจำกัด"]

STREETS = [
    "ถนนสีลม", "ถนนสุขุมวิท", "ถนนพระราม 4", "ถนนรัชดาภิเษก", "ถนนลาดพร้าว",
]


def person_name(i: int) -> str:
    return f"{FIRST[i % len(FIRST)]} {LAST[(i * 3) % len(LAST)]}"


def company_name(i: int, base: str) -> str:
    return f"{base} {COMPANY_SUFFIX[i % len(COMPANY_SUFFIX)]}"


def tax_id(seq: int) -> str:
    # Fictional 13-digit Thai-style tax id (not a real registrant).
    return f"01055{seq:08d}"[:13]


def barcode(seq: int) -> str:
    return f"8850999{seq:06d}"


def phone(seq: int) -> str:
    return f"02-{1000 + (seq % 8000):04d}-{1000 + ((seq * 7) % 9000):04d}"
