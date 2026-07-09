# Laravel Horizon (Tier 2)

laravel/horizon v5 idioms only. For writing jobs, dispatching, batches, and
retry/backoff see `../../frameworks/laravel.md` (jobs-queues) and
`../../concerns/performance.md`. Balance policy: a consistent existing pattern
wins unless it is a security/correctness/performance defect — an exposed
dashboard is a **critical** security defect and is overridden with a migration
note.

## Protect the dashboard
- `Horizon::auth()` gate in `HorizonServiceProvider` decides who sees the UI. The
  default only allows `local`. In any shared environment it **must** authorize
  real users — an open `/horizon` leaks queue payloads, failed-job exceptions,
  and lets anyone retry/delete jobs.

## Configure supervisors, not just `default`
- Split queues by priority and give each its own supervisor
  (`config/horizon.php`). Do not funnel everything onto one queue where slow bulk
  jobs starve latency-sensitive ones.
- Pick a `balance` strategy deliberately: `auto` (scales workers to load) is the
  usual default; `simple`/`false` only when you need fixed, predictable workers.
- Set `maxProcesses`, `memory`, `timeout`, and `tries` per supervisor. `timeout`
  must be shorter than the queue connection's `retry_after`, or a job runs twice.

## Jobs must be idempotent and serializable
- A queued job can retry, so running it twice must not double-charge or
  double-send. Guard with a unique key / `ShouldBeUnique`, or make the effect
  naturally idempotent.
- Constructor state is serialized. Pass IDs, not fat objects/closures; use
  `SerializesModels` and re-fetch inside `handle()`. Tag jobs
  (`public function tags(): array`) so Horizon monitoring can group them.

❌ Bad — open dashboard, non-idempotent job
```php
// HorizonServiceProvider: no gate → anyone reaching /horizon controls the queue.

class ChargeCustomer implements ShouldQueue
{
    public function handle(): void
    {
        // A retry after a timeout charges the card a second time.
        Stripe::charge($this->order->total);
        $this->order->update(['status' => 'paid']);
    }
}
```
✅ Good — gated dashboard, idempotent + tagged job
```php
// HorizonServiceProvider
Horizon::auth(fn ($request) => $request->user()?->can('viewHorizon'));

class ChargeCustomer implements ShouldQueue, ShouldBeUnique
{
    public int $tries = 3;
    public function uniqueId(): string { return "charge-{$this->orderId}"; }
    public function tags(): array { return ["order:{$this->orderId}"]; }

    public function handle(): void
    {
        $order = Order::findOrFail($this->orderId);
        if ($order->isPaid()) return;                 // idempotent guard
        Stripe::charge($order->total);
        $order->update(['status' => 'paid']);
    }
}
```

Source: best-practice · Confidence: high
