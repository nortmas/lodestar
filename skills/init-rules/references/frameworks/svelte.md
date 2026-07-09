# Svelte / SvelteKit (Tier 3)

Detect the installed major and match it: Svelte 5 introduces **runes**; Svelte 4
uses stores + reactive `$:`. Do not port a codebase to runes wholesale — follow
what the repo already uses. Balance policy: a consistent existing pattern wins
unless it is a security/correctness/performance defect.

## Rules

- **Reactivity — match the version.** Svelte 5: `$state` for reactive state,
  `$derived` for computed values, `$effect` for side effects (sparingly, like a
  React effect — for syncing with externals, not for deriving data). Svelte 4:
  writable/derived stores and `$:` reactive statements.
- **Load data in `load` functions.** Fetch in `+page.ts`/`+page.server.ts`
  (and layout equivalents), not ad hoc inside components. Return data; let the
  page render it.
- **Server vs universal `load`.** `+page.server.ts` runs only on the server —
  use it for DB access and anything touching secrets. `+page.ts` (universal) runs
  on both server and client, so **never read secrets there**; its return value is
  serialized to the browser.
- **Follow `+page` / `+layout` conventions.** Routes are folders under `routes/`;
  shared shell goes in `+layout`, endpoints in `+server.ts`. Keep components
  small and focused — split when a component grows past one clear responsibility.

## ❌ Bad — secret read in a universal load (ships to client)

```ts
// +page.ts — runs in the browser too; API_SECRET is exposed
export const load = async ({ fetch }) => {
  const res = await fetch(`/ext?key=${import.meta.env.API_SECRET}`);
  return { data: await res.json() };
};
```

## ✅ Good — secret confined to a server load

```ts
// +page.server.ts — server-only
import { API_SECRET } from '$env/static/private';
export const load = async ({ fetch }) => {
  const res = await fetch('https://ext/report', { headers: { authorization: API_SECRET } });
  return { data: await res.json() };   // only the result crosses to the client
};
```

## Research hook

On activation, `WebSearch` `"svelte <installed-version> best practices"` (and
`"sveltekit <version>"` if present). Prefer official docs (svelte.dev), then
cross-check a second reputable source. Codify findings with provenance
`researched` + source URL + retrieval date. Never block on a failed search —
fall back to the rules above.

Source: best-practice · Confidence: medium
