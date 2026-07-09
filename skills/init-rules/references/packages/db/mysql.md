# MySQL (Tier 2)

Datastore-specific decisions. For generic ORM/query hygiene see `../../concerns/performance.md`, `../../concerns/security.md`, `../../frameworks/laravel.md` (Eloquent), and `../python/sqlalchemy.md`.

## Engine & charset
- Use InnoDB (transactions, row locking, FK support), never MyISAM for application data.
- Use `utf8mb4` charset/collation, never `utf8` — MySQL's `utf8` is a legacy 3-byte encoding that silently truncates emoji and some CJK. This is a correctness carve-out.

## Indexing
- Index columns in hot `WHERE`/`JOIN`/`ORDER BY` and every foreign key. A missing index on a hot path is a **performance defect** — override the balance policy and add it with a migration note.
- Verify with `EXPLAIN`; watch for `type: ALL` (full scan) and `Using filesort` on large tables.

## Types
`DECIMAL` for money, never `FLOAT`/`DOUBLE` (binary rounding corrupts sums).

```sql
-- ❌ Bad: 3-byte utf8 truncates emoji; FLOAT loses cents
CREATE TABLE orders (
  note  VARCHAR(255) CHARACTER SET utf8,
  total FLOAT
);

-- ✅ Good: full unicode + exact money
CREATE TABLE orders (
  note  VARCHAR(255) CHARACTER SET utf8mb4,
  total DECIMAL(12,2)
) ENGINE=InnoDB;
```

## Implicit coercion
A type mismatch between column and value silently disables the index. Compare like with like — quote strings, don't pass numbers to `VARCHAR` columns.

```sql
-- ❌ Bad: numeric literal vs VARCHAR column → coercion, no index used
SELECT * FROM users WHERE phone = 491234567;

-- ✅ Good: matching string type keeps the index
SELECT id, name FROM users WHERE phone = '491234567';
```

## sql_mode
Run with strict mode (`STRICT_TRANS_TABLES`, `NO_ENGINE_SUBSTITUTION`). Without it, MySQL truncates overflowing values and accepts invalid dates instead of erroring.

## Querying
- Explicit column lists, never `SELECT *`.
- Parameterized queries only — never interpolate input (SQL injection is a critical carve-out; see `../../concerns/security.md`).
- Avoid `ORDER BY RAND()` on large tables (full scan + filesort of every row). Sample by random id range instead.
- Avoid large-offset pagination: `LIMIT 100000, 20` scans and discards 100k rows. Use keyset/seek pagination.

```sql
-- ❌ Bad: OFFSET scans and throws away every earlier row
SELECT id, title FROM posts ORDER BY id LIMIT 100000, 20;

-- ✅ Good: keyset pagination seeks straight to the page via the index
SELECT id, title FROM posts WHERE id > 100000 ORDER BY id LIMIT 20;
```

Source: best-practice · Confidence: high
