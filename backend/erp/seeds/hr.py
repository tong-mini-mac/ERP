"""HR attendance, leave, payroll story data."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from erp.payroll_th import build_payroll_run, leave_balances


def build_hr(employees: list[dict]) -> dict[str, Any]:
    today = date(2026, 9, 7)
    attendance = []
    # Last 30 days: mark absences + late for story
    absent_ids = {employees[2]["id"], employees[5]["id"], employees[8]["id"]}
    late_ids = {employees[i]["id"] for i in (1, 3, 4, 6, 7)}
    for d in range(30):
        day = today - timedelta(days=d)
        if day.weekday() >= 5:
            continue
        for emp in employees:
            status = "present"
            if emp["id"] in absent_ids and d % 11 == 0:
                status = "absent"
            elif emp["id"] in late_ids and d % 7 == 0:
                status = "late"
            attendance.append(
                {
                    "date": day.isoformat(),
                    "employee_id": emp["id"],
                    "employee": emp["full_name"],
                    "status": status,
                }
            )

    leave = []
    leave_mix = (
        [("approved", 2)] * 4
        + [("pending", 1)] * 4
        + [("rejected", 1)] * 2
    )
    for i, (status, days) in enumerate(leave_mix):
        emp = employees[(i + 1) % len(employees)]
        leave.append(
            {
                "id": f"leave-{i + 1}",
                "employee_id": emp["id"],
                "employee": emp["full_name"],
                "type": ["annual", "sick", "personal"][i % 3],
                "days": days + (i % 2),
                "status": status,
                "start_date": (today - timedelta(days=20 + i)).isoformat(),
                "end_date": (today - timedelta(days=20 + i - (days + (i % 2)) + 1)).isoformat(),
            }
        )

    pending_leave = [x for x in leave if x["status"] == "pending"]
    on_leave_today = sum(
        1 for a in attendance if a["date"] == today.isoformat() and a["status"] == "absent"
    )

    balances = leave_balances(employees, leave, year=today.year)

    payroll = [
        build_payroll_run(
            employees,
            period="2026-08",
            status="paid",
            attendance=attendance,
        ),
        build_payroll_run(
            employees,
            period="2026-09",
            status="draft",
            attendance=attendance,
        ),
    ]

    dashboard = {
        "headcount": len(employees),
        "on_leave_today": on_leave_today,
        "pending_leave": len(pending_leave),
        "payroll_status": "ready",
        "absent_without_leave": 1,
        "payroll_total_net": payroll[0]["total_net"],
        "payroll_total_sso": payroll[0]["total_sso_employee"],
        "payroll_total_wht": payroll[0]["total_withholding_tax"],
    }

    return {
        "ATTENDANCE": attendance,
        "LEAVE_REQUESTS": leave,
        "LEAVE_PENDING": pending_leave,
        "LEAVE_BALANCES": balances,
        "PAYROLL_RUNS": payroll,
        "HR_DASHBOARD": dashboard,
    }
