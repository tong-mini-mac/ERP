"""Thai payroll demo helpers: SSO, WHT, attendance deductions, leave balances.

Rules are intentionally simplified for ERP-Demo (CTO walkthrough), not a full
Revenue Department / SSO filing engine.
"""

from __future__ import annotations

from typing import Any

# SSO wage base cap (THB / month) — classic demo figure
SSO_WAGE_CAP = 15_000.0
SSO_RATE = 0.05  # employee + employer each 5%

# Personal income tax allowance (annual) used in monthly WHT estimate
PERSONAL_ALLOWANCE_YEAR = 60_000.0

# Attendance deduction policy (demo)
WORKING_DAYS_PER_MONTH = 30.0
LATE_PENALTY_THB = 100.0  # flat per late
LATES_AS_HALF_DAY = 3  # every N lates → extra 0.5 day unpaid

# Default annual entitlements (demo / Labor Protection Act flavoured)
LEAVE_ENTITLEMENTS = {
    "annual": 6.0,
    "sick": 30.0,
    "personal": 3.0,
}

# Progressive PIT brackets (annual taxable income)
_PIT_BRACKETS: list[tuple[float, float]] = [
    (150_000, 0.00),
    (300_000, 0.05),
    (500_000, 0.10),
    (750_000, 0.15),
    (1_000_000, 0.20),
    (2_000_000, 0.25),
    (5_000_000, 0.30),
    (float("inf"), 0.35),
]


def _r2(n: float) -> float:
    return round(float(n) + 1e-9, 2)


def sso_employee(gross: float) -> float:
    base = min(max(gross, 0.0), SSO_WAGE_CAP)
    return _r2(base * SSO_RATE)


def sso_employer(gross: float) -> float:
    return sso_employee(gross)


def annual_pit(taxable_annual: float) -> float:
    """Progressive PIT on annual taxable income."""
    remaining = max(taxable_annual, 0.0)
    prev_cap = 0.0
    tax = 0.0
    for cap, rate in _PIT_BRACKETS:
        slice_amt = min(remaining, cap - prev_cap)
        if slice_amt <= 0:
            break
        tax += slice_amt * rate
        remaining -= slice_amt
        prev_cap = cap
        if remaining <= 0:
            break
    return _r2(tax)


def withholding_tax_monthly(gross: float, sso_emp: float) -> float:
    """Estimate monthly WHT from annualised gross − SSO − personal allowance."""
    annual_gross = gross * 12.0
    annual_sso = sso_emp * 12.0
    taxable = max(0.0, annual_gross - annual_sso - PERSONAL_ALLOWANCE_YEAR)
    return _r2(annual_pit(taxable) / 12.0)


def attendance_counts(
    attendance: list[dict[str, Any]],
    employee_id: str,
    period: str,
) -> dict[str, Any]:
    """Count present/late/absent for YYYY-MM period."""
    present = late = absent = 0
    for row in attendance:
        if row.get("employee_id") != employee_id:
            continue
        day = str(row.get("date") or "")
        if not day.startswith(period):
            continue
        st = (row.get("status") or "").lower()
        if st == "late":
            late += 1
        elif st == "absent":
            absent += 1
        elif st == "present":
            present += 1
    return {
        "present_days": present,
        "late_days": late,
        "absent_days": absent,
    }


def attendance_deduction(gross: float, counts: dict[str, Any]) -> dict[str, Any]:
    daily = _r2(gross / WORKING_DAYS_PER_MONTH) if gross else 0.0
    absent = int(counts.get("absent_days") or 0)
    late = int(counts.get("late_days") or 0)
    absent_amt = _r2(absent * daily)
    late_flat = _r2(late * LATE_PENALTY_THB)
    half_days = (late // LATES_AS_HALF_DAY) * 0.5
    late_day_amt = _r2(half_days * daily)
    total = _r2(absent_amt + late_flat + late_day_amt)
    return {
        "daily_rate": daily,
        "absent_days": absent,
        "late_days": late,
        "absent_deduction": absent_amt,
        "late_penalty": late_flat,
        "late_half_day_deduction": late_day_amt,
        "attendance_deduction": total,
        "notes": [
            f"Absent {absent} day(s) × {daily:.2f}",
            f"Late {late} × {LATE_PENALTY_THB:.0f} THB"
            + (f" + {half_days:g} unpaid half-day" if half_days else ""),
        ],
    }


def calculate_payslip(
    employee: dict[str, Any],
    *,
    period: str,
    attendance: list[dict[str, Any]] | None = None,
    status: str = "calculated",
) -> dict[str, Any]:
    """Full TH payslip: gross → attendance → SSO → WHT → net."""
    gross = float(employee.get("salary") or 0)
    counts = attendance_counts(attendance or [], str(employee.get("id") or ""), period)
    attn = attendance_deduction(gross, counts)

    # Taxable base for SSO/WHT uses contractual gross (not reduced by attendance)
    # Attendance is a separate unpaid deduction before net.
    sso_emp = sso_employee(gross)
    sso_er = sso_employer(gross)
    wht = withholding_tax_monthly(gross, sso_emp)
    attendance_ded = float(attn["attendance_deduction"])

    total_deductions = _r2(sso_emp + wht + attendance_ded)
    net = _r2(max(0.0, gross - total_deductions))

    return {
        "employee_id": employee.get("id"),
        "employee": employee.get("full_name") or employee.get("name"),
        "code": employee.get("code"),
        "department": employee.get("department"),
        "period": period,
        "currency": employee.get("currency") or "THB",
        "status": status,
        "gross": _r2(gross),
        "earnings": [
            {"code": "BASIC", "name": "เงินเดือน / Basic salary", "amount": _r2(gross)},
        ],
        "deductions": [
            {
                "code": "SSO",
                "name": "ประกันสังคม (ลูกจ้าง 5%)",
                "amount": sso_emp,
                "meta": {"rate": SSO_RATE, "wage_cap": SSO_WAGE_CAP},
            },
            {
                "code": "WHT",
                "name": "ภาษีหัก ณ ที่จ่าย (ประมาณการ)",
                "amount": wht,
                "meta": {"method": "annualise_progressive_pit"},
            },
            {
                "code": "ATTN",
                "name": "หักขาดงาน / สาย",
                "amount": attendance_ded,
                "meta": attn,
            },
        ],
        "employer_contributions": [
            {
                "code": "SSO_ER",
                "name": "ประกันสังคม (นายจ้าง 5%)",
                "amount": sso_er,
            }
        ],
        "sso_employee": sso_emp,
        "sso_employer": sso_er,
        "withholding_tax": wht,
        "attendance": attn,
        "total_deductions": total_deductions,
        "net": net,
        # aliases for SPA that may read net_pay / total_net
        "net_pay": net,
        "salary": _r2(gross),
    }


def build_payroll_run(
    employees: list[dict[str, Any]],
    *,
    period: str,
    status: str,
    attendance: list[dict[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    lines = [
        calculate_payslip(e, period=period, attendance=attendance, status=status)
        for e in employees
    ]
    total_gross = _r2(sum(float(x["gross"]) for x in lines))
    total_net = _r2(sum(float(x["net"]) for x in lines))
    total_sso = _r2(sum(float(x["sso_employee"]) for x in lines))
    total_wht = _r2(sum(float(x["withholding_tax"]) for x in lines))
    total_attn = _r2(sum(float(x["attendance"]["attendance_deduction"]) for x in lines))
    return {
        "id": run_id or f"pay-{period}",
        "period": period,
        "status": status,
        "currency": "THB",
        "total": total_net,
        "total_net": total_net,
        "total_gross": total_gross,
        "total_sso_employee": total_sso,
        "total_withholding_tax": total_wht,
        "total_attendance_deduction": total_attn,
        "employee_count": len(lines),
        "lines": lines,
        "country": "TH",
        "calc_version": "th-demo-v1",
    }


def leave_balances(
    employees: list[dict[str, Any]],
    leave_requests: list[dict[str, Any]],
    *,
    year: int = 2026,
) -> list[dict[str, Any]]:
    """Per-employee leave balances from entitlements − approved usage."""
    used: dict[str, dict[str, float]] = {}
    for req in leave_requests:
        if (req.get("status") or "").lower() != "approved":
            continue
        emp_id = str(req.get("employee_id") or "")
        typ = str(req.get("type") or req.get("leave_type") or "annual").lower()
        if typ not in LEAVE_ENTITLEMENTS:
            typ = "annual"
        days = float(req.get("days") or 0)
        bucket = used.setdefault(emp_id, {k: 0.0 for k in LEAVE_ENTITLEMENTS})
        bucket[typ] = _r2(bucket.get(typ, 0.0) + days)

    out: list[dict[str, Any]] = []
    for emp in employees:
        emp_id = str(emp.get("id") or "")
        u = used.get(emp_id, {})
        types = []
        for typ, entitled in LEAVE_ENTITLEMENTS.items():
            used_days = _r2(float(u.get(typ, 0.0)))
            remaining = _r2(max(0.0, entitled - used_days))
            types.append(
                {
                    "type": typ,
                    "name": {
                        "annual": "ลาพักร้อน",
                        "sick": "ลาป่วย",
                        "personal": "ลากิจ",
                    }.get(typ, typ),
                    "entitled": entitled,
                    "used": used_days,
                    "remaining": remaining,
                    "pending": 0.0,
                }
            )
        # pending days (not deducted from remaining yet)
        pending_by_type = {k: 0.0 for k in LEAVE_ENTITLEMENTS}
        for req in leave_requests:
            if req.get("employee_id") != emp_id:
                continue
            if (req.get("status") or "").lower() != "pending":
                continue
            typ = str(req.get("type") or "annual").lower()
            if typ not in pending_by_type:
                typ = "annual"
            pending_by_type[typ] = _r2(pending_by_type[typ] + float(req.get("days") or 0))
        for row in types:
            row["pending"] = pending_by_type.get(row["type"], 0.0)

        out.append(
            {
                "employee_id": emp_id,
                "employee": emp.get("full_name") or emp.get("name"),
                "code": emp.get("code"),
                "year": year,
                "balances": types,
                "total_remaining": _r2(sum(t["remaining"] for t in types)),
            }
        )
    return out
