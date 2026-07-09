# Laravel Passport (Tier 3)

Passport-specific guidance only. For auth, middleware, and token abilities see
`../../frameworks/laravel.md`, `../../concerns/security.md`, and the Sanctum
reference. Balance policy: a consistent existing pattern wins unless it is a
security/correctness/performance defect — auth defects are **critical**.

## Rules
- **Only when you need a full OAuth2 server.** Passport is an OAuth2 provider
  (authorization codes, third-party clients, refresh tokens). For first-party
  SPAs, mobile apps, and simple API tokens, use **Sanctum** instead — Passport's
  key/client machinery is unjustified overhead there.
- **Scope every token.** Define scopes and enforce them per route with the
  `scope`/`scopes` middleware or `$user->tokenCan('...')`. A token issued without
  scopes is a full-account credential — flag it.
- **Short lifetimes + refresh.** Set access-token and refresh-token TTLs
  explicitly (`Passport::tokensExpireIn(...)`, `refreshTokensExpireIn(...)`).
  Do not ship long-lived access tokens.
- **Grant per client type.** Use `client_credentials` for machine-to-machine and
  `authorization_code` (with PKCE for public clients) for user-facing flows;
  avoid the deprecated password grant.

❌ Bad — unscoped token from a needlessly-installed OAuth server
```php
$token = $user->createToken('app')->accessToken;   // no scopes, default long TTL
```
✅ Good — scoped, enforced
```php
$token = $user->createToken('app', ['orders:read'])->accessToken;
Route::middleware(['auth:api', 'scope:orders:read'])->get('/orders', /* ... */);
```

## Research hook
On activation, `WebSearch` `"laravel passport <installed-version> best practices"`.
Prefer the official docs (laravel.com/docs/passport), then cross-check one
reputable source. Confirm the grant types, PKCE, and scope-enforcement API for the
installed major (v12/v13 differ from older releases) and codify findings with
provenance `researched` + source URL + retrieval date. Never block on a failed
search — fall back to the rules above.

Source: best-practice · Confidence: medium
