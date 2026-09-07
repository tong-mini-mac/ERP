"""Finance docs: invoices with overdue story, receipts, GL slice."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def build_finance(customers: list[dict]) -> dict[str, Any]:
    today = date(2026, 9, 7)
    invoices: list[dict] = []
    # 30 tax invoices: paid 20, pending 7, overdue 3
    for i in range(50):
        cust = customers[i % len(customers)]
        issued = today - timedelta(days=5 + i * 2)
        due = issued + timedelta(days=15)
        if i < 3:
            status = "overdue"
            due = today - timedelta(days=10 + i * 3)
        elif i < 10:
            status = "pending"
        else:
            status = "paid"
        amount = 3500 + i * 850
        invoices.append(
            {
                "id": f"inv-{i + 1:03d}",
                "number": f"INV-TT-2026-{i + 1:03d}",
                "title": f"INV-TT-2026-{i + 1:03d}",
                "type": "tax_invoice",
                "customer_id": cust["id"],
                "customer_name": cust["name"],
                "issue_date": issued.isoformat(),
                "due_date": due.isoformat(),
                "status": status,
                "subtotal": amount,
                "vat": round(amount * 0.07, 2),
                "total": round(amount * 1.07, 2),
                "currency": "THB",
                "days_overdue": max(0, (today - due).days) if status == "overdue" else 0,
            }
        )

    billing_notes = []
    for i in range(20):
        billing_notes.append(
            {
                "id": f"bn-{i + 1:02d}",
                "number": f"BN-2026-{i + 1:03d}",
                "status": ["draft", "sent", "paid"][i % 3],
                "total": 8000 + i * 400,
                "currency": "THB",
                "customer_id": customers[i % len(customers)]["id"],
            }
        )

    receipts = []
    for i, inv in enumerate(invoices):
        if inv["status"] != "paid":
            continue
        if len(receipts) >= 18:
            break
        receipts.append(
            {
                "id": f"rcpt-{len(receipts) + 1:02d}",
                "number": f"RC-2026-{len(receipts) + 1:03d}",
                "invoice_id": inv["id"],
                "amount": inv["total"],
                "currency": "THB",
                "paid_date": inv["issue_date"],
            }
        )

    credit_notes = [
        {"id": f"cn-{i+1}", "number": f"CN-2026-{i+1:03d}", "total": 500 + i * 200, "status": "posted"}
        for i in range(4)
    ]
    debit_notes = [
        {"id": f"dn-{i+1}", "number": f"DN-2026-{i+1:03d}", "total": 300 + i * 150, "status": "posted"}
        for i in range(3)
    ]

    gl_entries = []
    for i in range(60):
        day = today - timedelta(days=i % 90)
        gl_entries.append(
            {
                "id": f"gl-{i + 1:03d}",
                "date": day.isoformat(),
                "memo": f"Demo journal #{i + 1}",
                "lines": [
                    {"account": "1200" if i % 2 == 0 else "5100", "debit": 1000 + i * 10, "credit": 0},
                    {"account": "4100" if i % 2 == 0 else "1100", "debit": 0, "credit": 1000 + i * 10},
                ],
            }
        )

    # Simple 3-month P&L story: profit, loss, profit
    income_statements = [
        {"period": "2026-06", "revenue": 420000, "cogs": 210000, "opex": 150000, "net": 60000},
        {"period": "2026-07", "revenue": 380000, "cogs": 200000, "opex": 195000, "net": -15000},
        {"period": "2026-08", "revenue": 455000, "cogs": 220000, "opex": 160000, "net": 75000},
    ]
    balance_sheet = {
        "as_of": "2026-08-31",
        "assets": 1850000,
        "liabilities": 640000,
        "equity": 1210000,
        "currency": "THB",
    }

    accounting_documents = [
        {
            "id": inv["id"],
            "title": inv["number"],
            "status": inv["status"],
            "type": "invoice",
            "total": inv["total"],
            "customer_name": inv["customer_name"],
            "due_date": inv["due_date"],
        }
        for inv in invoices
    ]

    return {
        "INVOICES": invoices,
        "BILLING_NOTES": billing_notes,
        "RECEIPTS": receipts,
        "CREDIT_NOTES": credit_notes,
        "DEBIT_NOTES": debit_notes,
        "GL_ENTRIES": gl_entries,
        "INCOME_STATEMENTS": income_statements,
        "BALANCE_SHEET": balance_sheet,
        "ACCOUNTING_DOCUMENTS": accounting_documents,
        "ACCOUNTING_TYPES": [
            {"id": "invoice", "name": "Tax Invoice"},
            {"id": "billing_note", "name": "Billing Note"},
            {"id": "receipt", "name": "Receipt"},
            {"id": "credit_note", "name": "Credit Note"},
            {"id": "debit_note", "name": "Debit Note"},
        ],
        "ACCOUNTING_TEMPLATES": [
            {"id": "tpl-inv-th", "name": "ใบกำกับภาษี TH", "type": "invoice"},
            {"id": "tpl-rc-th", "name": "ใบเสร็จรับเงิน TH", "type": "receipt"},
        ],
    }
