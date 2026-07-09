# Spatie Laravel-Permission (Tier 2)

spatie/laravel-permission v6 idioms only. For Gates/Policies, authorization, and
Eloquent see `../../frameworks/laravel.md` and `../../concerns/security.md`.
Balance policy: a consistent existing pattern wins unless it is a
security/correctness/performance defect — auth defects are **critical** and are
overridden with a migration note.

## Permissions are the unit of authority, roles are a bundle
- Assign **permissions** to roles; assign roles (or direct permissions) to users.
- In code, check **permissions**, never role names. Roles are an admin-facing
  grouping that changes over time; a scattered `hasRole('admin')` hard-codes a
  policy decision that should live in one place.
- Centralize checks in Gates/Policies (`can:...`), so business code asks
  "may this user do X?" not "is this user an admin?".

## Guard names must match
- Every role/permission is scoped to a **guard** (`web`, `api`, …). A permission
  created under `web` will not satisfy a check running under `api`. Create and
  check under the same guard, matching the route's auth guard.

## Cache
- Permissions are cached (`config/permission.php` → `cache.expiration_time`).
  After seeding or programmatically creating roles/permissions you **must** reset
  it: `app(\Spatie\Permission\PermissionRegistrar::class)->forgetCachedPermissions();`
  Stale cache is a common "permission exists but check fails" bug.

## Middleware
- Use the package middleware (`role:`, `permission:`, `role_or_permission:`) or
  Laravel's `can:` on routes. Prefer `permission:`/`can:` over `role:` for the
  same reason as above. Register aliases per the v6 install notes.

❌ Bad — hard-coded role string scattered through code
```php
if (auth()->user()->hasRole('admin')) {          // policy baked into a controller
    $invoice->void();
}
// ...and repeated in a Blade view, a job, a command — every one must change
// the day "manager" also needs to void.
```
✅ Good — permission-based check, centralized in a Policy/Gate
```php
// Seeder: role bundles permissions once.
$role->givePermissionTo('invoices.void');

// Policy owns the decision.
public function void(User $user, Invoice $invoice): bool
{
    return $user->can('invoices.void');   // guard-scoped, cached
}

// Callers just authorize the ability.
$this->authorize('void', $invoice);
```

Source: best-practice · Confidence: high
