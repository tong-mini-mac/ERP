# Landing: admin@inz.lol unlimited on every product

Repo: `tong-mini-mac/in-z-landing`  
Issue: https://github.com/tong-mini-mac/in-z-landing/issues/2  
Patch file: [`patches/in-z-landing-admin-unlimited.patch`](./patches/in-z-landing-admin-unlimited.patch)

## Why

`admin@inz.lol` already signs in with `role: admin` + `unlimited: true`, but Account → **Your products** only listed the 5 commercial SKUs (`COMMERCIAL_PRODUCT_IDS`). ERP-Demo / PRISM / internal tools were missing, and `/api/auth/product-handoff` rejected `erp-demo` (checkout allowlist only).

## Apply (on a machine with push to landing)

```bash
cd in-z-landing
git apply path/to/in-z-landing-admin-unlimited.patch
# or copy the four file edits below
git commit -am "feat(auth): admin unlimited launcher for all products"
git push
# deploy landing
```

Then **sign out and sign in again** as `admin@inz.lol` so the session gets the full `allowedProducts` list.

## Files changed

1. `lib/products.ts` — `ADMIN_LAUNCHER_PRODUCT_IDS`, `HANDOFF_PRODUCT_IDS`; admin `productsForAccess` returns the full launcher list
2. `app/api/auth/product-handoff/route.ts` — allow SSO for handoff ids (incl. `erp-demo`); unlimited token carries full admin product list
3. `app/api/auth/special-signin/route.ts` — return full `allowedProducts` for demo admin
4. `components/AuthForm.tsx` — persist admin `allowedProducts` in session (was dropped before)

## After deploy

Account should list: SynthComm, QA LAB, Music Demo, Content Creator, NetR, PRISM, ERP-Demo, AI-Marketing, Admin Portal, PRISM API, Universal ERP (ATLAS).  
OPEN uses unlimited handoff (`package: unlimited`) where SSO is wired; others fall back to raw URL (501).
