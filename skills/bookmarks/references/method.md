# Method

## Find

`bm.py search` is retrieval, not the answer. It returns up to 60 candidates ranked by
BM25 over path, title, URL, tags and summary. Your job is the reranking and the shape
of the reply.

**Expand the query first.** A user asking «где-то была ссылка про блокировки в
очередях» should produce terms like `блокировка очередь lock queue atomic race
mutex`. One-word searches are the main cause of a miss, not a weak index.

**Read the paths.** Two hits in the same folder mean the folder itself is the answer —
say so, and offer the folder rather than listing its contents one by one.

**Answer format.** Group by theme when there are more than about five results.
Per result: a markdown link on the title, the folder path, one clause on why it
matches. Never dump the raw TSV.

**Zero hits is not an answer, it is a signal to try again.** Retrieval is lexical:
your words have to overlap the words in the title, path or tags. When the first query
returns nothing, the usual cause is vocabulary, not absence. Re-expand along a
different axis — the other language, brand name instead of function, plain speech
instead of jargon — and search again. Only after two or three genuinely different
attempts should you say it is not there, and then name the folders you covered.

A confident wrong answer costs more than a miss here — the user knows their collection
and will spot a bad match instantly. But a premature "not found" for a link that is
sitting right there costs the most trust of all.

## File a new bookmark

Route by role, not by topic keyword. The roots in `profile.md` carry the routing rules;
most collections separate work from personal from reference from short-term, whatever
the folder names happen to be.

Find where siblings live: search for terms drawn from the URL and see which folder
already holds that kind of thing. Land the bookmark next to its siblings even if a
theoretically better category exists elsewhere — consistency beats correctness, because
the user navigates from memory.

Propose the destination and one alternative. Do not create a folder for a single
bookmark; that is what thin folders are made of.

## Audit

`bm.py check-links` writes a browsable HTML report when it finishes — clickable
titles, folder paths, the enrichment summary under each entry, colour badges for
evergreen/obsolete/googlable, and the guid column needed to build a delete patch.
It lands at `report_path` from `config.json`, default `~/bookmarks-cleanup.html`.
Give the user that path and let them read it; do not paginate hundreds of rows into
the conversation. Rebuild it any time with `bm.py report --html [PATH]`, and suppress
it during a sweep with `--no-report`.

`bm.py report` without `--html` prints the same grouping as TSV, for when you need to
reason over the rows yourself. Present them in descending order of safety:

**Dead links** — 404, 410, or a domain that no longer resolves, confirmed by a GET
after the HEAD. The `link_status` field records both (`HEAD 404 / GET 200` means the
server dislikes HEAD and the page is fine — those are classified `ok`, not dead). Still
show the list rather than acting on it: a handful of sites 404 selectively.

`check-links` resolves canary hosts before starting and refuses to run without DNS, and
discards a large batch whose DNS failure rate is implausible. Neither guard covers a
*partial* fault — one blocked country or TLD looks exactly like genuine death. Before
proposing deletions, look at whether the dead set clusters on one TLD or one network
path; if it does, say so instead of proposing them.

**Obsolete stack** — the technology underneath is gone. A major version nobody runs,
a discontinued product, a retired API. This is the only bulk-deletion category that
matters, and it needs the model's judgement rather than a query: flagged during
enrichment via `obsolete`, then confirmed by looking at the actual folder.

**Trivially re-googlable** — homepages and landing pages of well-known tools. Low
value, low risk, but check `evergreen` first.

**Verify by hand** — 403, 429, timeouts, 5xx. Many are alive and simply refuse bots.
Never propose these for deletion; hand the list over as-is.

**Stale short-term** — items sitting in the staging root past its TTL. The clock is
`hot_since`, stamped by `sync` when a bookmark is first seen there, **not** the date it
was created: a link saved years ago and moved into staging yesterday has been waiting
one day. That means the clock starts at the first sync after setup, so this section is
empty at first and becomes meaningful over time — say so rather than reporting zero.

The question here is never "delete?" but "does this get a permanent home, or does it go
to the archive?"

### Age is not a deletion criterion

A link untouched for six years may be exactly the reference the user wants next month.
Algorithms, design patterns, grammar, mathematics, and principles do not expire; the
`evergreen` flag protects them explicitly. Age only raises an item for review — the
decision comes from whether the underlying thing is dead.

Never propose deleting an entire branch on aggregate statistics. Open it, look at what
is actually in it, and say what you found.

## Reorganize

### The trade-off to optimize

Depth costs clicks. A four-level path is four decisions between wanting a link and
having it. Whether perfect taxonomy or fast access wins when they conflict is the
user's call, recorded in `profile.md` — and it is the answer that governs every
proposal here, so do not start without it.

Read `profile.md` for constraints on the root level too. Where the top level doubles
as a quick-access row on a small screen, its width and name length are load-bearing
and not available for tidying.

### What to look for

**Thin folders.** A folder at or under the `thin_folder_max` threshold with no
subfolders is a decision the user made once and never used again. Collapsing it into
its parent removes a level for its contents. `bm.py stats` counts them; `bm.py report`
lists them. Collapse in groups, by branch, with the whole group visible for review.

**Deep bookmarks.** Anything at or past `deep_level`. Usually the tail of a
subdivision that went one step too far.

**Scattered themes.** The same subject living in three or four places because it grew
into different branches over the years. Propose one home and moves into it — but only
if the merge does not deepen the path for the majority.

**Fat folders.** At or above `fat_folder_min` direct bookmarks. Rarer than expected,
and splitting one costs a level, so only split when a natural grouping already exists
in the titles.

### Procedure

1. Pick one branch. Never the whole tree at once.
2. `bm.py folder "<path fragment>"` to see everything in it.
3. Record before-metrics from `bm.py stats`.
4. Propose the changes as a readable list — «сложить X, Y, Z в родителя; переименовать
   A в B» — not as JSON. Include the depth change.
5. On approval, build the patch (`patching.md`), dry-run it, apply it.
6. Report after-metrics.

### Naming fixes

Typos frozen into folder names and HTML entities leaked into titles are safe,
mechanical repairs — batch them.

Rewriting titles wholesale is not. Trimming `| Site Name` suffixes and shortening long
titles changes what the user recognizes when scanning, and there is no diff to review
afterwards inside Chrome. Do it per branch with the proposed names visible, never as a
single pass over the whole collection.
