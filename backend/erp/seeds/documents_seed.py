"""Document OCR scan history + manual entry seed."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

VENDORS = [
    "Demo Supplier Co.", "Bangkok Pack Co.", "Silom Fresh Foods",
    "Asok Office Supply", "Gulf Logistics TH", "Northern Cold Chain",
    "Eastern Plastics", "ASEAN Spice Hub", "Chiang Mai Agro", "Local Pack Thailand",
]


def build_documents() -> dict[str, Any]:
    today = date(2026, 9, 7)
    scans: list[dict[str, Any]] = []
    types = ["invoice", "tor", "contract"]
    for i in range(50):
        doc_type = types[i % 3]
        day = today - timedelta(days=i % 40)
        vendor = VENDORS[i % len(VENDORS)]
        total = 1500 + i * 175
        scans.append(
            {
                "id": f"scan-{i + 1:02d}",
                "filename": f"{doc_type}-{i + 1:02d}.pdf",
                "doc_type": doc_type,
                "status": ["parsed", "parsed", "review", "parsed"][i % 4],
                "vendor": vendor,
                "vendor_tax_id": f"01055{6600000 + i}",
                "invoice_number": f"INV-2026-{1000 + i}",
                "total": total,
                "currency": "THB",
                "scanned_at": day.isoformat(),
                "source": "upload" if i % 5 else "manual",
                "lines": [
                    {"desc": f"Line item {j + 1}", "qty": j + 1, "amount": total // 3}
                    for j in range(3)
                ],
            }
        )
    return {"DOCUMENT_SCANS": scans}
