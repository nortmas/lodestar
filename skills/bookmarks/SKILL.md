---
name: bookmarks
description: Search, file, audit and reorganize Chrome bookmarks via a sidecar index
disable-model-invocation: true
---

# Bookmarks

Chrome stores bookmarks as a single JSON file. This skill reads it directly, keeps
a searchable sidecar index next to it, and writes back only through reviewed patches.

**Reads are always safe.** Chrome does not lock the file, so search, audit and
reporting work with the browser open. **Writes require Chrome to be closed**, because
Chrome holds the tree in memory and overwrites the file when it exits.

All work goes through one script, invoked as:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/bookmarks/scripts/bm.py" status
```

If `${CLAUDE_PLUGIN_ROOT}` is unset the path collapses to `/skills/...` and nothing
runs; fall back to `~/.claude/skills/lodestar/skills/bookmarks/scripts/bm.py`.

The rest of this skill writes that as `bm.py` for brevity — always expand it to the
full path above. It is Python 3 with no dependencies. **Run `bm.py status` first** in
any session that reorganizes, deletes, or writes through `apply` — skip it when simply
filing a bookmark, which needs none of what it reports. It reports the profile path,
index size, whether Chrome is running, and whether the safety guard has been disabled.

## The user's own rules come first

Personal taxonomy lives in `profile.md` in the data directory (default
`~/.claude/bookmarks/`), never in this repo. **Read it before proposing any change.**
It defines the root folders and their retention roles, naming conventions, language
rules, and thresholds.

If `profile.md` is missing, run the setup in `references/setup.md`. It starts with
`bm.py profile-scan`, which reports what the tree reveals, and then **interviews the
user** about the parts that cannot be inferred: what each root is for, how long things
stay there, why the shape is the shape, and what must never be deleted. Do not invent
conventions and do not hand out a generic questionnaire — a tree someone has curated
for years already answers half the questions, and quoting it back is what makes the
other half worth asking.

Thresholds live in `config.json` and are set during that interview. Nothing in this
skill hardcodes what counts as too deep, too small, too old, or too big.

## Commands

This skill is invoked explicitly (`/lodestar:bookmarks …`) and never auto-triggers. Read
the **first word** of the invocation as a command and the rest as its target, then follow
the section it points to. **With no command, present `help` (below) and then run
`bm.py status`**, so the user sees what they can do and the current state in one go. An
unrecognized first word → show `help` and ask, do not guess.

| Command | Target | What it does |
|---------|--------|--------------|
| `help` | — | Explain the skill, the commands, and the Chrome extension setup (below). |
| `reshape` | a folder | Redesign the folder's taxonomy from a blank slate — see "Reorganize" → *Reshape a branch from a blank slate* in `references/method.md`. **Ask the preferences question first** (below). |
| `rename` | a folder | Shorten every title in the folder by the short-name principle (`references/method.md` → *Naming fixes* → *The short-name principle*). If the folder is large, fan the naming out as a workflow, then apply the results in one `exec` pass. |
| `tidy` | a folder | Incremental cleanup, not a redesign: collapse thin folders, fix name typos, enforce folders-first order. See "Reorganize". |
| `merge` | 2+ folders | Consolidate same-theme folders into one, deduping items that already live in the target. See "Reorganize". |
| `find` | a query | Search the index — see *Find*. |
| `add` | a URL | File a new bookmark — see *File a new bookmark*. |
| `audit` | a folder (optional) | Dead / obsolete link sweep + interactive report — see *Audit*. |
| `sync` | — | `bm.py sync` — refresh the index from the live tree. |
| `save` | a message | `bm.py save "<msg>"` — commit and push the index. |

Every writing command still obeys the ceremony table in "Writing changes": a global
restructure (`reshape`, `merge`, bulk `rename`) previews and backs up; a single `add`
does not.

### `help` — what to tell the user

On `help` (and on a bare invocation), give a short orientation in the user's language,
covering these points — not as a raw dump, but tight and readable:

- **What it is.** A companion to Chrome bookmarks: a searchable sidecar index kept next
  to the browser's own store. It lets you find by meaning, file new links, audit for
  dead/obsolete ones, and reorganize whole branches — semantic search plus safe bulk
  edits Chrome's UI has no way to do.
- **The commands**, one line each — reproduce the table above (`reshape`, `rename`,
  `tidy`, `merge`, `find`, `add`, `audit`, `sync`, `save`), with an example invocation
  like `/lodestar:bookmarks reshape Media`.
- **Reads are always safe; writes are careful.** Search and audit run with Chrome open
  and never touch the tree. Any bulk change previews first, backs up the store, and is
  reversible with `bm.py restore`.
- **How writes reach Chrome — the extension.** On a profile signed in with sync (the
  usual case, `bm.py status` shows `AccountBookmarks`), the Bookmarks file cannot be
  edited directly — the sync server would overwrite it. Instead a small **unpacked MV3
  Chrome extension** ("Bookmark Agent Bridge", in `skills/bookmarks/extension/`) performs
  every change through Chrome's own `chrome.bookmarks` API while the browser stays open.
  It talks to the skill over a localhost relay started with **`bm.py bridge`** (127.0.0.1:8787).
  So two things must be live for any write: the bridge process running, and the extension
  loaded in `chrome://extensions` (Developer mode → *Load unpacked*). Check both with
  **`bm.py call ping`** — `{"ok":true}` means ready; an error means reload the extension
  or restart the bridge. First-time setup of the extension and bridge is in
  `references/setup.md`.
- **Where the data lives.** The index, your `profile.md` (personal taxonomy and
  thresholds), and timestamped backups sit in `~/.claude/bookmarks/`, a private git repo
  — nothing bookmark-related is ever written into this public skill repo.
- Point out that everything is a proposal you approve before it runs, and that deletions
  are treated as one-way (they may reach the synced account before any local rollback).

### `reshape` — ask about preferences first

Before analysing anything, ask the user **one** `AskUserQuestion`: *use the current
folder/tree structure to infer your organizing preferences, or start clean?* The
whole-tree read is what made past reshapes fit the user's habits — but someone who wants
a deliberate break, or whose current shape is exactly the mess being escaped, will not
want it. On **yes**, do the preference read in step 1 of *Reshape a branch from a blank
slate*. On **no**, skip that read and group purely by function, letting `profile.md`
alone constrain the result. Only after the answer do you proceed to the taxonomy proposal.

## Modes

Pick from what the user asked. When it is ambiguous, ask.

### Find

1. `bm.py search <terms> -n 60`. Pass several terms — the query is OR'd across
   title, folder path, URL, tags and summary, ranked by BM25.
2. **Expand the query yourself before calling.** This is the single biggest lever on
   result quality, because the index does not stem or translate. Add synonyms, the
   dictionary form of inflected words, the other language (a question in one language
   routinely has to match titles in another), and likely technical spellings. Two or
   three extra terms change results completely; a single-word search is the usual
   cause of a miss.
3. If the header reports `missing>0`, run `bm.py sync` and search again — the user
   added bookmarks in Chrome since the last index update.
4. **If you get few or no hits, do not report a miss. Search again with different
   words.** Retrieval is lexical: a hit requires the words you chose to overlap the
   words in the title, path or tags. One re-expansion is the difference between
   finding nothing and finding the answer at rank 1 — measured, on this design.
   Change register (colloquial ↔ technical), switch language, try the product or
   brand name instead of the function, or the function instead of the brand. Two or
   three attempts before concluding it is not there.
5. Rerank the candidates by actual relevance to the question, drop the noise, and
   group what survives by theme. Use the `summary` column — it says what the page
   gives you, which the title often does not.
6. Answer with **clickable markdown links**, the full folder path, and one short line
   per result saying why it matches. Paths matter: they tell the user where to look
   next time.

`matches=` in the header is the true number of candidates; `shown=` is what `-n`
returned. A large gap means the query is too broad — narrow it rather than paging.

Pass words as separate arguments; they are OR'd. Quoting a whole phrase is not a
grouping shortcut — use `--phrase` when an exact sequence is genuinely wanted.

The search header reports `unenriched`. While that is most of the collection, this is
keyword matching, not semantic search — paraphrases and cross-language queries will
miss things that are there. Say so rather than reporting a clean "not found", and
offer the enrichment pass (`references/index.md`).

### File a new bookmark

**This is the fast path. Adding one bookmark is not a restructure — no backup, no
dry-run, no approval round-trip.** Filing on arrival is the user's habit; the skill
must not make it slower than dragging the star in Chrome.

Given a URL: fetch nothing, infer from the URL and the user's existing taxonomy.

1. `bm.py search` on terms from the URL — brand name, function, and the Russian
   equivalent. This finds where siblings of the same kind already sit and, in the same
   pass, whether the URL is already filed. Zero duplicates is a record worth keeping;
   if it is already there, say where and stop.
2. **One obvious home → just add it.** A folder whose existing contents are the same
   kind of thing is the answer; do not stage a proposal for confirmation.
3. **Two or more plausible homes → ask with `AskUserQuestion`**, one option per
   candidate folder, each labelled with the path and what already lives there. Never
   describe the options in prose and wait for a typed reply — the user picks and the
   add proceeds in the same turn.
4. Create, then refresh:

   ```bash
   bm.py call create --arg '{"node":{"parentId":"<id>","title":"<name>","url":"<url>"}}'
   bm.py sync
   bm.py save "add <name> to <path>"
   ```

   `parentId` is the numeric **id** from `bm.py call tree`, not a guid. On a synced
   profile this is the only write path that survives the next merge — see
   `references/patching.md` ("Live restructuring").

Title: a short clean name, not the raw `<title>` with its `| Site Name` tail. Match the
language convention of the branch it lands in.

Respect whatever `profile.md` records about the root level. Where the top level is a
quick-access row rather than a category system, adding a root or lengthening a name
costs the user something real — check before doing either.

A new entry lands in the index unenriched, so it will not answer function-word searches
until the next enrichment pass. Mention that only if the user is likely to look for it
that way soon.

### Audit

`bm.py check-links` runs the HTTP sweep, caches results in the index, and writes an
**interactive** HTML report — categories ranked by how safe they are to act on, with
a checkbox per row and one per category that marks the whole group for deletion.
Hand over the path rather than pasting rows into the conversation; the user decides
in the report and exports a patch from it, which you then read back, summarize and
apply. The round trip is described in `references/method.md` — do not skip the
summarize step. `bm.py report --html` rebuilds it, `bm.py report` prints the same
grouping as TSV, `bm.py stats` gives folder health.

Report findings, ranked by how safe each group is to act on. Deletion is only ever
proposed, never performed silently. See `references/method.md` for what qualifies as
a deletion candidate — the rules are specific and age alone is not one of them.

### Reorganize

Optimize for whatever `profile.md` says the user values — for most people who let a
tree grow for years, that is **access speed over taxonomic purity**, but ask rather
than assume. Measure before and after with `bm.py stats`: average depth, deep
bookmarks, and thin folder count are the metrics that move.

Work one branch at a time. Show the proposed changes as a readable list, get approval,
then build the patch. See `references/method.md`.

When the user wants a branch redesigned from scratch — "if these were a flat pile with
no folders, how would you organize them?" — that is the **global reorganization**
capability: read their preferences off the whole tree, propose a full taxonomy for
approval, then execute it as a phased id-based migration. Steps are in
`references/method.md` ("Reshape a branch from a blank slate").

## Writing changes

**Scope the ceremony to the risk.** Adding a single bookmark, or renaming one, is a
one-liner — use the fast path above and skip everything in this section. The review
and backup discipline below exists for **global actions**: reorganizing a branch,
moving bookmarks in bulk, and any deletion. Those are the operations that can lose
years of curation; a single `create` cannot.

| Action | Backup | Preview + approval |
|--------|--------|--------------------|
| Add one bookmark, rename one node | no | no |
| Move a handful of bookmarks | no | show the list |
| Reorganize a branch, bulk move, any delete | **yes** | **yes** |

For those global actions, always in this order:

1. Compose the patch while Chrome is open — computing is free, writing is not.
2. `bm.py apply patch.json --dry-run` and show the user the resulting action list
   together with the node-count line.
3. Get explicit approval.
4. Ask the user to quit Chrome. `bm.py apply` refuses to write while it runs.
5. `bm.py apply patch.json` — it backs the file up, verifies what landed on disk, and
   rolls back automatically if the result is not what the ops accounted for.
6. Tell the user they can reopen Chrome, then `bm.py sync` and `bm.py save "<what changed>"`.

**Every change is recoverable, one step at a time.** `bm.py backups` lists snapshots
with node counts; `bm.py restore --last` undoes the most recent write, and taking that
step saves the current state too.

**Deletion is different.** With Chrome sync enabled, a deletion may reach the account
before any rollback happens, and the interaction between external edits and Chromium's
sync metadata is not verified — see the sync section of `references/patching.md` for
the safe procedure. Walk through it before any patch containing `delete`.

**On a profile signed in with sync, this file flow does not apply.** The sync server
rewrites the Bookmarks file back on the next merge, so writes must go through the Chrome
extension by node id — `bm.py exec`, with Chrome left open — not `bm.py apply`. `apply`
refuses when `AccountBookmarks` exists. The live path, and the phasing that makes a
multi-step restructure safe, are in `references/patching.md` ("Live restructuring").

Patch format and every operation are documented in `references/patching.md`.

## Index maintenance

The index is the user's data and lives in their private data directory, which is a git
repository. After any change to `index.jsonl`, commit and push with
`bm.py save "<message>"`. Never write the index, backups, or anything derived from the
user's bookmarks into this skill's repository — it is public.

Schema, the enrichment procedure, and batching guidance are in `references/index.md`.

## References

- `references/setup.md` — first-run bootstrap, data directory, profile creation
- `references/index.md` — index schema, enrichment pass, keeping it fresh
- `references/method.md` — the four modes in detail, deletion rules, folder health
- `references/patching.md` — patch operations, write safety, recovery
