"""Users, org members, employees."""

from __future__ import annotations

from typing import Any

from erp.seeds._fake_data import person_name

DEMO_PASSWORD = "demo-erp-2026"
DEMO_EMAIL = "demo@erp.demo"

TITLES = [
    ("เจ้าของกิจการ / Owner", "owner", "dept-finance"),
    ("ผู้จัดการฝ่ายบัญชี", "finance", "dept-finance"),
    ("เจ้าหน้าที่บัญชี", "finance", "dept-finance"),
    ("HR Manager", "hr", "dept-hr"),
    ("HR Officer", "hr", "dept-hr"),
    ("หัวหน้าคลัง", "warehouse", "dept-wh"),
    ("พนักงานคลัง", "warehouse", "dept-wh"),
    ("ผู้จัดการจัดซื้อ", "purchasing", "dept-purch"),
    ("เจ้าหน้าที่จัดซื้อ", "purchasing", "dept-purch"),
    ("Marketing Lead", "marketing", "dept-mkt"),
]


def build_people() -> dict[str, Any]:
    users: dict[str, dict] = {
        DEMO_EMAIL: {
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "full_name": "ThaiTrade Demo Owner",
            "shop_name": "ThaiTrade Solutions",
            "role": "owner",
        }
    }
    members: list[dict] = []
    employees: list[dict] = []

    for i in range(50):
        name = "ThaiTrade Demo Owner" if i == 0 else person_name(i)
        title, role, dept = TITLES[i % len(TITLES)]
        if i == 0:
            title, role, dept = TITLES[0]
        email = DEMO_EMAIL if i == 0 else f"staff{i:02d}@thaitrade.demo"
        emp_type = "full_time" if i < 40 else "part_time"
        salary = 45000 - (i * 400) if emp_type == "full_time" else 18000
        # SPA HR table reads `name` (not full_name) + hyphenated employment_type.
        emp = {
            "id": f"emp-{i + 1:02d}",
            "code": f"E{i + 1:03d}",
            "name": name,
            "full_name": name,
            "title": title,
            "status": "active",
            "department": dept.replace("dept-", "").upper(),
            "department_id": dept,
            "employment_type": emp_type.replace("_", "-"),
            "salary": salary,
            "currency": "THB",
            "start_date": "2024-01-15" if i == 0 else f"2024-{(i % 12) + 1:02d}-01",
            "bank_account": f"1234567{i:03d}",
            "bank_name": "SCB",
            "manager_id": None if i == 0 else 1,
        }
        employees.append(emp)
        members.append(
            {
                "id": f"mem-{i + 1:02d}",
                "email": email,
                "full_name": name,
                "role": role if i < 10 else "staff",
                "department_id": dept,
            }
        )
        if i > 0:
            users[email] = {
                "email": email,
                "password": DEMO_PASSWORD,
                "full_name": name,
                "shop_name": "ThaiTrade Solutions",
                "role": role if i < 10 else "staff",
            }

    return {
        "DEMO_EMAIL": DEMO_EMAIL,
        "DEMO_PASSWORD": DEMO_PASSWORD,
        "USERS": users,
        "MEMBERS": members,
        "EMPLOYEES": employees,
    }
