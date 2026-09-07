"""
Universal ERP Demo — customer trial sandbox (tong-mini-mac/ERP).

Purpose: let IN Z customers try ERP with synthetic data only.
Not a live company ERP. Not ATLAS. No shared ATLAS database.

Auth model:
- Customers sign in once on inz.lol (platform account)
- Landing opens ERP-Demo with ?inz_sso=... handoff
- This app exchanges that token for a local demo JWT and never calls ATLAS

SERVE_FRONTEND serves frontend/dist for monolith demo deploys.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from erp import demo_seed as seed

JWT_SECRET = os.getenv("JWT_SECRET", "erp-demo-dev-secret-change-me-32chars")
JWT_ALG = "HS256"
JWT_TTL_SEC = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "60")) * 60
ENVIRONMENT = os.getenv("ENVIRONMENT", "demo")
PRODUCT_MODE = os.getenv("PRODUCT_MODE", "erp-demo").strip().lower() or "erp-demo"
# Platform SSO from inz.lol landing (trial) — NOT ATLAS ERP integration.
ACCEPT_PLATFORM_SSO = os.getenv("ACCEPT_PLATFORM_SSO", "true").lower() in {
    "1",
    "true",
    "yes",
}
# Shared with inz.lol landing product-handoff HMAC (demo trail only).
PLATFORM_SSO_SECRET = (
    os.getenv("PLATFORM_SSO_SECRET")
    or os.getenv("INZ_SSO_SECRET")
    or os.getenv("ERP_DEMO_SSO_SECRET")
    or "dev-secret"
).strip()
ALLOWED_HANDOFF_PRODUCTS = {
    p.strip()
    for p in os.getenv("ALLOWED_HANDOFF_PRODUCTS", "erp-demo").split(",")
    if p.strip()
}
SERVE_FRONTEND = os.getenv("SERVE_FRONTEND", "true").lower() in {"1", "true", "yes"}
FRONTEND_DIST_DIR = Path(
    os.getenv(
        "FRONTEND_DIST_DIR",
        str(Path(__file__).resolve().parents[2] / "frontend" / "dist"),
    )
)

if PRODUCT_MODE not in {"erp-demo", "demo"}:
    raise RuntimeError(
        f"This repository serves ERP-Demo only (PRODUCT_MODE={PRODUCT_MODE!r}). "
        "Production / ATLAS ERP must run from a separate codebase and deployment."
    )


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    shop_name: str = "Demo Shop"
    full_name: str = "Demo User"


class PlatformSsoBody(BaseModel):
    token: str = Field(min_length=10)


def _b64url_decode(value: str) -> bytes:
    padded = value.replace("-", "+").replace("_", "/")
    pad = "=" * (-len(padded) % 4)
    return base64.b64decode(padded + pad)


def verify_platform_handoff(token: str) -> dict[str, Any]:
    """Verify inz.lol landing handoff HMAC. Does not contact ATLAS."""
    try:
        body, sig = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="invalid_token") from exc
    expected = hmac.new(
        PLATFORM_SSO_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    given = _b64url_decode(sig)
    if len(given) != len(expected) or not hmac.compare_digest(given, expected):
        raise HTTPException(status_code=401, detail="bad_signature")
    try:
        claims = json.loads(_b64url_decode(body).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=401, detail="invalid_claims") from exc
    email = str(claims.get("email") or "").strip().lower()
    product_id = str(claims.get("product_id") or "").strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=401, detail="invalid_email")
    if product_id not in ALLOWED_HANDOFF_PRODUCTS:
        raise HTTPException(status_code=403, detail="product_not_allowed")
    if int(time.time()) > int(claims.get("exp") or 0):
        raise HTTPException(status_code=401, detail="expired")
    return claims


def ensure_trial_user(email: str, full_name: str | None = None) -> dict[str, Any]:
    """Map any platform user into the local synth-data sandbox (not ATLAS)."""
    existing = seed.USERS.get(email)
    if existing:
        return existing
    user = {
        "email": email,
        "password": uuid.uuid4().hex,  # password login disabled for SSO trial users
        "full_name": full_name or email.split("@")[0],
        "shop_name": "ERP Demo Sandbox",
        "role": "owner",
        "source": "platform_sso",
    }
    seed.USERS[email] = user
    return user


def create_token(email: str) -> str:
    now = int(time.time())
    payload = {
        "sub": email,
        "iat": now,
        "exp": now + JWT_TTL_SEC,
        "iss": "erp-demo",
        "env": ENVIRONMENT,
        "sandbox": True,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1].strip()
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    email = str(data.get("sub") or "")
    user = seed.USERS.get(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "email": user["email"],
        "full_name": user.get("full_name"),
        "shop_name": user.get("shop_name"),
        "role": user.get("role", "owner"),
        "id": user["email"],
    }


app = FastAPI(title="Universal ERP Demo", version="1.0.0-demo")

cors_origins = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "https://www.inz.lol,https://inz.lol,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "universal-erp-demo",
        "product": "erp-demo",
        "environment": ENVIRONMENT,
        "company": getattr(seed, "COMPANY", {}).get("legal_name"),
        "repo": "tong-mini-mac/ERP",
        "isolated_from_atlas": True,
        "accept_platform_sso": ACCEPT_PLATFORM_SSO,
        "synth_data_only": True,
        "seed": {
            "skus": len(seed.SKUS),
            "employees": len(seed.EMPLOYEES),
            "invoices": len(getattr(seed, "INVOICES", [])),
            "customers": len(getattr(seed, "CUSTOMERS", [])),
        },
        "note": (
            "ThaiTrade Solutions synth sandbox; "
            "single login via inz.lol platform SSO; not linked to ATLAS"
        ),
    }


@app.post("/api/auth/inz-sso")
@app.post("/api/auth/product-handoff")
def exchange_platform_sso(body: PlatformSsoBody) -> dict[str, Any]:
    """Exchange inz.lol platform handoff for a local demo JWT.

    Does not call ATLAS. Issues sandbox access only against synth seed data.
    """
    if not ACCEPT_PLATFORM_SSO:
        raise HTTPException(status_code=409, detail="platform_sso_disabled")
    claims = verify_platform_handoff(body.token)
    email = str(claims["email"]).strip().lower()
    user = ensure_trial_user(email)
    return {
        "access_token": create_token(user["email"]),
        "token_type": "bearer",
        "sandbox": True,
        "email": user["email"],
        "isolated_from_atlas": True,
    }


@app.get("/api/auth/inz-sso")
@app.get("/api/auth/product-handoff")
def platform_sso_info() -> dict[str, Any]:
    return {
        "ok": True,
        "accept_platform_sso": ACCEPT_PLATFORM_SSO,
        "method": "POST JSON { token }",
        "isolated_from_atlas": True,
        "note": "Use POST with landing handoff token to enter the synth-data demo",
    }


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    return {"users": len(seed.USERS), "skus": len(seed.SKUS), "employees": len(seed.EMPLOYEES)}


# --- Auth (frontend contract) -------------------------------------------------

@app.post("/api/stock/auth/login")
def login(body: LoginBody) -> dict[str, Any]:
    user = seed.USERS.get(body.email.lower())
    if not user or user["password"] != body.password:
        raise HTTPException(status_code=401, detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    return {"access_token": create_token(user["email"]), "token_type": "bearer"}


@app.post("/api/stock/auth/register")
def register(body: RegisterBody) -> dict[str, Any]:
    email = body.email.lower()
    if email in seed.USERS:
        raise HTTPException(status_code=400, detail="อีเมลนี้มีอยู่แล้ว")
    seed.USERS[email] = {
        "email": email,
        "password": body.password,
        "full_name": body.full_name,
        "shop_name": body.shop_name,
        "role": "owner",
    }
    return {"access_token": create_token(email), "token_type": "bearer"}


@app.get("/api/stock/auth/me")
def me(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return public_user(user)


# --- Platform / org -----------------------------------------------------------

@app.get("/api/platform/tenant")
def platform_tenant(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return seed.TENANT


@app.get("/api/platform/tiers")
def platform_tiers(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.TIERS


@app.get("/api/platform/branches")
def platform_branches(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.BRANCHES


@app.post("/api/platform/branches")
async def create_branch(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    item = {
        "id": f"branch-{uuid.uuid4().hex[:8]}",
        "name": body.get("name") or "New branch",
        "code": body.get("code") or "NEW",
        "city": body.get("city") or "Bangkok",
        "is_primary": False,
    }
    seed.BRANCHES.append(item)
    return item


@app.get("/api/organization/departments")
def org_departments(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.DEPARTMENTS


@app.get("/api/organization/members")
def org_members(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.MEMBERS


@app.get("/api/organization/members/{member_id}")
def org_member(member_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    for m in seed.MEMBERS:
        if m["id"] == member_id:
            return m
    raise HTTPException(status_code=404, detail="Not found")


@app.get("/api/organization/roles")
def org_roles(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return [
        {"id": "owner", "name": "Owner"},
        {"id": "finance", "name": "Finance"},
        {"id": "hr", "name": "HR"},
    ]


@app.get("/api/organization/permissions")
def org_permissions(_: dict[str, Any] = Depends(current_user)) -> list[str]:
    return ["read", "write", "approve", "admin"]


# --- Stock --------------------------------------------------------------------

@app.get("/api/stock/skus")
def stock_skus(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.SKUS


@app.get("/api/stock/warehouses")
def stock_warehouses(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.WAREHOUSES


@app.get("/api/stock/settings/shop")
def stock_shop(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {
        "name": seed.TENANT["name"],
        "country_code": "TH",
        "currency": "THB",
        "timezone": "Asia/Bangkok",
    }


@app.get("/api/stock/settings/members")
def stock_members(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.MEMBERS


@app.get("/api/stock/onboarding/checklist")
def stock_onboarding(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return seed.ONBOARDING


@app.get("/api/stock/barcodes/{code}")
def stock_barcode(code: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    for sku in seed.SKUS:
        if sku.get("barcode") == code or sku.get("sku") == code:
            return sku
    raise HTTPException(status_code=404, detail="Barcode not found")


@app.post("/api/stock/barcodes/scan")
async def stock_scan(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    code = str(body.get("code") or body.get("barcode") or "")
    for sku in seed.SKUS:
        if sku.get("barcode") == code or sku.get("sku") == code:
            return {"ok": True, "sku": sku}
    raise HTTPException(status_code=404, detail="Barcode not found")


# --- HR -----------------------------------------------------------------------

@app.get("/api/hr-platform/employees")
def hr_employees(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.EMPLOYEES


@app.get("/api/hr-platform/dashboard")
def hr_dashboard(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return seed.HR_DASHBOARD


@app.get("/api/hr-platform/leave")
def hr_leave(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.LEAVE_REQUESTS


@app.get("/api/hr-platform/leave/pending")
def hr_leave_pending(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.LEAVE_PENDING


@app.get("/api/hr-platform/payroll")
def hr_payroll(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return [{k: v for k, v in row.items() if k != "lines"} for row in seed.PAYROLL_RUNS]


@app.get("/api/hr-platform/payroll/{payroll_id}")
def hr_payroll_one(payroll_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    for row in seed.PAYROLL_RUNS:
        if row["id"] == payroll_id:
            return row
    raise HTTPException(status_code=404, detail="payroll_not_found")



@app.post("/api/hr-platform/payroll/run")
def hr_payroll_run(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"ok": True, "id": "pay-2026-09", "status": "calculated"}


@app.post("/api/hr-platform/payroll/{payroll_id}/submit-approval")
def hr_payroll_submit(payroll_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"ok": True, "id": payroll_id, "status": "pending_approval"}


@app.post("/api/hr-platform/attendance/{employee_id}")
def hr_clock_in(employee_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"ok": True, "employee_id": employee_id, "event": "clock_in"}


@app.post("/api/hr-platform/attendance/clock-out")
async def hr_clock_out(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    return {"ok": True, "event": "clock_out", "employee_id": body.get("employee_id")}


# --- Finance / procurement / marketing / resto --------------------------------

@app.get("/api/finance/countries")
def finance_countries(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.FINANCE_COUNTRIES


@app.get("/api/finance/plan")
def finance_plan(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"plan_tier": seed.TENANT["plan_tier"], "country_code": "TH", "currency": "THB"}


@app.get("/api/finance/payroll-journal-template")
def finance_payroll_template(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {
        "country": "TH",
        "lines": [
            {"account": "5100", "name": "Salary expense", "side": "debit"},
            {"account": "2100", "name": "Accrued payroll", "side": "credit"},
        ],
    }


@app.get("/api/finance/demo/production-flow")
def finance_demo_flow(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {
        "steps": [
            {"name": "ขาย", "status": "ok"},
            {"name": "รับเงิน", "status": "ok"},
            {"name": "ลงบัญชี", "status": "ok"},
        ],
        "demo": True,
    }


@app.get("/api/procurement/pr")
def procurement_pr(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.PROCUREMENT_PRS


@app.post("/api/procurement/pr/{pr_id}/status")
async def procurement_pr_status(
    pr_id: str, request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    for pr in seed.PROCUREMENT_PRS:
        if pr["id"] == pr_id:
            pr["status"] = body.get("status") or pr["status"]
            return pr
    raise HTTPException(status_code=404, detail="PR not found")


@app.get("/api/marketing/campaigns/pre")
def marketing_pre(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.CAMPAIGNS_PRE


@app.get("/api/marketing/campaigns/post")
def marketing_post(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.CAMPAIGNS_POST


@app.get("/api/marketing/legs/resto/health")
def resto_mkt_health(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"ok": True, "leg": "resto", "demo": True}


@app.get("/api/marketing/legs/resto/platforms")
def resto_platforms(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return [{"id": "grab", "name": "GrabFood", "connected": False}]


@app.get("/api/marketing/legs/resto/policies")
def resto_policies(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return [{"id": "pol-1", "name": "Default guest reply", "enabled": True}]


@app.get("/api/marketing/legs/resto/guest-interactions/interaction-types")
def resto_interaction_types(_: dict[str, Any] = Depends(current_user)) -> list[str]:
    return ["complaint", "compliment", "refund_request"]


@app.get("/api/marketing/legs/resto/guest-interactions/runs")
def resto_interaction_runs(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return []


@app.post("/api/marketing/legs/resto/guest-interactions/handle")
async def resto_handle(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    return {"ok": True, "draft": "ขอบคุณสำหรับความคิดเห็น (ข้อความจำลอง)", "input": body}


@app.get("/api/resto/menus")
def resto_menus(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.MENUS


@app.get("/api/resto/menus/{menu_id}")
def resto_menu(menu_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    for menu in seed.MENUS:
        if menu["id"] == menu_id:
            return menu
    raise HTTPException(status_code=404, detail="Menu not found")


@app.get("/api/resto/menus/{menu_id}/cost-preview")
def resto_menu_cost(menu_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"menu_id": menu_id, "food_cost_pct": 32.5, "demo": True}


@app.get("/api/resto/ingredients")
def resto_ingredients(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.INGREDIENTS


@app.get("/api/resto/ingredients/{ing_id}")
def resto_ingredient(ing_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    for item in seed.INGREDIENTS:
        if item["id"] == ing_id:
            return item
    raise HTTPException(status_code=404, detail="Not found")


@app.get("/api/resto/catalog")
def resto_catalog(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"menus": seed.MENUS, "ingredients": seed.INGREDIENTS}


@app.get("/api/resto/ml/models")
@app.get("/api/resto/ml/training-runs")
@app.get("/api/resto/ml/trends")
@app.get("/api/resto/ml/insights")
@app.get("/api/resto/ml/benchmark")
@app.get("/api/resto/ml/context-compare")
@app.get("/api/resto/ml/federated")
def resto_ml_stub(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"items": [], "demo": True, "message": "ML endpoints return simulated empty results"}


@app.post("/api/resto/ml/train")
def resto_ml_train(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"ok": True, "status": "queued", "demo": True}


@app.post("/api/resto/stock/manual-receive")
async def resto_manual_receive(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    return {"ok": True, "received": body, "demo": True}


@app.post("/api/resto/events/platform-order/")
async def resto_platform_order(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    return {"ok": True, "event": "platform-order", "payload": body, "demo": True}


# --- Documents / CFO / enterprise / workflows ---------------------------------

@app.get("/api/documents/health")
def documents_health(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"ok": True, "ocr": "mock", "demo": True}


@app.get("/api/documents/scans")
def documents_scans(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return [
        {
            "id": "scan-1",
            "filename": "invoice-demo.pdf",
            "status": "parsed",
            "vendor": "Demo Supplier Co.",
            "total": 5500,
        }
    ]


@app.get("/api/documents/scans/{scan_id}")
def documents_scan(scan_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {
        "id": scan_id,
        "filename": "invoice-demo.pdf",
        "status": "parsed",
        "vendor": "Demo Supplier Co.",
        "total": 5500,
        "lines": [{"desc": "น้ำดื่ม", "amount": 5500}],
    }


@app.post("/api/documents/scan")
async def documents_scan_upload(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"id": f"scan-{uuid.uuid4().hex[:8]}", "status": "parsed", "demo": True}


@app.post("/api/documents/scans/{scan_id}/create-pr")
def documents_create_pr(scan_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"ok": True, "pr_id": "pr-1003", "from_scan": scan_id}


@app.get("/api/accounting-docs/types")
def accounting_types(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.ACCOUNTING_TYPES


@app.get("/api/accounting-docs/templates")
def accounting_templates(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.ACCOUNTING_TEMPLATES


@app.get("/api/accounting-docs/documents")
def accounting_documents(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.ACCOUNTING_DOCUMENTS


@app.get("/api/finance/invoices")
def finance_invoices(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.INVOICES


@app.get("/api/finance/statements/income")
def finance_income(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.INCOME_STATEMENTS


@app.get("/api/finance/statements/balance-sheet")
def finance_balance(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return seed.BALANCE_SHEET


@app.get("/api/procurement/po")
def procurement_po(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.PURCHASE_ORDERS


@app.get("/api/stock/alerts")
def stock_alerts(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return seed.STOCK_ALERTS


@app.get("/api/demo/scenarios")
def demo_scenarios(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return seed.DEMO_SCENARIOS


@app.get("/api/demo/company")
def demo_company(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return seed.COMPANY


@app.post("/api/demo/reset")
def demo_reset(
    request: Request,
    _: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    """Reload ThaiTrade synth seed in-memory (shared sandbox tidy-up)."""
    expected = os.getenv("DEMO_RESET_KEY", "demo-reset")
    key = request.headers.get("X-Demo-Reset-Key", "")
    if key != expected:
        raise HTTPException(status_code=403, detail="reset_forbidden")
    counts = seed.reset_seed()
    return {"ok": True, "reset": True, "counts": counts}


@app.get("/api/cfo/health")
def cfo_health(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"ok": True, "athena": False, "demo": True}


@app.get("/api/cfo/brief")
def cfo_brief(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    overdue = len([i for i in seed.INVOICES if i.get("status") == "overdue"])
    return {
        "summary": (
            f"ThaiTrade Demo: มีใบแจ้งหนี้ค้างชำระ {overdue} รายการ, "
            f"SKU ใกล้จุดสั่งซื้อ {len(seed.STOCK_ALERTS.get('low_stock', []))} รายการ — ข้อมูลจำลองสำหรับทดสอบ"
        ),
        "demo": True,
        "scenarios": seed.DEMO_SCENARIOS.get("headline", []),
    }


@app.post("/api/cfo/query")
async def cfo_query(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    return {
        "answer": "นี่คือคำตอบจำลองจาก CFO demo (ไม่ได้เชื่อม Athena จริง)",
        "question": body.get("question") or body.get("q"),
        "demo": True,
    }


@app.get("/api/enterprise/sso/config")
def enterprise_sso(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {
        "enabled": False,
        "demo": True,
        "platform_sso": ACCEPT_PLATFORM_SSO,
        "isolated_from_atlas": True,
        "synth_data_only": True,
        "note": "Trial sandbox JWT only — not ATLAS SSO",
    }


@app.get("/api/enterprise/rules")
def enterprise_rules(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return []


@app.get("/api/enterprise/custom-fields/definitions")
def enterprise_cf(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return []


@app.get("/api/enterprise/audit/events")
def enterprise_audit(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return [
        {
            "id": "aud-1",
            "action": "login",
            "actor": seed.DEMO_EMAIL,
            "at": "2026-09-06T10:00:00Z",
        }
    ]


@app.get("/api/workflows/inbox")
def workflows_inbox(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return seed.WORKFLOW_INBOX


@app.get("/api/workflows/definitions")
def workflows_definitions(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return [{"id": "wf-def-1", "name": "PR Approval", "active": True}]


@app.get("/api/workflows/requests")
def workflows_requests(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.WORKFLOW_INBOX["items"]


@app.post("/api/workflows/requests/{req_id}/approve")
def workflows_approve(req_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"ok": True, "id": req_id, "status": "approved"}


@app.post("/api/workflows/requests/{req_id}/reject")
def workflows_reject(req_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"ok": True, "id": req_id, "status": "rejected"}


# --- Catch-all mock for remaining /api routes ---------------------------------

@app.api_route("/api/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def api_fallback(full_path: str, request: Request) -> JSONResponse:
    # Unauthenticated health-ish paths already covered; require auth for the rest.
    auth = request.headers.get("authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        current_user(auth)
    except HTTPException:
        raise
    if request.method == "GET":
        return JSONResponse({"items": [], "demo": True, "path": f"/api/{full_path}"})
    body: Any = None
    try:
        body = await request.json()
    except Exception:
        body = None
    return JSONResponse(
        {"ok": True, "demo": True, "path": f"/api/{full_path}", "echo": body}
    )


# --- Frontend monolith --------------------------------------------------------

def _mount_frontend() -> None:
    if not SERVE_FRONTEND:
        return
    dist = FRONTEND_DIST_DIR
    if not dist.is_dir():
        return
    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str) -> FileResponse:
        # Do not shadow API/health
        candidate = dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        index = dist / "index.html"
        if not index.is_file():
            raise HTTPException(status_code=404, detail="Frontend not found")
        # Keep HTML uncached so iframe picks up the latest bootstrap.
        # Do NOT send Clear-Site-Data: it wipes localStorage/sessionStorage on
        # every document load and fights the auto-login bootstrap (blank iframe).
        return FileResponse(
            index,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )


_mount_frontend()
