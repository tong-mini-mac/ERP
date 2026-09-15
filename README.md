# Universal ERP Demo

**This repository is ERP-Demo only** — a customer trial sandbox with **synthetic data** for IN Z (`inz.lol/demo`).

It is **not** company ATLAS / live ERP. ATLAS stays untouched. Demo never shares ATLAS DB, production tenants, or production JWT secrets.

| | |
|--|--|
| **Public** repo | [tong-mini-mac/ERP](https://github.com/tong-mini-mac/ERP) |
| Live sandbox | https://erp-demo-production-9ab8.up.railway.app |
| Demo hub | https://inz.lol/demo → **ERP-Demo** |
| App version | **1.0.0-demo** |
| Default finance locale | **TH** |

---

## What customers see today

1. Open **inz.lol/demo** → choose **ERP-Demo** (iframe), or open the live URL / **OPEN IN NEW TAB**
2. Enter the sandbox **without a second Platform login wall**
3. Explore modules on **synthetic** data only

### UX notes (demo)
- Stock barcode: scanner is primary; if hardware is broken, type code + Enter (failover)
- Documents: Scan & extract is primary; **Manual entry** is the failover when scanner/OCR is down
- Marketing includes **Present-campaign** (mock live pulse); Clinic/Beauty/Ecommerce/Trading remain pending
- Admin forms avoid raw JSON where possible (payload fields accept plain notes)
- UI English overlay + **Home · inz.lol** link (SPA ships as built `frontend/dist`)


| Path | When | Result |
|------|------|--------|
| Platform SSO `?inz_sso=...` | Landing product-handoff after inz.lol sign-in | Local sandbox JWT for that email |
| Auto demo login | Iframe / public trial with no SSO token | Signs in as `demo@erp.demo` |
| Manual demo login | Engineers / fallback | `demo@erp.demo` / `demo-erp-2026` |

Landing handoff notes: [`docs/LANDING_SINGLE_LOGIN.md`](docs/LANDING_SINGLE_LOGIN.md).  
Admin Account launcher (all products): [`docs/LANDING_ADMIN_UNLIMITED.md`](docs/LANDING_ADMIN_UNLIMITED.md) (landing repo change).

### Isolation from ATLAS

| | ERP-Demo (this repo) | ATLAS (company backend) |
|--|----------------------|-------------------------|
| Purpose | Customer trial / synth data | Live company ERP |
| Touched by this repo? | Yes | **No — leave alone** |
| Auth | Platform SSO → local demo JWT, or auto `demo@erp.demo` | Separate production auth |
| Database | Demo seed / in-memory style sandbox | Production DB |
| Shared session/DB with the other? | **No** | **No** |

Details: [`docs/ERP_DEMO_ISOLATION.md`](docs/ERP_DEMO_ISOLATION.md).

### Product decision: open portfolio sandbox (no time limit)

Audience is **portfolio reviewers** (CTO / Senior AI who got a job-application link) — not paying customers. Volume is low.

The GitHub repository is **public** (`tong-mini-mac/ERP`) so reviewers can browse source and seed data freely. Live demo data remains synthetic only and stays isolated from ATLAS.

| Choice | Why |
|--------|-----|
| **Public source** | Portfolio transparency — clone/browse without a private invite |
| **No time limit** | Reviewers look ~10–15 minutes; a trial clock adds complexity without value |
| **Shared sandbox** | One synth tenant; cost is the server you already run |
| **No signup required** | Auto / shared login `demo@erp.demo` — open from `/demo` or the live URL |
| **No metered trial system** | Do not block shipping on per-user timers or entitlements |

Story-driven seed data: **ThaiTrade Solutions Co., Ltd.** — see [`docs/SYNTHETIC_DATA.md`](docs/SYNTHETIC_DATA.md) and `backend/erp/seeds/` (catalog ≥50 customers/vendors/SKUs; procurement mock ≥50 per set).  
Optional later: nightly `POST /api/demo/reset` (header `X-Demo-Reset-Key`) — not a ship blocker.

---

## Stack

| Layer | Tech |
|-------|------|
| API | FastAPI (`erp.main:app`), Pydantic Settings |
| Auth | Local JWT + optional platform SSO handoff |
| Primary DB | PostgreSQL (`DATABASE_URL`) when configured; demo can run seeded without ATLAS |
| Cache / jobs | Redis (optional for demo) |
| Module DBs | SQLite under `data/` (HR, procurement, finance audit) |
| Frontend | React + Vite (`frontend/`, shipped `frontend/dist/`) |
| Deploy | Railway service **ERP-Demo** only (never ATLAS) |

Use **Python >= 3.11**. Frontend dist is committed for monolith deploys.

---

## Layout

```
ERP/
├── .env.example
├── backend/erp/           # FastAPI app
├── frontend/              # Vite SPA + dist/
├── docs/                  # isolation + landing handoff notes
├── athena/                # optional CFO brain
└── data/                  # local sqlite / uploads (*.db gitignored)
```

---

## Modules (sandbox)

Finance, accounting docs, HR, Stock, **Procurement**, Marketing, Documents (OCR), CFO/Athena, Organization / Enterprise / Platform, Workflows — all against **demo data**.

### Procurement (จัดซื้อตามช่วงงบ)

Open **`/procurement`**. Every case is **scan-first** (work from scanned docs in-system); receipts / tax invoices / important originals can be **sent to accounting later** for tax filing.

| Band | Budget (THB) | Flow |
|------|--------------|------|
| **A · Petty cash** | ≤ 10,000 | Float **50,000**; max **10,000**/receipt · PR+TOR → buy → clear bills with accounting → month-end reconcile |
| **B · Mid** | > 10,000 and ≤ 100,000 | PR+TOR → online market-price research → ≥3 registered quotes (optional public board) → same award / PO / delivery / AP path as high |
| **C · High** | > 100,000 | Public board · AI award (TOR-fit + lowest) · manager approve · **PO** if &lt; 1M · **contract** if ≥ 1M · delivery → stock → AP |

Demo APIs (auth required):

| Endpoint | Purpose |
|----------|---------|
| `GET /api/procurement/flow/meta` | Thresholds + scan policy |
| `GET /api/procurement/mock-stats` | Volume counts (≥50 per mock set) |
| `GET/POST /api/procurement/documents…` | Scan registry + physical original follow-up |
| `GET/POST /api/procurement/petty-cash…` | Petty float, purchase, clearance, reconcile |
| `GET/POST /api/procurement/tenders…` | Mid/high tenders, bids, evaluate, award, PO/contract, delivery, invoices |

Seed volume (process start / `POST /api/demo/reset`): **≥50** vendors, tenders, board cards, petty purchases, clearances, reconciles, vendor invoices, accounting alerts, and **≥50 scanned docs per type** (PR, TOR, receipt, tax invoice, …). Walkthrough anchors: `tender-hv-001`, `tender-mid-001`, `petty-101`.

---

## Local setup

```bash
cp .env.example .env
python3 -m venv --upgrade-deps .venv
.venv/bin/pip install -r backend/requirements.txt
```

Minimum demo-oriented env:

```
PRODUCT_MODE=erp-demo
ACCEPT_PLATFORM_SSO=true
SERVE_FRONTEND=1
FRONTEND_DIST_DIR=frontend/dist
JWT_SECRET=<at-least-32-chars>
# Same HMAC as landing when testing SSO:
# PLATFORM_SSO_SECRET=...   # or INZ_SSO_SECRET
```

Run monolith:

```bash
export PYTHONPATH=backend
.venv/bin/uvicorn erp.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET /health` (reports `isolated_from_atlas`, `synth_data_only`, etc.)
- App: `http://127.0.0.1:8000/`

Cloud Agent install/start uses the same venv + uvicorn pattern on port **8000**.

---

## Deploy (Railway)

- GitHub Action `.github/workflows/deploy-railway.yml` deploys **only** service `ERP-Demo` on push to `main`
- `RAILWAY_TOKEN` must be a **Railway Project Token** (not account/workspace token)
- Do **not** deploy this repo to the company ATLAS / `admin.inz.lol` service

---

## Ops notes

- Do not send `Clear-Site-Data: storage` on HTML — it wipes the demo JWT and blanks the inz.lol iframe
- Keep `Cache-Control: no-cache` on `index.html` so iframe clients pick up auth bootstrap
- Share only `PLATFORM_SSO_SECRET` / `INZ_SSO_SECRET` with landing — never ATLAS DB URLs
- Engineer fallback: `demo@erp.demo` / `demo-erp-2026`
