# Fix DemoHub double-login (apply on GitHub.com — agent has no push to landing)

Repo: `tong-mini-mac/in-z-landing`  
File: `components/DemoHub.tsx`

## Why

`/demo` iframes `offer.href` raw. Account page already uses `/api/auth/product-handoff`.
ERP-Demo needs the handoff URL (`?inz_sso=...`) or iframe auto-login after ERP deploy.

## Minimal patch

1. Import session helper (same as ProductLauncher):

```tsx
import { getSession } from "@/lib/auth-session";
```

2. Add state for iframe src:

```tsx
const [frameSrc, setFrameSrc] = useState<string | null>(null);
```

3. When `active` changes, resolve ERP-Demo via handoff:

```tsx
useEffect(() => {
  let cancelled = false;
  async function resolve() {
    if (!active) {
      setFrameSrc(null);
      return;
    }
    if (active.id !== "erp-demo") {
      setFrameSrc(active.href);
      return;
    }
    const session = getSession();
    if (!session?.user?.email) {
      window.location.href = "/auth?next=/demo";
      return;
    }
    try {
      const res = await fetch("/api/auth/product-handoff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: session.user.email,
          productId: "erp-demo",
          role: session.user.role || "trial",
          kind: session.user.kind || "complimentary",
          allowedProducts: session.user.allowedProducts || ["erp-demo"],
        }),
      });
      const data = await res.json();
      if (!cancelled) setFrameSrc(res.ok && data.url ? data.url : active.href);
    } catch {
      if (!cancelled) setFrameSrc(active.href);
    }
  }
  void resolve();
  return () => {
    cancelled = true;
  };
}, [active]);
```

4. Replace iframe `src={active.href}` with `src={frameSrc || active.href}`.

## Env (Railway ERP-Demo)

- `ACCEPT_PLATFORM_SSO=true`
- `PLATFORM_SSO_SECRET` or `INZ_SSO_SECRET` = same value as landing `INZ_SSO_SECRET`

## Fallback without landing change

After ERP deploy of `frontend/dist/index.html`, iframe on inz.lol/demo auto-logs in as
`demo@erp.demo` (synth data only). Handoff is still preferred.
