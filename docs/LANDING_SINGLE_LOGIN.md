# Landing change: single login into ERP-Demo

ERP-Demo accepts platform SSO from `inz.lol` and maps the user into **synthetic sandbox data**.
It does **not** connect to ATLAS.

## Required change in `tong-mini-mac/in-z-landing`

`components/DemoHub.tsx` currently iframes the raw ERP-Demo URL, so a user who already
signed in on the landing still sees a second login form.

When opening **ERP-Demo**, if the user has a platform session, call product-handoff and
use the returned URL (includes `?inz_sso=...`).

### Suggested logic

```tsx
async function resolveDemoSrc(offer: DemoOffer, sessionEmail: string | null) {
  if (offer.id !== "erp-demo" || !sessionEmail) {
    return offer.href; // or redirect to /auth?next=/demo for erp-demo
  }
  const res = await fetch("/api/auth/product-handoff", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: sessionEmail,
      productId: "erp-demo",
      role: "trial",
      kind: "complimentary",
      allowedProducts: ["erp-demo"],
    }),
  });
  const data = await res.json();
  if (res.ok && data.url) return data.url;
  return offer.href;
}
```

Then set `<iframe src={resolvedSrc} />`.

If there is no platform session, send the user to `/auth?next=/demo` first
(so they log in once on the main site).

### Env

Landing and ERP-Demo must share the same HMAC secret:

- Landing: `INZ_SSO_SECRET`
- ERP-Demo: `PLATFORM_SSO_SECRET` or `INZ_SSO_SECRET`

Do **not** reuse ATLAS production DB credentials for this.

## ERP-Demo behavior after handoff

1. `index.html` reads `?inz_sso=`
2. `POST /api/auth/inz-sso` → local demo JWT
3. Stores `erp_access_token` and enters the app
4. Data remains synthetic seed data only
