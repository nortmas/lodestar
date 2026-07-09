# Inertia (Tier 2)

Inertia + Laravel glue only. For controllers, Resources, validation, and layering
see `../../frameworks/laravel.md`; for the client side see the detected frontend
framework file (`../frontend/*` / `../../frameworks/react.md`). Balance policy: a
consistent existing pattern wins unless it is a security/correctness/performance
defect.

## Page props go through Resources
Never hand a raw Eloquent model or `->all()` array to `Inertia::render()` — it
leaks columns and hidden attributes straight to the browser. Shape props with an
API Resource, exactly as you would a JSON response.

❌ Bad — leaks the whole model and over-fetches
```php
return Inertia::render('Users/Show', [
    'user'  => User::with('orders')->find($id),   // password hash, tokens, all columns leak
    'stats' => Stat::all(),                        // fetched even though the page seldom shows it
]);
```
✅ Good — Resource-shaped, lazy where optional
```php
return Inertia::render('Users/Show', [
    'user'  => new UserResource($user),
    'stats' => Inertia::lazy(fn () => StatResource::collection($user->stats())), // only on partial reload
]);
```

## Share data sparingly
Put only truly global, small data in the `HandleInertiaRequests` middleware
(auth user summary, flash, locale). Everything page-specific belongs in that
page's props — shared props ride on **every** response.

## Partial reloads & over-fetching
- Use `only`/`except` partial reloads and `Inertia::lazy()` for expensive props so
  a table refresh does not re-query the whole page.
- Do not eager-load relations a page never renders.

## Forms & validation
- Use the client `useForm` helper; return standard Laravel validation errors from
  FormRequests — Inertia maps them into `form.errors` automatically. Do not invent
  a parallel JSON error shape.

## Typed page props
- Define a TypeScript type/interface per page's props and type the page component
  with it; keep it in sync with the Resource. Do not consume `props` as `any`.

Source: best-practice · Confidence: high
