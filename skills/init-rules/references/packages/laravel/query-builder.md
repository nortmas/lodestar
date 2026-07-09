# Spatie Laravel-Query-Builder (Tier 2)

spatie/laravel-query-builder v6 idioms only. For API Resources, pagination, and
N+1 see `../../concerns/api-design.md`, `../../concerns/performance.md`, and
`../../frameworks/laravel.md`. Balance policy: a consistent existing pattern wins
unless it is a security/correctness/performance defect — exposing unbounded query
surface is a **security** defect and is overridden with a migration note.

## Allowlist everything — deny by default
- Filters, sorts, and includes are attacker-controlled query strings. Declare an
  explicit allowlist with `allowedFilters()`, `allowedSorts()`,
  `allowedIncludes()`. Anything not listed must be rejected, not silently applied.
- Never expose raw column names 1:1 with the table. A caller who can sort/filter
  by any column can probe hidden data and force full-table scans. Map public
  filter names to intended columns/scopes.

## Includes — bound them
- `allowedIncludes()` maps to eager-loads; an unbounded or deeply nested include
  is an N+1 / over-fetch and a memory risk. List only the relations the endpoint
  serves, and paginate collections.

## Pair with API Resources
- QueryBuilder shapes the **query**; a JsonResource shapes the **response**. Do
  not return `->get()` straight to JSON — wrap in a Resource so output columns are
  intentional, independent of what was queryable.

❌ Bad — everything the client asks for
```php
// Sorts/filters by ANY column, includes ANY relation, returns raw models.
$users = QueryBuilder::for(User::class)
    ->allowedFilters(request('filter') ? array_keys(request('filter')) : [])
    ->allowedSorts(request('sort'))     // whatever arrives in the URL
    ->get();

return response()->json($users);        // leaks password_hash, remember_token, …
```
✅ Good — explicit allowlist, scoped filter, Resource output
```php
$users = QueryBuilder::for(User::class)
    ->allowedFilters([
        'name',
        AllowedFilter::scope('active'),          // maps to a query scope, not a raw column
    ])
    ->allowedSorts(['name', 'created_at'])       // fixed set
    ->allowedIncludes(['profile'])               // bounded eager-load
    ->paginate();

return UserResource::collection($users);         // output shape is intentional
```

Source: best-practice · Confidence: high
