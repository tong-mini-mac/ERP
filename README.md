# Universal ERP Demo

**This repository is ERP-Demo only** — a customer trial sandbox with **synthetic data** for IN Z (`inz.lol/demo`).

It is **not** company ATLAS / live ERP. ATLAS stays untouched. Demo never shares ATLAS DB or production tenants.

Private repo: [tong-mini-mac/ERP](https://github.com/tong-mini-mac/ERP)

App version: **1.0.0-demo**. Default finance locale: **TH**.

### How login works

1. Customer signs in **once** on `inz.lol` (platform account / MY ACCOUNT)
2. Landing opens ERP-Demo with `?inz_sso=...`
3. Demo exchanges that token for a **local sandbox JWT** and enters the app
4. No second login form; data is synthetic only

### Isolation from ATLAS

| | ERP-Demo (this repo) | ATLAS (company backend) |
|--|----------------------|-------------------------|
| Purpose | Customer trial / synth data | Live company ERP |
| Touched by this repo? | Yes | **No — leave alone** |
| Auth | Platform SSO → local demo JWT | Separate production auth |
| Database | In-memory seed | Production DB |
| Shared session/DB with the other? | **No** | **No** |

Landing iframe handoff notes: [`docs/LANDING_SINGLE_LOGIN.md`](docs/LANDING_SINGLE_LOGIN.md).  
Isolation details: [`docs/ERP_DEMO_ISOLATION.md`](docs/ERP_DEMO_ISOLATION.md).

---

## Stack

| Layer | Tech |
|-------|------|
| API | FastAPI (`erp.main:app`), Pydantic Settings |
| Auth | JWT (`/auth/register`, `/auth/login`, `/auth/me`) |
| Primary DB | PostgreSQL (`DATABASE_URL`) |
| Cache / jobs | Redis |
| Module DBs | SQLite under `data/` (HR, procurement, finance audit) |
| Migrations | Alembic (`backend/alembic`) |
| Frontend | React 19 + Vite 6 + React Router 7 (`erp-frontend` 0.1.0) |
| Billing | Stripe (plan tiers: Solo / Micro / Small / Medium / Large) |
| CFO | Athena (`athena/`) — knowledge vault + economic engine |

Use **Python >= 3.11** and **Node.js 18+**.

---

## Layout

```
ERP/
├── .env.example              # copy to .env — do not commit secrets
├── backend/
│   └── erp/                  # FastAPI app package
│       ├── modules/          # finance, hr, marketing, procurement, stock
│       └── ...
├── frontend/                 # Vite SPA (dev: :5173)
│   ├── dist/                 # production build
│   └── .env.example          # VITE_API_BASE_URL
├── athena/                   # optional CFO brain (vendored SAG + ai_cfo)
└── data/                     # local sqlite / uploads (*.db gitignored)
```

---

## Modules

| Area | What it covers |
|------|----------------|
| **Core** | Multi-tenant platform, feature gating, departments/RBAC, approval workflows, Stripe billing |
| **Finance** | GL / localization (TH default), payroll journal templates, audit |
| **HR** | Employees, attendance, leave, payroll |
| **Stock** | SKU, barcode, lots |
| **Procurement** | PR → vendor reply → PO / receive; optional LLM |
| **Marketing** | Campaigns + vertical legs: resto, clinic, ecommerce, trading, beauty |
| **Resto** | Menus, recipe cost, dine-in, table sessions, delivery platforms |
| **Clinic** | Appointments, pets, mode (pet/dental) |
| **Beauty** | Clients, rooms, appointments, media upload |
| **Ecommerce** | Catalog, channel orders, marketplace ingest |
| **Trading** | Customers, price lists, quotations, payment reminders |
| **Documents** | OCR (GCP Vision / Azure Document Intelligence) |
| **CFO** | `/api/cfo/*` via Athena |
| **Feeds** | MOC / BOT open data + internal KPIs |

Frontend routes in the current Vite build include `/`, `/login`, `/finance`, `/hr`, `/stock`, `/procurement`, `/marketing`, `/resto-menu`, `/cfo`, `/documents`, `/accounting-docs`, `/organization`, `/platform`, `/enterprise`, `/workflows`.

---

## Setup

```powershell
cd D:\Myworkspace\ERP   # or clone path
copy .env.example .env
copy frontend\.env.example frontend\.env
```

Minimum `.env` for local API:

```
DATABASE_URL=postgresql+psycopg://erp:erp@localhost:5432/erp
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=<at-least-32-chars>
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ATHENA_MACRO_REFRESH_ON_START=0
```

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn pydantic pydantic-settings psycopg redis alembic python-dotenv
alembic upgrade head
```

Frontend:

```powershell
cd frontend
npm install
```

Do not commit `.env`. `.gitignore` excludes `.env`, `__pycache__`, `node_modules`, and `*.db`.

---

## Run

**API:**

```powershell
cd backend
uvicorn erp.main:app --reload --port 8000
```

- Health: `GET /health`
- Metrics: `GET /metrics`
- API routers under `/api`

**Frontend:**

```powershell
cd frontend
npm run dev
```

Open `http://localhost:5173`. Leave `VITE_API_BASE_URL` empty for same-origin / monolith.

**Monolith** (FastAPI serves `frontend/dist`):

```
SERVE_FRONTEND=true
FRONTEND_DIST_DIR=/app/static/dist
```

---

## Athena CFO

`athena/` vendors the Athena platform (knowledge = `vendor/sag`, economic = `vendor/centralize` / `ai_cfo`). ERP exposes it at `/api/cfo/*` when API keys are set.

```powershell
pip install -e athena/vendor/centralize
pip install -e athena
```

Set `GEMINI_API_KEY` and/or `OPENAI_API_KEY` in the root `.env`. Keep `ATHENA_MACRO_REFRESH_ON_START=0` unless you want a macro pull on process start.

---

## Tests

```powershell
cd backend
python -m pytest tests -v
```

---

## Environment (short)

Full template: `.env.example`.

| Variable | Role |
|----------|------|
| `DATABASE_URL` | Postgres (stock, auth, tenant) |
| `REDIS_URL` | Redis |
| `ERP_HR_DATABASE_PATH` | HR sqlite |
| `JWT_SECRET` | Auth signing key |
| `STRIPE_*` / `STRIPE_PRICE_*` | Billing + webhook |
| `GCP_VISION_ENABLED` / Azure DI | Document OCR |
| `BOT_API_TOKEN` / `MOC_API_BASE_URL` | Vertical feeds |
| `SERVE_FRONTEND` | Serve Vite dist from FastAPI |

---

## Sync notes

- This repo is **private ERP-Demo** (synth-data trial). Do not touch ATLAS.
- Platform SSO from `inz.lol` is allowed for single login; ATLAS DB/tenants stay disconnected.
- Landing must open ERP-Demo via product-handoff (`?inz_sso=`). See `docs/LANDING_SINGLE_LOGIN.md`.
- `data/*.db` and secrets stay local. Share only `PLATFORM_SSO_SECRET` / `INZ_SSO_SECRET` with landing.
- Clone / pull from `https://github.com/tong-mini-mac/ERP` to keep local and GitHub aligned.
