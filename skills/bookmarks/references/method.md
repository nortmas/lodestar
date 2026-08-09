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

When one folder is clearly the home, file it there and report where it went — a
confirmation round-trip on a single add costs the user more than a wrong guess, which
is one `move` op to fix. Ask only when the candidates are genuinely comparable, and ask
with `AskUserQuestion` so the answer is a click: one option per folder, labelled with
its path and what already lives in it.

Do not create a folder for a single bookmark; that is what thin folders are made of.

## Audit

`bm.py check-links` writes an **interactive** HTML report when it finishes, and this
is the main way the user makes cleanup decisions. It lands at `report_path` from
`config.json`, default `~/bookmarks-cleanup.html`. Rebuild it any time with
`bm.py report --html [PATH]`; suppress it during a sweep with `--no-report`.

The report has clickable titles, folder paths, the enrichment summary under each
entry, badges for evergreen/obsolete/googlable so conflicting signals are visible,
sortable columns, and a checkbox on every row plus one per category that marks the
whole group. A ticked box means **delete**; unticked means keep. Marks persist in the
browser's localStorage, so the user can review across sessions.

**Give the user the path and let them work.** Do not paginate hundreds of rows into
the conversation — the report exists precisely so that does not have to happen.

### Reading their decisions back

The report's "Скачать патч" button writes `~/Downloads/bookmarks-delete-patch.json`.
It is directly applicable, and each op also carries `title`, `path` and `category`,
which `bm.py apply` ignores and you must not.

When the user says they have marked things:

1. Read the file. If it is missing, ask — they may have used "Скопировать патч" and
   will paste it instead.
2. **Summarize what it actually contains before touching anything**: how many
   deletions, which branches they fall in, and anything that looks like a mistake —
   an evergreen entry among the deletions, a whole category ticked where the
   category was one you flagged as needing judgement, a branch losing far more than
   the rest.
3. `bm.py apply <file> --dry-run`, show the action list, get explicit approval.
4. Then the normal write procedure, including the sync warning.

Never apply a patch from the report without step 2. A ticked checkbox is a decision
made while scrolling; your job is to make its consequences visible before the write.

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

**The short-name principle.** When the user does ask for readable names across a branch,
the target is the shortest string that still says what the thing *is* — which is almost
always the **brand or product name**, with the marketing tail cut:

- Drop everything after the brand: `Wispr Flow | Voice Dictation` → `Wispr Flow`,
  `ChatPDF - Chat with any PDF!` → `ChatPDF`, `Coinbase - Your Hosted Bitcoin Wallet`
  → `Coinbase`. The tagline is noise once the folder gives the context.
- When the brand is not in the title, recover it from the URL or tags and use it:
  `Voice Meeting Notes` (otter.ai) → `Otter`, `Free Online Presentation` (canva.com)
  → `Canva`. The tags carry the brand — that is what they are for.
- No brand? Name the function, short: `MOV to GIF` → `MOV → GIF`,
  `Online Video Downloader` → `Video Downloader`.
- Two entries that resolve to the same brand need a disambiguator in parentheses, or
  they read as duplicates: `HideMy.name — прокси`, `Стикеры (tlgrm.ru)` vs
  `Стикеры (telegramchannels)`.
- Keep the topic's language — a Russian/local item stays Russian (`Профи.ру`,
  `Аренда без посредников (КРД)`); do not anglicise it to look uniform.
- Leave a title that is already a bare brand untouched (`TinyPNG`, `Excalidraw`), and
  fix any typo in passing (`Pixlr X - радактрор фото` → `Pixlr`).

It is still a per-branch pass with the full before→after list shown for approval — the
principle decides each name, it does not license skipping the review.

### Ordering within a folder — subfolders first, then bookmarks

Inside any folder, all subfolders come first, then the loose bookmarks. Chrome shows
nodes in stored order, and a folder that mixes them — a few subfolders, then links,
then more subfolders — reads as unsorted clutter. This is the default the user expects.

It matters most right after a restructure: `move` and `create` append to the end of the
destination, so newly-created subfolders land *below* the existing loose bookmarks. Any
reorganize that adds or moves nodes must finish with a reorder pass that lifts every
subfolder above the first URL. Reorder by re-`move`ing each subfolder to its target
`index` (folders take indices `0..n-1`, in the chosen order — alphabetical unless the
user asked otherwise); the bookmarks fall in behind them. Preview and apply it as part
of the same restructure, not as a separate afterthought.

### Reshape a branch from a blank slate (global reorganization)

Distinct from the incremental tidying above. The trigger is the user asking, in effect,
«если бы это была плоская куча закладок без папок, как бы ты её разложил?» — a full
redesign of one branch's taxonomy, not a handful of moves. The steps below; only the
last one writes.

0. **Ask first whether to read preferences off the current structure.** One
   `AskUserQuestion`: infer their organizing preferences from the existing tree, or start
   clean? On *no*, skip step 1 entirely and group purely by function under `profile.md`'s
   constraints — a user escaping the current mess does not want it treated as the spec.
   Only on *yes* do step 1.

1. **Read the user's preferences off the whole tree, not just the branch.** The existing
   structure *is* the spec. Walk every root and name what it reveals, then say it back
   before proposing anything:
   - what the top level sorts by — life-domain / role vs. content-type;
   - how much depth the user tolerates where a topic is rich;
   - whether a theme earns a folder at one or two bookmarks (granularity);
   - which language each kind of topic is named in;
   - what is kept apart from what (work vs. personal, tools vs. reading);
   - whether loose bookmarks at a folder's root are normal for them.
   These, with `profile.md`, govern every later choice. Treat any hard constraint the
   user states outright — a depth cap («не глубже двух уровней»), a naming rule — as an
   invariant, and check the final tree against it.

2. **Flatten and redesign on paper.** `bm.py folder <branch>` for the full contents;
   treat them as an unsorted pile. Group by function/theme into a taxonomy that obeys
   the preferences from step 1. Present it as a table with per-folder counts, mark the
   judgement calls (items that could sit in two places, singletons with no clean home),
   and get approval. Nothing is executed here.

3. **Execute as a phased id-based migration.** Reuse what exists: rename a folder into
   its new role rather than creating a twin, promote a subfolder by moving it up rather
   than rebuilding it, absorb loose items into the folder that already holds their kind.
   On a synced profile all of this runs through `exec` by node id — the phasing rules
   (why you cannot move-then-remove in one run, how nested empties collapse one level
   per phase) are in `references/patching.md`, "Live restructuring".

4. **Verify.** The bookmark count under the branch must be unchanged unless you deleted
   on purpose; depth must be within any cap the user set; folders must precede loose
   bookmarks. Then `bm.py sync` and `bm.py save`.
