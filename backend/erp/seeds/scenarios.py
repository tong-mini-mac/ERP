"""Dashboard scenarios — the 'problems to solve' for reviewers."""

from __future__ import annotations

from typing import Any


def build_scenarios(
    invoices: list[dict],
    stock_alerts: dict,
    prs: list[dict],
    pos: list[dict],
    hr_dashboard: dict,
) -> dict[str, Any]:
    overdue = [i for i in invoices if i.get("status") == "overdue"]
    pending_pr = [p for p in prs if p.get("status") == "pending"]
    partial_po = [p for p in pos if p.get("status") == "partial"]
    return {
        "DEMO_SCENARIOS": {
            "overdue_invoices": overdue,
            "low_stock": stock_alerts.get("low_stock", []),
            "out_of_stock": stock_alerts.get("out_of_stock", []),
            "pending_prs": pending_pr,
            "partial_pos": partial_po,
            "hr_flags": {
                "pending_leave": hr_dashboard.get("pending_leave"),
                "absent_without_leave": hr_dashboard.get("absent_without_leave"),
            },
            "headline": [
                "🔴 ใบแจ้งหนี้ค้างชำระ 3 รายการ — ทดสอบ aging / follow-up",
                "🟡 สินค้าใกล้จุดสั่งซื้อ 5 รายการ — ทดสอบสร้าง PR",
                "🟡 PR รออนุมัติหลายรายการ — ทดสอบ workflow",
                "🔴 มีพนักงานขาดโดยไม่มีใบลา — ทดสอบ HR alert",
                "🟢 PO รับของบางส่วน — ทดสอบ partial receive",
            ],
        }
    }
