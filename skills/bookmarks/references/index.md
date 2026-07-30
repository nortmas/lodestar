# The index

Two files, one source of truth. `index.jsonl` holds the data and is committed to git;
`index.db` is an SQLite FTS5 table rebuilt from it on every write and never committed.
Records are keyed by the bookmark's Chrome `guid`, which survives renames and moves —
paths and titles do not.

## Record

```json
{
  "guid": "4a514839-…",
  "path": ["bookmark_bar", "Laravel", "Articles & Blogs", "Cache"],
  "title": "Preventing Duplicate Form Submissions Using Atomic Locks",
  "url": "https://…",
  "root": "bookmark_bar",
  "added": "2024-03-11", "used": "", "age_days": 872, "cold": true,
  "tags": ["atomic lock", "атомарная блокировка", "race condition", "очередь"],
  "summary": "Using Cache::lock to stop double form submits",
  "kind": "article",
  "evergreen": true, "obsolete": false, "googlable": false,
  "link": "ok", "link_status": "200", "checked": "2026-07-30"
}
```

`bm.py sync` maintains everything above the `tags` line straight from Chrome. The
model produces the middle block. `bm.py check-links` fills the last one.

## Fields the model writes

| Field | Meaning |
|-------|---------|
| `tags` | 4–8 retrieval handles. Include the **other language** — a query in one language must reach a title in another. Include the concept, and synonyms at a different register, not just words already in the title. This field is why search works at all. |
| `summary` | One clause, under 12 words, saying what the page gives you. Shown in search output and used for reranking, so write it for a reader who has forgotten the page. Skip only if the title genuinely says it. |
| `kind` | `article`, `docs`, `tool`, `library`, `video`, `course`, `reference`, `shop`, `service`, `account`, `forum` |
| `evergreen` | True if it stays valuable regardless of age: algorithms, patterns, grammar, math, principles. **Protects from deletion.** |
| `obsolete` | True only if the underlying technology is dead — a major version nobody runs, a discontinued product, a retired API. Not "old". |
| `googlable` | True if a search engine would return this in one query — a site homepage, a well-known tool's landing page. Low bookmark value. |

`evergreen`, `obsolete` and `googlable` are the deletion signals. Be conservative:
a wrong `obsolete` costs the user a link they wanted, a wrong `false` costs nothing.

## Enrichment pass

```bash
bm.py dump --limit 100                # TSV: guid, path, title, url
```

Read the batch, write one JSON object per line, feed it back:

```bash
bm.py ingest batch.jsonl              # or: … | bm.py ingest -
```

Then repeat the same two commands until `dump` prints `0 bookmarks in this batch`.

**`dump` is a queue, not a page.** It excludes records that already have tags, so each
call returns the next slice of remaining work. Never pass `--offset` — it would skip
bookmarks that still need tags, and the loop would then terminate reporting success on
a half-enriched corpus. The command refuses `--offset` for this reason. The trailing
count (`N still queued after it`) is the honest progress indicator.

Batches of 80–120 are the practical unit: each record is roughly 90 output tokens, so
100 records is about 9k tokens of writing in one go. Commit every few batches with
`bm.py save`.

The **folder path is the strongest context you have**. A bookmark named `Sentry` under
`Work › ClientName` is that client's error tracker; the same name under `Tools` is the
product page. Titles like `VIA`, `Th`, or `Сборник инфы` mean nothing alone and
everything in place. Use the path and the URL; do not fetch pages.

**Cost, both sides.** Roughly **60 input and 90 output tokens per bookmark** — the
output side is the larger one and the more expensive one per token, so quote both. For
a 3000-bookmark collection that is on the order of 180k in and 270k out. Give the user
that estimate before starting, not a single number.

## Keeping it fresh

`bm.py sync` reconciles the index with Chrome: new bookmarks get stub records, moved
and renamed ones get updated paths. It is fast enough to run before every search, and
`bm.py search` reports `missing=N` when it is stale.

**Records are not deleted when a bookmark disappears.** They are marked
`missing_since` and excluded from search, `report` and link checking, because a sync
run against the wrong Chrome profile — or before Chrome sync has finished downloading
the tree — would otherwise destroy the entire enrichment corpus in one command. `sync`
refuses outright when more than 5% of the index would vanish. `--prune` is the
deliberate override; reach for it only after confirming the profile path in
`bm.py status`.

This is why a cleanup cycle converges: bookmarks deleted in a previous round are not
proposed again. `report` prints how many such records exist so they stay visible.

A bookmark that **moved** keeps its tags: its meaning did not change. A bookmark whose
**URL was edited** does not — `sync` compares a hash of title+url and drops stale tags
so `dump` picks the record up again. `re-queued=N` in the sync output is that count.

After any index change: `bm.py save "<message>"` to commit, rebase onto the remote and
push. It stages only files that exist and fails loudly rather than reporting a success
it did not achieve.

**Two machines.** `index.jsonl` is one record per line keyed by guid, so a git conflict
is mechanically resolvable: keep both sides, delete the markers, `git add index.jsonl
&& git rebase --continue`, then `bm.py sync`. If `read_index` hits a conflict marker it
says so and names the line.

If the remote has diverged, `save` commits, aborts the rebase so the repository is left
clean on its branch with the commit safe, and prints the manual sequence. It refuses to
run at all while a rebase or merge is half-finished, and `bm.py status` reports that
state — acting on top of an interrupted rebase is how a commit ends up on no branch.

After any `git pull` the local `index.db` is stale. `search` detects that from an md5 of
`index.jsonl` and rebuilds automatically, so a pulled enrichment is never silently
invisible — including after a `cp -p` or `rsync -t` that preserves timestamps.
