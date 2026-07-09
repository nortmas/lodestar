# Redis (Tier 2)

Datastore-specific decisions. For caching strategy and hot-path cost see `../../concerns/performance.md`; for Laravel queues/Horizon see `../../frameworks/laravel.md`.

## TTLs
Set a TTL on every cache key. Keys without expiry accumulate until Redis hits `maxmemory` and starts evicting (or erroring) — **unbounded memory growth is a critical defect**, override the balance policy.

## Key naming
Namespace keys hierarchically: `app:entity:id` (e.g. `shop:cart:1042`). Consistent prefixes make `SCAN` filtering, per-feature flushing, and debugging tractable.

## Data structures
Pick the structure that fits the access pattern instead of stuffing JSON blobs into strings:
- Hash for object fields you update individually (`HSET user:1 name ...`).
- Set / Sorted Set for membership, ranking, leaderboards, rate windows.
- String JSON only when you always read/write the whole value.

## Never KEYS in production
`KEYS` is O(N) and blocks the single-threaded server across the whole keyspace. Use `SCAN` (cursor, non-blocking) instead. This is a correctness/performance carve-out.

```
# ❌ Bad: blocks Redis, and the key never expires
KEYS user:*
SET user:1 "{...}"

# ✅ Good: non-blocking scan, namespaced key, bounded lifetime
SCAN 0 MATCH app:user:* COUNT 100
SET app:user:1 "{...}" EX 3600
```

## Persistence vs pure cache
Know the role. A pure cache can lose everything on restart (disable/relax RDB/AOF, treat misses as normal). A queue/session/source-of-truth store needs AOF (`appendfsync everysec`) and a backup plan — data loss there is a correctness bug.

## Separate concerns
Keep cache, queue, and session on separate databases or instances. A cache flush must never wipe queued jobs or live sessions; mixed workloads also fight over eviction policy.

## Avoid blocking operations
Do not store multi-MB values or fire huge pipelines/`MGET`s — one big command stalls every other client (single thread). Chunk large batches.

## Idempotent invalidation
Invalidation must be safe to run twice and tolerate a missing key. Prefer deleting the key (lazy recompute on next read) over trying to keep it perfectly in sync.

Source: best-practice · Confidence: high
