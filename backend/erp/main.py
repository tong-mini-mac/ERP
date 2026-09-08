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
from datetime import date
from pathlib import Path
from typing import Any

import jwt
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from erp import demo_seed as seed
from erp import accounting_docs_demo as ac_docs
from erp import gl_posting

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
            "ingredients": len(getattr(seed, "INGREDIENTS", [])),
            "menus": len(getattr(seed, "MENUS", [])),
            "document_scans": len(getattr(seed, "DOCUMENT_SCANS", [])),
            "gl_entries": len(getattr(seed, "GL_ENTRIES", [])),
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
def stock_warehouses(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    # SPA reads `response.warehouses` (not a bare array).
    return {"warehouses": seed.WAREHOUSES}


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
def hr_employees(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    # SPA: `const data = await employees(); setList(data.items || [])`
    items = []
    for e in seed.EMPLOYEES:
        items.append(
            {
                **e,
                "name": e.get("name") or e.get("full_name"),
                "employment_type": str(e.get("employment_type") or "full-time").replace("_", "-"),
            }
        )
    return {"items": items}


@app.get("/api/hr-platform/dashboard")
def hr_dashboard(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return seed.HR_DASHBOARD


@app.get("/api/hr-platform/leave")
def hr_leave(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.LEAVE_REQUESTS


@app.get("/api/hr-platform/leave/pending")
def hr_leave_pending(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    items = []
    for row in seed.LEAVE_PENDING:
        items.append(
            {
                **row,
                "emp_name": row.get("emp_name") or row.get("employee"),
                "leave_type": row.get("leave_type") or row.get("type"),
                "start_date": row.get("start_date") or "",
                "end_date": row.get("end_date") or "",
            }
        )
    return {"items": items}


@app.get("/api/hr-platform/payroll")
def hr_payroll(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    items = []
    for row in seed.PAYROLL_RUNS:
        period = str(row.get("period") or "")
        year, month = row.get("year"), row.get("month")
        if (year is None or month is None) and "-" in period:
            try:
                year_s, month_s = period.split("-", 1)
                year, month = int(year_s), int(month_s)
            except ValueError:
                pass
        items.append(
            {
                "id": row.get("id"),
                "period": period,
                "year": year,
                "month": month,
                "status": row.get("status"),
                "total": row.get("total"),
                "total_net": row.get("total_net", row.get("total")),
                "currency": row.get("currency") or "THB",
            }
        )
    return {"items": items}


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
def marketing_pre(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"items": seed.CAMPAIGNS_PRE}


@app.post("/api/marketing/campaigns/pre")
async def marketing_pre_run(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    return {
        "ok": True,
        "demo": True,
        "phase": "pre",
        "summary": (
            f"Pre-campaign plan for {body.get('product_name') or 'product'}: "
            f"audience={body.get('target_audience')}, goal={body.get('campaign_goal')}, "
            f"budget={body.get('budget') or 0}."
        ),
        "recommendations": [
            "Lead with social proof on Facebook + LINE OA",
            "Test 3 creatives in week 1",
            "Keep CTA to store visit / QR",
        ],
        "echo": body,
    }


@app.get("/api/marketing/campaigns/present")
def marketing_present_list(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"items": getattr(seed, "CAMPAIGNS_PRESENT", [])}


@app.post("/api/marketing/campaigns/present")
async def marketing_present_run(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    live = getattr(seed, "CAMPAIGNS_PRESENT", [])[:5]
    return {
        "ok": True,
        "demo": True,
        "phase": "present",
        "summary": "Live campaign pulse (mock): CTR and spend for the last 7 days.",
        "live_campaigns": live,
        "alerts": [
            "Budget pacing 92% — consider pause on low-CTR creative",
            "LINE OA reply SLA within target",
        ],
        "echo": body,
    }


@app.get("/api/marketing/campaigns/post")
def marketing_post(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"items": seed.CAMPAIGNS_POST}


@app.post("/api/marketing/campaigns/post")
async def marketing_post_run(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    return {
        "ok": True,
        "demo": True,
        "phase": "post",
        "summary": "Post-campaign review (mock): sentiment and follow-up tasks.",
        "followups": [
            "Thank responders on LINE",
            "Retarget clickers who did not convert",
            "Share NPS snapshot with store managers",
        ],
        "echo": body,
    }


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


@app.post("/api/resto/ingredients")
async def resto_create_ingredient(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    item = {
        "id": f"ing-{uuid.uuid4().hex[:6]}",
        "name": body.get("name") or "New ingredient",
        "unit": body.get("unit") or "kg",
        "on_hand": float(body.get("on_hand") or 0),
        "yield_pct": float(body.get("yield_pct") or 100),
        "purchase_price": float(body.get("purchase_price") or 0),
        "erp_sku_id": body.get("erp_sku_id") or "",
        "erp_warehouse_id": body.get("erp_warehouse_id") or "",
        "notes": body.get("notes") or "",
    }
    seed.INGREDIENTS.insert(0, item)
    return item


@app.get("/api/resto/ingredients/{ing_id}")
def resto_ingredient(ing_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    for item in seed.INGREDIENTS:
        if item["id"] == ing_id:
            return item
    raise HTTPException(status_code=404, detail="Not found")


@app.get("/api/resto/catalog")
def resto_catalog(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    # Ingredients tab crashes if `skus` / `warehouses` are missing (`x.skus.map`).
    return {
        "menus": seed.MENUS,
        "ingredients": seed.INGREDIENTS,
        "skus": seed.SKUS,
        "warehouses": seed.WAREHOUSES,
    }


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
    return {
        "ok": True,
        "ocr": "mock",
        "vision_available": False,
        "manual_entry": True,
        "manual_entry_note": "Failover when scanner/OCR is broken — not a replacement for scanning.",
        "demo": True,
    }


@app.get("/api/documents/scans")
def documents_scans(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    # SPA: `list(); setItems(data.items || [])`
    return {"items": list(getattr(seed, "DOCUMENT_SCANS", []))}


@app.get("/api/documents/scans/{scan_id}")
def documents_scan(scan_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    for row in getattr(seed, "DOCUMENT_SCANS", []):
        if row["id"] == scan_id:
            return row
    raise HTTPException(status_code=404, detail="scan_not_found")


@app.post("/api/documents/scan")
async def documents_scan_upload(
    file: UploadFile | None = File(None),
    _: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    # Multipart upload is mocked OCR — still create a usable history row.
    filename = (file.filename if file else None) or "uploaded-document.pdf"
    if file is not None:
        await file.read()  # consume body; demo does not persist binary
    row = {
        "id": f"scan-{uuid.uuid4().hex[:8]}",
        "filename": filename,
        "doc_type": "invoice",
        "status": "parsed",
        "vendor": "Uploaded Vendor",
        "total": 0,
        "currency": "THB",
        "source": "upload",
        "lines": [{"desc": f"Parsed from {filename}", "qty": 1, "amount": 0}],
        "demo": True,
    }
    getattr(seed, "DOCUMENT_SCANS").insert(0, row)
    return row


@app.post("/api/documents/manual")
async def documents_manual_entry(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    """Manual document entry when scanner/OCR is unavailable."""
    body = await request.json()
    row = {
        "id": f"scan-{uuid.uuid4().hex[:8]}",
        "filename": body.get("filename") or "manual-entry",
        "doc_type": body.get("doc_type") or "invoice",
        "status": "parsed",
        "vendor": body.get("vendor") or "Manual vendor",
        "vendor_tax_id": body.get("vendor_tax_id") or "",
        "invoice_number": body.get("invoice_number") or "",
        "total": float(body.get("total") or 0),
        "currency": body.get("currency") or "THB",
        "source": "manual",
        "notes": body.get("notes") or "",
        "lines": body.get("lines")
        or [
            {
                "desc": body.get("line_desc") or "Manual line",
                "qty": float(body.get("qty") or 1),
                "amount": float(body.get("total") or 0),
            }
        ],
        "demo": True,
    }
    getattr(seed, "DOCUMENT_SCANS").insert(0, row)
    return row


@app.post("/api/documents/scans/{scan_id}/create-pr")
def documents_create_pr(scan_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"ok": True, "pr_id": "pr-1003", "from_scan": scan_id}


@app.get("/api/accounting-docs/types")
def accounting_types(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return ac_docs.list_types()


@app.get("/api/accounting-docs/templates")
def accounting_templates(
    doc_type: str | None = None,
    _: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    return ac_docs.list_templates(doc_type)


@app.post("/api/accounting-docs/templates")
async def accounting_create_template(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    return ac_docs.create_template(body if isinstance(body, dict) else {})


@app.get("/api/accounting-docs/templates/{template_id}")
def accounting_get_template(
    template_id: str, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    try:
        return ac_docs.get_template(template_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="template_not_found") from None


@app.post("/api/accounting-docs/templates/{template_id}/preview")
async def accounting_preview(
    template_id: str, request: Request, _: dict[str, Any] = Depends(current_user)
) -> HTMLResponse:
    try:
        body = await request.json()
    except Exception:
        body = {}
    payload = body.get("payload") if isinstance(body, dict) else None
    try:
        html = ac_docs.render_preview_html(template_id, payload if isinstance(payload, dict) else None)
    except KeyError:
        raise HTTPException(status_code=404, detail="template_not_found") from None
    return HTMLResponse(content=html)


@app.post("/api/accounting-docs/templates/{template_id}/bot/chat")
async def accounting_bot_chat(
    template_id: str, request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    message = str((body or {}).get("message") or "")
    try:
        return ac_docs.bot_chat(template_id, message)
    except KeyError:
        raise HTTPException(status_code=404, detail="template_not_found") from None


@app.get("/api/accounting-docs/documents")
def accounting_documents(
    doc_type: str | None = None,
    _: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    return ac_docs.list_documents(doc_type)


@app.post("/api/accounting-docs/documents")
async def accounting_issue_document(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    return ac_docs.issue_document(body if isinstance(body, dict) else {})


@app.get("/api/accounting-docs/documents/{doc_id}/html")
def accounting_doc_html(doc_id: str, _: dict[str, Any] = Depends(current_user)) -> HTMLResponse:
    docs = ac_docs.list_documents()["items"]
    doc = next((d for d in docs if d["id"] == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="document_not_found")
    tpl_id = doc.get("template_id") or ac_docs.list_templates(doc.get("doc_type"))["items"][0]["id"]
    html = ac_docs.render_preview_html(tpl_id, doc.get("payload"))
    return HTMLResponse(content=html)


@app.get("/api/accounting-docs/documents/{doc_id}/pdf")
def accounting_doc_pdf(doc_id: str, _: dict[str, Any] = Depends(current_user)) -> HTMLResponse:
    # Demo: return printable HTML (browser can Save as PDF).
    return accounting_doc_html(doc_id, _)


@app.get("/api/finance/invoices")
def finance_invoices(_: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return seed.INVOICES


@app.get("/api/finance/journal")
def finance_journal(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    """สมุดรายวัน — every Dr/Cr journal entry (GL_ENTRIES)."""
    items = sorted(
        list(getattr(seed, "GL_ENTRIES", [])),
        key=lambda e: (e.get("date") or "", e.get("id") or ""),
        reverse=True,
    )
    return {"items": items, "count": len(items)}


@app.get("/api/finance/journal/{entry_id}")
def finance_journal_one(
    entry_id: str, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    for e in getattr(seed, "GL_ENTRIES", []):
        if e.get("id") == entry_id:
            return e
    raise HTTPException(status_code=404, detail="journal_not_found")


@app.get("/api/finance/gl")
@app.get("/api/finance/ledger")
def finance_gl(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    """บัญชีแยกประเภท — General Ledger by account."""
    return gl_posting.general_ledger(
        list(getattr(seed, "GL_ENTRIES", [])),
        list(getattr(seed, "CHART_OF_ACCOUNTS", [])),
    )


@app.get("/api/finance/trial-balance")
def finance_trial_balance(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return gl_posting.trial_balance(
        list(getattr(seed, "GL_ENTRIES", [])),
        list(getattr(seed, "CHART_OF_ACCOUNTS", [])),
    )


@app.get("/api/finance/accounts")
def finance_accounts(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"items": list(getattr(seed, "CHART_OF_ACCOUNTS", []))}


@app.post("/api/finance/invoices")
async def finance_create_invoice(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    """Create invoice and auto-post issue journal (Dr AR / Cr Revenue + VAT)."""
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="invalid_body")
    n = len(seed.INVOICES) + 1
    inv_id = f"inv-{n:03d}"
    while any(i.get("id") == inv_id for i in seed.INVOICES):
        n += 1
        inv_id = f"inv-{n:03d}"
    subtotal = float(body.get("subtotal") or body.get("amount") or 0)
    vat = float(body.get("vat") if body.get("vat") is not None else round(subtotal * 0.07, 2))
    total = float(body.get("total") if body.get("total") is not None else round(subtotal + vat, 2))
    today = body.get("issue_date") or date.today().isoformat()
    customer_name = body.get("customer_name") or "Walk-in customer"
    invoice = {
        "id": inv_id,
        "number": body.get("number") or f"INV-TT-2026-{n:03d}",
        "title": body.get("number") or f"INV-TT-2026-{n:03d}",
        "type": "tax_invoice",
        "customer_id": body.get("customer_id") or "",
        "customer_name": customer_name,
        "issue_date": today,
        "due_date": body.get("due_date") or today,
        "status": "pending",
        "subtotal": subtotal,
        "vat": vat,
        "total": total,
        "currency": "THB",
        "days_overdue": 0,
    }
    seed.INVOICES.append(invoice)
    je = gl_posting.post_invoice_issue(seed.GL_ENTRIES, invoice)
    return {"ok": True, "invoice": invoice, "journal_entry": je}


@app.post("/api/finance/invoices/{invoice_id}/pay")
async def finance_pay_invoice(
    invoice_id: str,
    request: Request,
    _: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    """Mark invoice paid, create receipt, auto-post payment JE (Dr Cash / Cr AR)."""
    invoice = next((i for i in seed.INVOICES if i.get("id") == invoice_id), None)
    if not invoice:
        raise HTTPException(status_code=404, detail="invoice_not_found")
    body: dict[str, Any] = {}
    try:
        raw = await request.json()
        if isinstance(raw, dict):
            body = raw
    except Exception:
        body = {}

    # Ensure issue JE exists first (pending invoices may already have it from seed).
    issue_je = gl_posting.post_invoice_issue(seed.GL_ENTRIES, invoice)

    if invoice.get("status") == "paid" and invoice.get("gl_payment_id"):
        pay_je = gl_posting.find_by_source(seed.GL_ENTRIES, "invoice_payment", invoice_id)
        return {
            "ok": True,
            "invoice": invoice,
            "journal_issue": issue_je,
            "journal_payment": pay_je,
            "already_paid": True,
        }

    paid_date = body.get("paid_date") or date.today().isoformat()
    r_n = len(seed.RECEIPTS) + 1
    rcpt_id = f"rcpt-{r_n:02d}"
    while any(r.get("id") == rcpt_id for r in seed.RECEIPTS):
        r_n += 1
        rcpt_id = f"rcpt-{r_n:02d}"
    receipt = {
        "id": rcpt_id,
        "number": f"RC-2026-{r_n:03d}",
        "invoice_id": invoice_id,
        "amount": float(body.get("amount") or invoice.get("total") or 0),
        "currency": "THB",
        "paid_date": paid_date,
    }
    seed.RECEIPTS.append(receipt)
    invoice["status"] = "paid"
    invoice["days_overdue"] = 0
    pay_je = gl_posting.post_invoice_payment(
        seed.GL_ENTRIES, invoice, receipt=receipt, paid_date=paid_date
    )
    return {
        "ok": True,
        "invoice": invoice,
        "receipt": receipt,
        "journal_issue": issue_je,
        "journal_payment": pay_je,
    }


@app.post("/api/finance/invoices/{invoice_id}/post")
def finance_post_invoice(
    invoice_id: str, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    """Explicitly post issue journal for an existing invoice (idempotent)."""
    invoice = next((i for i in seed.INVOICES if i.get("id") == invoice_id), None)
    if not invoice:
        raise HTTPException(status_code=404, detail="invoice_not_found")
    je = gl_posting.post_invoice_issue(seed.GL_ENTRIES, invoice)
    return {"ok": True, "invoice": invoice, "journal_entry": je}


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
    ac_docs.reset_runtime()
    return {"ok": True, "reset": True, "counts": counts}


@app.get("/api/cfo/health")
def cfo_health(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"ok": True, "athena": False, "demo": True}


@app.get("/api/cfo/brief")
@app.post("/api/cfo/brief")
async def cfo_brief(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = {}
    overdue = len([i for i in seed.INVOICES if i.get("status") == "overdue"])
    return {
        "summary": (
            f"ThaiTrade Demo: {overdue} overdue invoices, "
            f"{len(seed.STOCK_ALERTS.get('low_stock', []))} SKUs near reorder. "
            "Synthetic data for portfolio review."
        ),
        "answer": (
            "Executive brief (demo): prioritize collections on overdue tax invoices, "
            "raise PRs for low-stock SKUs, and keep resto food-cost under 35%."
        ),
        "demo": True,
        "scenarios": seed.DEMO_SCENARIOS.get("headline", []),
        "echo": body,
    }


@app.post("/api/cfo/query")
async def cfo_query(
    request: Request, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    body = await request.json()
    question = body.get("query") or body.get("question") or body.get("q") or ""
    sales = body.get("sales_history") or []
    if isinstance(sales, str):
        sales = [s.strip() for s in sales.split(",") if s.strip()]
    scope = body.get("scope") or "ALL"
    role = body.get("role") or "CFO"
    department = body.get("department") or "Finance"
    return {
        "answer": (
            f"Demo CFO answer for [{role} / {department} / scope={scope}]: "
            f"Based on sales series {sales or 'n/a'}, "
            f"cash collection and food-cost control are the top levers. "
            f"Question: {question}"
        ),
        "question": question,
        "scope": scope,
        "role": role,
        "department": department,
        "demo": True,
        "athena": False,
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
