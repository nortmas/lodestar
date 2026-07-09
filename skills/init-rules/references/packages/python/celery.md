# Celery (Tier 2)

Celery task-design idioms (assume Celery 5+; check the installed major). For
Python correctness/errors see `../../languages/python.md`; for retry/backoff and
failure surfacing see `../../concerns/error-handling.md`. Balance policy: a
consistent existing pattern wins unless it is a security/correctness/performance
defect.

## Idempotent tasks
Assume at-least-once delivery: a task may run twice (redelivery, retry, worker
crash). Make effects idempotent — upsert on a natural key, guard with a
processed-marker, or make the operation naturally repeatable. Never assume
exactly-once.

## Serialize with JSON, never pickle
Set `task_serializer="json"` and `accept_content=["json"]`. `pickle` executes
arbitrary code on deserialization — a broker compromise becomes RCE. This is a
security carve-out: override an inherited pickle config and note the migration.

## Small, serializable args — pass IDs, not objects
Send primitive IDs and re-fetch inside the task. A serialized ORM object is
stale by the time it runs, bloats the broker, and may not round-trip.

❌ Bad — whole ORM object passed to the task
```python
@app.task
def send_invoice(order):           # ORM instance serialized onto the broker
    order.mark_sent()              # stale state; huge, fragile payload
```
✅ Good — pass the id, load fresh, stay idempotent
```python
@app.task(bind=True, max_retries=5, acks_late=True)
def send_invoice(self, order_id: int) -> None:
    order = Order.objects.get(pk=order_id)
    if order.invoiced_at:          # idempotency guard — safe on redelivery
        return
    try:
        mail.send(order.invoice())
        order.mark_sent()
    except SMTPException as exc:
        # Exponential backoff with jitter; do not retry forever.
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

## Timeouts + bounded retries with backoff
Set `time_limit`/`soft_time_limit` so a hung task cannot pin a worker forever.
Bound retries (`max_retries`) and back off exponentially with jitter; retrying
tight-loop hammers a struggling dependency. Use `acks_late=True` only with
idempotent tasks.

## Separate queues by priority
Route slow/bulk work to its own queue and worker pool so it cannot starve
latency-sensitive tasks. Do not run everything on the default queue.

## Never call `.get()` inside a task
Blocking on a subtask's result from within a task deadlocks the worker pool.
Compose with `chain`/`group`/`chord` or a callback instead. Keep a result
backend only if results are consumed; set `result_expires` so it self-cleans.

Source: best-practice · Confidence: high
