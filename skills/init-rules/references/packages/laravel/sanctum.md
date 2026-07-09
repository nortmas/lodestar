# Laravel Sanctum (Tier 2)

laravel/sanctum v4 idioms only. For auth, middleware, and CORS see
`../../frameworks/laravel.md` and `../../concerns/security.md`. Balance policy: a
consistent existing pattern wins unless it is a security/correctness/performance
defect — unscoped or long-lived tokens are a **critical** security defect and are
overridden with a migration note.

## Pick the right mode — do not mix them per endpoint
- **First-party SPA / mobile web on the same top domain:** cookie-based session
  auth. Requests hit the `sanctum/csrf-cookie` endpoint first, send the XSRF
  header, and go through the `EnsureFrontendRequestsAreStateful` middleware. Set
  `SANCTUM_STATEFUL_DOMAINS` correctly — a wrong value silently drops to token
  mode.
- **Third-party / server-to-server / mobile native:** personal access tokens.

## Every token must be scoped with abilities
- Issue tokens with explicit abilities:
  `$user->createToken('name', ['orders:read'])`. Guard each route/action with
  `tokenCan('orders:read')` or the `abilities:` / `ability:` middleware. A token
  minted with `['*']` (or no abilities) is a full-account credential — flag it.
- Set expirations (`config/sanctum.php` → `expiration`, or per-token
  `expiresAt`). Non-expiring tokens are a standing liability.

## Middleware & lifecycle
- Protect API routes with `auth:sanctum`. On logout, revoke: delete the current
  token (`currentAccessToken()->delete()`) or all tokens; a session logout that
  leaves API tokens alive is not a logout.

❌ Bad — full-power, non-expiring token, no ability checks
```php
$token = $user->createToken('api')->plainTextToken;   // ability ['*'], never expires

Route::middleware('auth:sanctum')->get('/orders', fn () => Order::all());
// any valid token can read every order
```
✅ Good — scoped, expiring token, ability-gated route
```php
$token = $user->createToken('mobile', ['orders:read'], now()->addDays(30))
    ->plainTextToken;

Route::middleware(['auth:sanctum', 'abilities:orders:read'])
    ->get('/orders', fn (Request $r) => $r->user()->orders);

// logout revokes the credential
$request->user()->currentAccessToken()->delete();
```

Source: best-practice · Confidence: high
