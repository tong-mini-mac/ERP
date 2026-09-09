"""Document OCR scan history + manual entry seed."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

VENDORS = [
    "Demo Supplier Co.", "Bangkok Pack Co.", "Silom Fresh Foods",
    "Asok Office Supply", "Gulf Logistics TH", "Northern Cold Chain",
    "Eastern Plastics", "ASEAN Spice Hub", "Chiang Mai Agro", "Local Pack Thailand",
]

# ≥50 mock rows per document type for testing
DOC_TYPES = [
    "pr",
    "tor",
    "receipt",
    "tax_invoice",
    "invoice",
    "quote",
    "po",
    "contract",
    "delivery",
    "vendor_invoice",
    "important",
]


def build_documents() -> dict[str, Any]:
    today = date(2026, 9, 7)
    scans: list[dict[str, Any]] = []
    n = 50
    idx = 0
    for doc_type in DOC_TYPES:
        for i in range(n):
            idx += 1
            day = today - timedelta(days=(idx % 90))
            vendor = VENDORS[idx % len(VENDORS)]
            total = 800 + idx * 95
            scans.append(
                {
                    "id": f"scan-{doc_type}-{i + 1:03d}",
                    "filename": f"{doc_type}-{i + 1:03d}.pdf",
                    "doc_type": doc_type,
                    "status": ["parsed", "parsed", "review", "parsed"][idx % 4],
                    "vendor": vendor,
                    "vendor_tax_id": f"01055{6600000 + idx}",
                    "invoice_number": f"DOC-2026-{1000 + idx}",
                    "total": total,
                    "currency": "THB",
                    "scanned_at": day.isoformat(),
                    "source": "upload" if idx % 5 else "manual",
                    "requires_physical_original": doc_type
                    in ("receipt", "tax_invoice", "contract", "important"),
                    "physical_status": (
                        "pending_send"
                        if doc_type in ("receipt", "tax_invoice", "contract", "important")
                        else "not_required"
                    ),
                    "lines": [
                        {"desc": f"{doc_type} line {j + 1}", "qty": j + 1, "amount": total // 3}
                        for j in range(3)
                    ],
                }
            )
    return {"DOCUMENT_SCANS": scans}
