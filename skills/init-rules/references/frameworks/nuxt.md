# Nuxt 3 (Tier 3)

Meta-framework for Vue. For Vue component idioms (`<script setup>`, composables,
`ref` vs `reactive`) see `./vue.md`; for Pinia stores see
`../packages/frontend/pinia.md`. Balance policy: a consistent existing pattern
wins unless it is a security/correctness/performance defect.

## Rules

- **Lean on file-based routing and auto-imports.** Pages in `pages/` map to
  routes; components, composables (`composables/`), and Nuxt/Vue APIs are
  auto-imported. Do not hand-wire a router or add manual imports for things Nuxt
  already provides.
- **Fetch with `useFetch`/`useAsyncData`, dedupe.** Use them for SSR-aware data
  loading with a stable `key` so the payload transfers to the client instead of
  re-fetching. Plain `$fetch` in `setup` without these causes double fetching
  (once on server, once on client).
- **Server routes live in `server/`.** Put API/backend logic in
  `server/api/**` (Nitro), not in components. Secret-holding work belongs here.
- **Choose the render mode deliberately.** SSR (default) for dynamic + SEO, SSG
  (`nuxt generate`) for static content, SPA only when there is no server. Set it
  per-route via `routeRules` when the app is mixed.
- **Never leak server secrets.** `runtimeConfig.public` ships to the browser;
  top-level `runtimeConfig` keys stay server-only. Keep tokens out of `public`.

## ❌ Bad — private key placed under `public`, exposed to the client

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    public: { apiSecret: process.env.API_SECRET },  // shipped in the client bundle!
  },
});
```

## ✅ Good — secret stays server-only, used in a server route

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    apiSecret: process.env.API_SECRET,          // server-only
    public: { apiBase: '/api' },                // safe to expose
  },
});
// server/api/report.get.ts
export default defineEventHandler(() => {
  const { apiSecret } = useRuntimeConfig();     // available only on the server
  return $fetch('https://provider/report', { headers: { authorization: apiSecret } });
});
```

## Research hook

On activation, `WebSearch` `"nuxt <installed-version> best practices"`. Prefer
official docs (nuxt.com), then cross-check a second reputable source. Codify
findings with provenance `researched` + source URL + retrieval date. Never block
on a failed search — fall back to the rules above.

Source: best-practice · Confidence: medium
