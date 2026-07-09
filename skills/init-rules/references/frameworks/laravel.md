# Laravel (Tier 1 — deepest, authoritative)

Best-practice source when Laravel is detected. This is the richest layer: it drives most of the
generated rules for a Laravel repo. Encode framework-specific decisions; skip generic PHP (that's
in `../languages/php.md`) and generic OOP.

## Contents
- Request lifecycle & layering
- Controllers
- Validation (Form Requests)
- Business logic (Services / Actions)
- Eloquent & the database (N+1, scopes, raw SQL)
- API output (Resources)
- Queues & slow work
- Config & secrets
- Testing
- Migrations
- Boost coexistence

## Request lifecycle & layering
The canonical flow this layer recommends:
`Route → FormRequest (validate) → Controller (thin) → Service/Action (logic) → Resource (shape) → response`.
Business logic lives in **Services or Actions**, never in controllers or models. Models hold
relationships, scopes, casts, accessors — not workflow logic.

## Controllers
- **Thin.** A controller method validates (via injected FormRequest), delegates to one
  service/action, returns a Resource or redirect. Target ≤ ~15 lines per action.
- Prefer single-action controllers (`__invoke`) for non-CRUD endpoints.
- No query building, no business rules, no `DB::` in controllers.

❌ Bad
```php
public function store(Request $request)
{
    $data = $request->all();                          // no validation
    $order = Order::create($data);                    // mass-assignment risk
    Mail::to($order->user)->send(new OrderPlaced($order)); // logic in controller
    return response()->json($order);                  // no output shaping
}
```
✅ Good
```php
public function store(StoreOrderRequest $request, PlaceOrder $placeOrder): OrderResource
{
    $order = $placeOrder->handle($request->validated());
    return new OrderResource($order);
}
```

## Validation — Form Requests
- Validate in **FormRequest** classes, not inline in controllers. Authorize in `authorize()`.
- Reuse rules via rule objects/arrays; keep messages localizable.

## Business logic — Services / Actions
- One public entry point per Action (`handle()` / `__invoke()`); inject dependencies via
  constructor. Keep them framework-thin so they're unit-testable.
- Wrap multi-write operations in `DB::transaction()`.

## Eloquent & the database
- Prefer Eloquent relationships and **query scopes** over raw `DB::` queries in domain code.
- **N+1 is a performance defect (critical carve-out).** Eager-load relations accessed in loops
  with `with()`/`load()`. Never lazy-load per iteration. Consider `Model::preventLazyLoading()`
  in non-production.
- **Never interpolate input into raw SQL** — use bindings / the query builder. Raw string SQL is
  a security defect (SQL injection) and is never codified even if the repo does it consistently.
- Guard mass assignment: explicit `$fillable`, or `$guarded = []` only with validated input.
- Use chunking (`chunkById`) / pagination for large sets; never load unbounded collections.

❌ Bad
```php
foreach ($users as $user) {
    echo $user->orders->count();   // N+1: one query per user
}
$rows = DB::select("select * from users where name = '$name'"); // SQL injection
```
✅ Good
```php
$users = User::withCount('orders')->get();   // one query
$rows = DB::table('users')->where('name', $name)->get(); // bound parameter
```

## API output — Resources
- Shape every API response through an **API Resource** (or Resource Collection). Don't return
  raw models/arrays from API controllers — it leaks columns and couples the API to the schema.

## Queues & slow work
- Push slow work (mail, external API calls, image processing, exports) to **queued jobs**.
- Make jobs idempotent and give them sane `tries`/`backoff`. Don't do >~200ms of work inline on
  a web request if it can be queued.

## Config & secrets
- Read config via `config()`, never `env()` outside `config/*` files (config caching breaks
  `env()` elsewhere). Secrets live in `.env` / the secret store, never committed.

## Testing
- **Pest** is the default test tool for new Laravel projects (see `../packages/laravel/pest.md`).
  Use factories, `RefreshDatabase`, and feature tests for HTTP endpoints.
- Codify the repo's actual choice (PHPUnit vs Pest) rather than forcing Pest onto a PHPUnit repo.

## Migrations
- One change per migration; always reversible (`down()`), or explicitly irreversible with a note.
- Never edit a shipped migration — add a new one. Keep schema changes and data changes separate.

## Boost coexistence
If **`.ai/guidelines/`** exists, Laravel Boost is installed and already injects guidelines. Do
NOT duplicate what Boost covers — cross-reference it instead, and only generate rules for gaps
Boost doesn't address or for this project's specific divergences. Never write to `.ai/guidelines/`.

## Research hook
For version-specific features (new casts, `Context`, Folio, Precognition, Pennant, etc.),
`WebSearch` the official `laravel.com/docs/<version>` page and codify the idioms in use.

Source: best-practice · Confidence: high
