# Laravel Telescope (Tier 3)

Telescope-specific guidance only. For environment config, gates, and logging see
`../../frameworks/laravel.md`, `../../concerns/security.md`, and
`../../concerns/debugging.md`. Balance policy: a consistent existing pattern wins
unless it is a security/correctness/performance defect — an exposed Telescope is a
**critical** data-exposure defect.

## Rules
- **Local / staging debugging tool.** Telescope records requests, queries,
  payloads, mail, and exceptions in full. Treat it as a dev instrument, not a
  production feature.
- **Never enable in production ungated.** If it must run in production, install
  with `--dev`-style gating: register it conditionally and lock the dashboard
  behind `Gate::define('viewTelescope', ...)` in `TelescopeServiceProvider`. The
  default gate only allows `local`; an open `/telescope` leaks request bodies,
  auth tokens, and query data.
- **Prune aggressively.** Schedule `telescope:prune` (e.g. hourly, keep 24–48h).
  Unpruned, the `telescope_entries` tables grow without bound and slow the app.
- **Filter what you record.** Use `Telescope::filter()` / `night mode` and disable
  noisy watchers in production to cut storage and sensitive capture.

❌ Bad — recording everywhere, dashboard open
```php
// TelescopeServiceProvider — default gate left as 'local' but app runs in prod,
// and Telescope is registered unconditionally in AppServiceProvider.
```
✅ Good — gated and environment-scoped
```php
protected function gate(): void
{
    Gate::define('viewTelescope', fn ($user) => $user->can('viewTelescope'));
}
// register the provider only outside production, or behind an explicit env flag
```

## Research hook
On activation, `WebSearch` `"laravel telescope <installed-version> best practices"`.
Prefer the official docs (laravel.com/docs/telescope), then cross-check one
reputable source. Confirm the gate/authorization, pruning command, and
production-install guidance for the installed major and codify findings with
provenance `researched` + source URL + retrieval date. Never block on a failed
search — fall back to the rules above.

Source: best-practice · Confidence: medium
