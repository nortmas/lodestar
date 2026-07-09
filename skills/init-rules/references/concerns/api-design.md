# API Design (Tier 2)

Guidance for HTTP/REST API shape and contract consistency.

## Resource naming: plural nouns, no verbs
Paths name resources, HTTP methods are the verbs. Use plural collection nouns and nest for relationships. Verbs in paths (`/getUser`, `/createOrder`) duplicate what the method already says.

```
❌ Bad:  POST /createOrder,  GET /order/get/42,  GET /listUserOrders?uid=7
✅ Good: POST /orders,       GET /orders/42,     GET /users/7/orders
```

## Version deliberately and consistently
Pick one scheme — URI (`/v1/orders`) or header (`Accept: application/vnd.api.v1+json`) — and apply it everywhere. Mixing schemes across endpoints is the defect. Bump the version for breaking changes; add fields additively within a version.

## One success envelope, one error envelope
Every endpoint returns the same-shaped wrapper. Define it once (see `error-handling.md` for where errors are mapped). Errors carry a stable machine-readable code, not just a human string.

```json
// ✅ Good: consistent shapes
{ "data": { "id": 42, "status": "paid" } }
{ "error": { "code": "order_not_found", "message": "Order 42 does not exist" } }
```

## Pagination metadata
Return paginated collections with explicit metadata so clients can iterate without guessing. Include totals or a next cursor — never just a bare array that hides whether more exists.

```json
{ "data": [ ... ], "meta": { "next_cursor": "eyJpZCI6NTB9", "per_page": 50 } }
```

## Idempotency
GET, PUT, and DELETE must be idempotent — repeating them yields the same state. POST is not; when a retry must not double-create (payments, orders), accept an `Idempotency-Key` header and dedupe on it server-side.

```
❌ Bad:  retried POST /payments charges twice
✅ Good: POST /payments  +  Idempotency-Key: <uuid>  →  second call returns the first result
```

## Proper status codes
Map outcomes to semantics: 200/201/204 for success, 400 validation, 401 unauthenticated, 403 unauthorized, 404 missing, 409 conflict, 422 unprocessable, 429 rate-limited, 5xx server. Never return 200 with an error body — it breaks every client's error handling.

## Balance note
Conform to the codebase's established envelope, versioning, and naming even if you prefer another convention — consistency across the API outweighs local preference. Only 200-with-error-body and other correctness breaks warrant an override.

Source: best-practice · Confidence: high
