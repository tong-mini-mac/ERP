# ERP-Demo isolation (from ATLAS)

## Rule

ERP-Demo and ATLAS are different systems.

| System | Role | This repo |
|--------|------|-----------|
| **ERP-Demo** | Customer trial with synthetic data | Yes — owned here |
| **ATLAS** | Company / live ERP backend for IN Z | **Do not touch** |

They must **not** share:

- databases
- production JWT secrets
- production tenant data

They **may** share only a **platform handoff HMAC** with `inz.lol` landing so customers
sign in once on the main site and enter the demo without a second login form.

That handoff is **not** ATLAS access. It only proves the visitor already signed in on
`inz.lol`, then ERP-Demo issues its own local sandbox JWT.

## ERP-Demo guarantees

- `PRODUCT_MODE=erp-demo`
- `ACCEPT_PLATFORM_SSO=true` → accepts landing `?inz_sso=` / `POST /api/auth/inz-sso`
- No outbound calls to ATLAS
- Synthetic seed data only
- Fallback local login still available for engineers: `demo@erp.demo` / `demo-erp-2026`

## Landing requirement

See `docs/LANDING_SINGLE_LOGIN.md` — DemoHub must open ERP-Demo via product-handoff URL
when the platform session exists.
