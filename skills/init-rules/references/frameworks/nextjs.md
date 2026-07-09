# Next.js — App Router (Tier 3)

Meta-framework for React. For React component/hook idioms see `./react.md`.
Balance policy: a consistent existing pattern wins unless it is a
security/correctness/performance defect.

## Rules

- **Server Components by default.** Everything under `app/` is a Server Component
  unless it opts out. Add `"use client"` only when the file needs browser-only
  features — state/effects, event handlers, browser APIs. Push `"use client"` to
  the leaves; keep pages and layouts on the server.
- **Fetch data in Server Components.** Read the DB or call services directly in
  async server components — no client-side loading spinner round-trip, no
  exposing credentials. Use Route Handlers (`app/**/route.ts`) for actual HTTP
  endpoints, not as an internal data layer your own server components call.
- **Never expose secrets to client components.** Non-`NEXT_PUBLIC_` env vars are
  server-only; only `NEXT_PUBLIC_`-prefixed values reach the browser. Anything a
  client component references is in the client bundle.
- **Use `next/image`.** Prefer `<Image>` for automatic sizing, lazy loading, and
  format optimization over a raw `<img>`.
- **Be caching/revalidation aware.** Know whether a fetch is static or dynamic;
  set `revalidate` / `cache` intentionally and call `revalidatePath`/
  `revalidateTag` after mutations instead of assuming data refreshes itself.

## ❌ Bad — client component doing secret work

```tsx
'use client';
// API_KEY is inlined into the JS sent to every visitor.
export function Weather() {
  const [d, setD] = useState(null);
  useEffect(() => {
    fetch(`https://api.weather.com?key=${process.env.NEXT_PUBLIC_API_KEY}`)
      .then((r) => r.json()).then(setD);
  }, []);
  return <pre>{JSON.stringify(d)}</pre>;
}
```

## ✅ Good — server component holds the secret

```tsx
// app/weather/page.tsx — Server Component (no "use client")
export default async function Weather() {
  const res = await fetch(`https://api.weather.com?key=${process.env.API_KEY}`, {
    next: { revalidate: 600 },   // cached, revalidated every 10 min
  });
  const data = await res.json();
  return <pre>{JSON.stringify(data)}</pre>;   // API_KEY never leaves the server
}
```

## Research hook

On activation, `WebSearch` `"next.js <installed-version> best practices"`. Prefer
official docs (nextjs.org), then cross-check a second reputable source. Codify
findings with provenance `researched` + source URL + retrieval date. Never block
on a failed search — fall back to the rules above.

Source: best-practice · Confidence: medium
