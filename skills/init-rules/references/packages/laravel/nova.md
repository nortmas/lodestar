# Laravel Nova (Tier 3)

Nova-specific guidance only. For layering, Services/Actions, policies, and N+1 see
`../../frameworks/laravel.md`. Balance policy: a consistent existing pattern wins
unless it is a security/correctness/performance defect.

## Rules
- **One Resource per model** under `app/Nova/`; `fields()` is presentation wiring,
  not a place for business logic.
- **Authorize via policies.** Nova reads the model's Laravel policy for
  view/create/update/delete and relation attach — put access rules there, not in
  ad-hoc `canSee()` closures duplicated across fields.
- **Avoid heavy computed fields.** A `Text::make()->resolveUsing(fn () => ...)`
  that queries per row runs once per index row → N+1. Aggregate in the query or
  use `Number`/computed columns backed by `withCount`/`withSum`.
- **Actions / Filters / Lenses** are the extension points: destructive or
  multi-step operations belong in Nova **Actions** that delegate to a Service; use
  **Filters** for query scoping and **Lenses** for alternate list queries — do not
  fork Resources to achieve them.
- Keep orchestration in Services/Actions; the Action's `handle()` should call one.

❌ Bad — per-row query in a field
```php
Text::make('Orders', fn ($u) => $u->orders()->count());   // N+1 across the index
```
✅ Good — aggregate in the index query
```php
public static function indexQuery(NovaRequest $r, $query) { return $query->withCount('orders'); }
Number::make('Orders', 'orders_count');
```

## Research hook
On activation, `WebSearch` `"laravel nova <installed-version> best practices"`.
Prefer the official docs (nova.laravel.com), then cross-check one reputable
source. Confirm field/action/filter APIs for the installed major (v4 vs v5) and
codify findings with provenance `researched` + source URL + retrieval date. Never
block on a failed search — fall back to the rules above.

Source: best-practice · Confidence: medium
