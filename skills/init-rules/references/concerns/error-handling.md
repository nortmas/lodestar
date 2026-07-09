# Error Handling (Tier 2)

Guidance for how failures propagate, get logged, and surface to callers.

## Model failures as typed domain exceptions
Throw specific exception types (`PaymentDeclinedException`, `OrderNotFoundException`), not generic ones. Callers should discriminate on type, not parse messages. Reserve generic `\Exception`/`\RuntimeException` for truly unexpected conditions.

## Never swallow
A caught exception must be re-thrown, wrapped, or turned into a deliberate handled outcome. An empty or log-only `catch` that lets execution continue as if nothing happened is a correctness defect.

```php
// ❌ Bad: swallowed — caller believes the charge succeeded
try {
    $gateway->charge($order);
} catch (\Throwable $e) {
    // ignore
}

// ✅ Good: wrap with context, preserve cause, let it propagate
try {
    $gateway->charge($order);
} catch (GatewayException $e) {
    throw new PaymentFailedException("Charge failed for order {$order->id}", previous: $e);
}
```

## Fail fast on invalid state
Validate preconditions at the top of a function and throw immediately. Do not defensively `null`-guard downstream to paper over an invalid state that should never have been constructed.

## Map to an API error envelope in ONE place
Translate exceptions to HTTP status + error body in a single handler (exception handler / middleware), never per-controller. This keeps the wire contract consistent and prevents leaking stack traces or internal messages. The envelope shape lives in `api-design.md`.

## Log with context, never secrets
Attach a correlation/request id, entity ids, and operation name to every error log. Never log passwords, tokens, full card numbers, or PII. Log the exception once at the boundary where it is handled — not at every re-throw, which produces duplicate noise.

```php
// ✅ Good: structured context, cause preserved, no secrets
$logger->error('payment.charge.failed', [
    'correlation_id' => $ctx->correlationId,
    'order_id'       => $order->id,
    'exception'      => $e::class,
    // note: no card data, no auth token
]);
```

## Distinguish retryable vs terminal
Separate transient failures (timeout, 503, deadlock) from terminal ones (validation, 404, business rule). Only retry the retryable, with backoff and a cap. Retrying a terminal failure wastes resources and can double-apply side effects.

## Balance note
Match the codebase's existing exception hierarchy and envelope location even if you would structure them differently. But swallowed exceptions, logged secrets, and retrying non-idempotent terminal failures are correctness/security defects — flag and fix, do not codify.

Source: best-practice · Confidence: high
