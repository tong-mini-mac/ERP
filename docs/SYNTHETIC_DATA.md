# Synthetic data for ERP-Demo (ThaiTrade story)

## Decision: do **not** use SynthComm for this

| Tool | Good for | Bad for |
|------|----------|---------|
| **SynthComm** | Synthetic chat / CS dialogue corpora | Structured ERP masters (SKU, GL, PR/PO, payroll) |
| **Python seeds in this repo** | Typed records matching FastAPI demo APIs | Chat transcripts |

ERP-Demo needs **queryable business records** the UI already calls (`/api/stock/skus`, `/api/procurement/pr`, `/api/hr-platform/*`, `/api/accounting-docs/*`, …). Those belong in `backend/erp/seeds/` and are loaded by `demo_seed.py` at process start — not as JS blobs from SynthComm.

Accounting **document images/PDFs** can come later (OCR scans). First priority is structured seed JSON-like dicts in Python.

---

## Core principle

Data must tell a story: a **living fictional company** with history, problems, and actions for a reviewer to take — not random filler.

## Company identity

| Field | Value |
|-------|--------|
| Name | ThaiTrade Solutions Co., Ltd. |
| Tax ID | 0105566012345 |
| Address | 88/8 Silom Complex Bldg., Silom Rd., Bangkok 10500 |
| Branches | Head Office (Silom) + Asok Branch |
| Business | Import-export + retail (covers Finance / Stock / Procurement / HR) |
| Demo login | `demo@erp.demo` / `demo-erp-2026` (shared portfolio sandbox) |
| Industry legs | **Resto = demo**; Clinic / Beauty / Ecommerce / Trading = **pending** (`GET /api/demo/businesses`) |

## Live scenarios (must remain visible)

| Signal | Intent |
|--------|--------|
| 3 overdue tax invoices | Aging / collection follow-up |
| 5 SKUs at/near reorder | Create PR |
| Several PRs pending approval | Approval workflow |
| Absences / pending leave | HR attention |
| Partial PO receive | GRN / partial receive |

## Seed layout

```
backend/erp/seeds/
├── __init__.py          # build_all() → namespace used by demo_seed
├── _fake_data.py        # Thai names, tax ids, addresses
├── master.py            # company, branches, depts, CoA slice
├── people.py            # users, members, employees
├── catalog.py           # customers, vendors, SKUs
├── stock.py             # warehouses, lots, movements, alerts
├── finance.py           # invoices, receipts, GL highlights
├── procurement.py       # PR / PO
├── hr.py                # attendance, leave, payroll
└── scenarios.py         # dashboard alert summary
```

`demo_seed.py` re-exports the built namespace so existing `from erp import demo_seed as seed` keeps working.

## Reset strategy

- Process restart reloads seeds (in-memory).
- Optional: `POST /api/demo/reset` (demo secret) re-runs `build_all()` for a tidy sandbox without redeploy.
- Nightly cron is optional ops — **not** a ship blocker for portfolio demos.

## Product policy (aligned)

Open shared sandbox, **no timed trial**, no signup required for `/demo` iframe auto-login. See README.
