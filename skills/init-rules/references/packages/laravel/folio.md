# Laravel Folio (Tier 3)

Folio-specific guidance only. For controllers-vs-pages layering, Services/Actions,
and validation see `../../frameworks/laravel.md`. Balance policy: a consistent
existing pattern wins unless it is a security/correctness/performance defect.

## Rules
- **Page-based routing.** Files in the Folio mount (`resources/views/pages/`) map
  to routes by filename: `index.blade.php` → `/`, `users/[id].blade.php` →
  `/users/{id}`, `[...slug].blade.php` → catch-all. Follow the naming convention
  rather than adding parallel `Route::` definitions for the same URLs.
- **Middleware & names via hooks.** Attach middleware and route names through the
  `name()` / `middleware()` render hooks at the top of the page (or the
  `Folio::path()->middleware([...])` config), not by wrapping pages in ad-hoc
  route groups elsewhere.
- **Keep page files thin.** A page validates and renders; push any real work to a
  Service/Action (typically inside a Livewire/Volt component the page hosts). A
  Folio page is not a controller — do not grow query building or business rules in
  the Blade file.

❌ Bad — logic and raw query inside the page
```php
<?php
$users = DB::table('users')->where('active', 1)->get();   // query + no shaping in the view
?>
<x-layout>@foreach ($users as $u) {{ $u->email }} @endforeach</x-layout>
```
✅ Good — declare middleware, delegate the work
```php
<?php
use function Laravel\Folio\{name, middleware};
middleware(['auth']);
name('users.index');
?>
<livewire:users-list />   {{-- component/Service owns fetching + shaping --}}
```

## Research hook
On activation, `WebSearch` `"laravel folio <installed-version> best practices"`.
Prefer the official docs (laravel.com/docs/folio), then cross-check one reputable
source. Confirm the routing/naming and render-hook API for the installed major and
codify findings with provenance `researched` + source URL + retrieval date. Never
block on a failed search — fall back to the rules above.

Source: best-practice · Confidence: medium
