# Performance (Tier 2 — CRITICAL carve-out)

Most items here are ordinary trade-offs, but three are critical defects (called out below). For those, a consistent existing bad pattern does NOT win the balance policy: override with best practice and emit a migration note. Never codify the defect.

## Measure before optimizing
Profile to find the actual hot path before changing anything. Guessing wastes effort and often pessimizes the common case for a rare one. Optimize what the profiler and production metrics point at, not what feels slow.

```php
// ❌ Bad: micro-optimizing a loop that runs 3 times, ignoring the 400ms query beside it
// ✅ Good: profile first, then fix the dominant cost
```

## Eliminate N+1 queries — CRITICAL
Loading a collection then querying per row is a guaranteed N+1. Eager-load the relation. A confirmed N+1 on a request path is a critical defect: override and add a migration note, never enshrine it.

```php
// ❌ Bad: 1 + N queries
foreach (Order::all() as $o) { echo $o->customer->name; }

// ✅ Good: 2 queries, eager loaded
foreach (Order::with('customer')->get() as $o) { echo $o->customer->name; }
```

## Cache with a clear invalidation story
Use the right layer — request-scoped memo, application cache (Redis), HTTP/CDN cache. Never add a cache without deciding how and when it is invalidated; a stale cache is a correctness bug wearing a speed costume. Set TTLs; key by all inputs that affect the result.

## Paginate large sets — CRITICAL
Never load an unbounded collection into memory or return it whole over the wire. Missing pagination on a growing table is a critical defect (memory blowup + slow response): override and migration-note it. Use cursor pagination for large or deep sets.

```php
// ❌ Bad: unbounded memory — fails as the table grows
return User::all();

// ✅ Good: bounded
return User::paginate(50);
```

## Keep blocking I/O off hot paths
Do not perform synchronous network calls, heavy queries, or filesystem waits inside request handlers or tight loops. Push them to queues/background jobs, batch them, or cache them. Unbounded memory growth on a hot path is likewise a critical defect.

## Carve-out reminder
Guaranteed N+1, unbounded/unpaginated result sets, and unbounded memory on hot paths are critical — flag and fix even if pervasive in the codebase, and never write a rule that matches the bad pattern. Other performance choices follow the balance policy and defer to existing convention.

Source: best-practice · Confidence: high
