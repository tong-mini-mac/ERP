"""HR attendance, leave, payroll story data."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


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
            }
        )

    pending_leave = [x for x in leave if x["status"] == "pending"]
    on_leave_today = sum(1 for a in attendance if a["date"] == today.isoformat() and a["status"] == "absent")

    payroll = []
    for period, status in (("2026-08", "paid"), ("2026-09", "draft")):
        lines = [
            {"employee": e["full_name"], "employee_id": e["id"], "net": e["salary"]}
            for e in employees
        ]
        total = sum(x["net"] for x in lines)
        payroll.append(
            {
                "id": f"pay-{period}",
                "period": period,
                "status": status,
                "total": total,
                "currency": "THB",
                "lines": lines,
            }
        )

    dashboard = {
        "headcount": len(employees),
        "on_leave_today": on_leave_today,
        "pending_leave": len(pending_leave),
        "payroll_status": "ready",
        "absent_without_leave": 1,
    }

    return {
        "ATTENDANCE": attendance,
        "LEAVE_REQUESTS": leave,
        "LEAVE_PENDING": pending_leave,
        "PAYROLL_RUNS": payroll,
        "HR_DASHBOARD": dashboard,
    }
