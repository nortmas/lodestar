# Vite (Tier 2)

Build-tool guidance for the installed major (Vite 5.x+). Pair with the framework
plugin: `@vitejs/plugin-vue` / `@vitejs/plugin-react` / `laravel-vite-plugin`.
For Tailwind's build integration see `./tailwind.md`. Balance policy: a
consistent existing pattern wins unless it is a security/correctness/performance
defect.

## Env vars: `VITE_` prefix, never leak secrets
- Only variables prefixed `VITE_` are exposed to client code via
  `import.meta.env`. Everything in the bundle ships to the browser, so a secret
  placed in a `VITE_` var (or hardcoded inline) is public. Keep API keys, tokens,
  and DB credentials server-side; the client calls your backend, which holds the
  secret.

```ts
// ❌ Bad: secret hardcoded / VITE_-prefixed — it ends up in the shipped bundle
const stripe = new Stripe('sk_live_abc123');                 // hardcoded secret
fetch(`/charge?key=${import.meta.env.VITE_STRIPE_SECRET}`);  // exposed to browser

// ✅ Good: only the publishable/public value is client-side; secret stays on server
const pk = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY;      // safe to expose
await fetch('/api/charge', { method: 'POST', body: JSON.stringify({ amount }) });
// the server route holds STRIPE_SECRET (no VITE_ prefix) and talks to Stripe
```

## Code-splitting with dynamic import
- Split large or rarely used chunks (routes, heavy libs, modals) with dynamic
  `import()` so the initial bundle stays small. Framework routers do this for
  lazy routes; reuse that mechanism rather than importing everything eagerly.

```ts
// ✅ Good: heavy editor loaded on demand, not in the entry chunk
const Editor = () => import('./components/RichEditor.vue');
```

## Aliases over brittle relative paths
- Configure `resolve.alias` (e.g. `@` → `src`) and keep it in sync with the
  TypeScript `paths` in `tsconfig`. Deep `../../../` chains break on every move.

## Reproducible builds and asset handling
- Commit the lockfile and pin the framework plugin so dev and CI resolve the same
  graph. Import assets through Vite (`import logo from './logo.svg'` or `?url`)
  so they are hashed, fingerprinted, and cache-busted — do not hand-write paths
  into `/public` for assets that should be processed.

Source: best-practice · Confidence: high
