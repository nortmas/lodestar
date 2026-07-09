# Observability & Logging (Tier 2)

Codify what makes logs actionable and safe. The balance policy applies: match the repo's existing logger and format. The exception is leaking secrets/tokens/PII — that is a SECURITY defect (see `security.md`), never a style choice. Override and emit a migration note.

## Decisions worth encoding

- **Structured, not prose.** Emit key-value/JSON with a message plus fields. Never string-concatenate variables into a sentence — it defeats querying and aggregation.
- **Levels mean something.** `error` = needs attention/paged; `warn` = degraded but handled; `info` = business-level milestones; `debug` = dev diagnostics. Everything-at-`info` is a smell. Reserve `error` for failures the caller could not absorb (pair with `error-handling.md`).
- **Correlation IDs.** Thread a request/trace ID through every log line in a request lifecycle so a single flow is reconstructable. Put it in the logger context, not each call site.
- **Redact by default.** No passwords, tokens, API keys, auth headers, full card/SSN, or raw PII. Redact at the logger (processor/formatter) so no call site can leak.
- **Log at boundaries.** HTTP in/out, queue consume, external API calls, DB transaction edges — not inside tight loops (sample or aggregate instead).
- **Actionable context.** Include the ids/state needed to act (`user_id`, `order_id`, `status`), not "error occurred".
- **Metrics + health.** Expose RED (Rate, Errors, Duration) for request paths, USE (Utilization, Saturation, Errors) for resources, a health/readiness endpoint, and tracing spans around known-slow paths.
- **Centralize config.** One place wires channels, level, format, and redaction — call sites just log.

## Laravel note

Use Monolog channels (`config/logging.php`) and contextual logging — `Log::withContext([...])` for request-scoped ids, `Log::error($msg, ['order_id' => $id])` for per-event fields. Add a redaction processor rather than sanitizing at each call. Push the correlation id in middleware.

## Example

❌ Bad — unstructured, wrong level, leaks a token:

```php
// Interpolated prose, secret in the line, everything at info.
Log::info("Charge failed for {$user->email} using token {$card->token}: {$e->getMessage()}");
```

✅ Good — structured, correct level, redacted, correlated:

```php
// Fields are queryable; token never logged; error level; request id via context.
Log::error('payment.charge_failed', [
    'user_id'    => $user->id,        // id, not email/PII
    'order_id'   => $order->id,
    'gateway'    => 'stripe',
    'error_code' => $e->getCode(),    // no raw token, no message dump with secrets
]);
```

Migration note: if existing code logs secrets/PII, treat it as a critical finding — redact at the logger and scrub, regardless of prevailing style. See `security.md`.

Source: best-practice · Confidence: high
