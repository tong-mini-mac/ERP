# ERP vs ERP-Demo isolation

## Rule

| System | Repo / deploy | Auth | Data |
|--------|---------------|------|------|
| **ERP (production / ATLAS)** | separate company stack (`admin.inz.lol` / atlas Railway) | production JWT + IN Z SSO | real tenant DB |
| **ERP-Demo** | this repo `tong-mini-mac/ERP` | local sandbox JWT only (`iss=erp-demo`) | in-memory seed |

They must **not** share:

- JWT / SSO secrets
- databases
- product-handoff sessions
- entitlement grants that auto-open the other system

## This repo (ERP-Demo) guarantees

- `PRODUCT_MODE=erp-demo` (startup fails otherwise)
- `ACCEPT_INZ_SSO=false` (startup fails if enabled)
- `/api/auth/inz-sso` and `/api/auth/product-handoff` return **409**
- `/health` reports `isolated_from_production_erp: true`
- Sandbox login: `demo@erp.demo` / `demo-erp-2026`

## Required landing changes (`tong-mini-mac/in-z-landing`)

Agent token for this Cloud run cannot push that repo. Apply manually:

### 1) Stop SSO handoff for `erp-demo`

In `lib/sso-handoff.ts` / `productBaseUrl()`:

- Keep `erp` → production ATLAS URL
- For `erp-demo`, either **omit** from the SSO map or return `null` so `/api/auth/product-handoff` returns `501`

Demo hub already iframes the raw demo URL — that is correct. Do **not** append `?inz_sso=...` for ERP-Demo.

### 2) Product launcher

In `components/ProductLauncher.tsx` (or equivalent):

- Opening **ERP-Demo** → `window.open(demoUrl)` / iframe raw URL only
- Opening **ERP / ATLAS** → existing product-handoff SSO path only

### 3) Copy

Keep demo catalog text explicit, e.g.:

- TH: `Universal ERP พร้อมข้อมูลจำลอง — แยกจาก ATLAS บริษัท (admin.inz.lol) และไม่ใช้บัญชี Platform ร่วม`
- EN: `Simulated Universal ERP — isolated from company ATLAS; not linked to Platform SSO`

### 4) Secrets on Railway

| Deploy | Env |
|--------|-----|
| ERP-Demo | own `JWT_SECRET`, never set production `INZ_SSO_SECRET` / `ERP_SPECIAL_LOGIN_KEY` |
| ATLAS | own secrets; never point `ERP_DEMO_URL` commerce fulfillment into demo DB |

## Verify

```bash
curl -s https://<erp-demo-host>/health
# expect: isolated_from_production_erp=true, accept_inz_sso=false

curl -s -X POST https://<erp-demo-host>/api/auth/inz-sso
# expect: HTTP 409 erp_demo_isolated
```
