# PostgreSQL (Tier 2)

Datastore-specific decisions. For generic ORM/query hygiene see `../../concerns/performance.md`, `../../concerns/security.md`, `../../frameworks/laravel.md` (Eloquent), and `../python/sqlalchemy.md`.

## Indexing
- Index columns used in hot `WHERE`, `JOIN`, and `ORDER BY` clauses. A missing index on a hot path is a **performance defect** — override the balance policy and add it, with a migration note.
- Index every foreign key. Postgres does NOT create one automatically; unindexed FKs make cascades and joins seq-scan.
- Verify plans with `EXPLAIN (ANALYZE, BUFFERS)`. A `Seq Scan` over a large table on a filtered column is the smell.

```sql
-- ❌ Bad: filter column has no index → Seq Scan on every lookup
SELECT id, email FROM users WHERE lower(email) = 'a@b.com';

-- ✅ Good: expression index matches the query → Index Scan
CREATE INDEX idx_users_lower_email ON users (lower(email));
SELECT id, email FROM users WHERE lower(email) = 'a@b.com';
```

## Types
- `jsonb` over `json` (binary, indexable via GIN, deduped keys). Use `json` only to preserve exact input text.
- `timestamptz` over `timestamp` — always store an instant, not a naive wall-clock value.
- `text` over `varchar(n)` unless a length limit is a real domain constraint; they perform identically.
- `numeric` for money; never `float`/`double` (rounding loss).

## Constraints
Enforce in the database, not only in app code — app validation is bypassable and races. Use `NOT NULL`, FK references, `CHECK`, and `UNIQUE` constraints as the source of truth.

## Migrations
- Migrations run in a transaction, so a failed step rolls back — good.
- BUT `CREATE INDEX CONCURRENTLY` cannot run inside a transaction. On large hot tables, build indexes concurrently (no write lock) in a non-transactional migration step.

## Querying
- Explicit column lists, never `SELECT *` (avoids over-fetch, survives schema changes, enables index-only scans).
- Parameterized queries / bound statements only — never string-interpolate input (SQL injection is a critical carve-out; see `../../concerns/security.md`).
- Bound every result set with `LIMIT` / pagination; unbounded reads are a performance defect.

## Concurrency
Front the DB with a pooler (PgBouncer, transaction mode) under high concurrency. Postgres backends are heavyweight; hundreds of direct app connections exhaust `max_connections` and memory.

Source: best-practice · Confidence: high
