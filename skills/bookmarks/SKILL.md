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

This skill is invoked explicitly (`/lodestar:bookmarks …`) and never auto-triggers.

**First, check whether it is set up.** Run `bm.py status`. If `profile.md` is missing or
the index is empty, this is a **first run** — ignore whatever command was typed and go to
*First run* below. Do not print a help screen or try to act on a folder before setup
exists.

If it is set up, read the **first word** of the invocation as a command and the rest as
its target, then follow the section it points to. **With no command, present `help`
(below) and the one-line state from `bm.py status`**, so the user sees what they can do
and that it is ready. An unrecognized first word → show `help` and ask, do not guess.

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

### First run — set it up *with* the user

A missing `profile.md` or empty index means nothing is configured yet. Do **not** make
the user learn commands or read setup docs — drive it yourself, running each step and
asking only what you cannot infer from their tree. The full script is
`references/setup.md`; the shape:

1. Say hi and, in one line, what this is.
2. Create the data directory — `references/setup.md` §1.
3. **Learn how they sort — this is the important part.** Run `bm.py profile-scan` (it
   reads their existing bookmark tree and reports what it reveals), then ask the short
   interview questions from setup.md: what each top folder is for, what must never be
   deleted, their language/naming habits, where unsorted links land. Write `profile.md`
   and `config.json` from the answers. Everything the skill does later is governed by
   this, so do not skip it or invent conventions — quote their own tree back and ask
   about the rest.
4. Build the search — `bm.py sync` for the first index — then offer the enrichment pass
   (`references/index.md`) that makes search-by-meaning work.
5. On a synced profile, **turn on the Chrome helper** (the three steps in `help` /
   setup.md §9) so edits are possible. Skip on an unsynced profile.
6. `bm.py backup "baseline"`, and tell them `bm.py restore --last` undoes any step.

Then say it's ready and show `help`. Keep it conversational — one thing at a time, a
question at a time, never a wall of steps.

### `help` — what to tell the user

On `help` (and on a bare invocation), give a short, plain-language orientation in the
user's language. **No jargon** — a smart 12-year-old should follow every line. Do **not**
mention sync, `AccountBookmarks`, MV3, the `chrome.bookmarks` API, node ids, the bridge
port, or *why* the file can't be edited directly. That is plumbing; the user only needs
to know what they can do and that it is safe. Cover:

- **What it does, in one breath.** Something like: "I help you tidy your Chrome
  bookmarks — find any link just by describing it, save new ones into the right folder,
  clear out dead links, and reorganize whole folders. Things the bookmarks menu can't do."
- **First time? Just run it — I set everything up with you.** Say plainly that on the
  first run they don't need to know any commands: "I'll look at your current bookmarks,
  ask you a few short questions about how you like them sorted, build the search, and help
  you switch on a small Chrome helper. You just answer the questions — takes a couple of
  minutes." The only thing they do by hand is turning on the helper:
  1. In Chrome, open `chrome://extensions`.
  2. Turn on **Developer mode** (switch, top-right).
  3. Click **Load unpacked** and choose the folder
     `~/.claude/skills/lodestar/skills/bookmarks/extension`.
  Then it's ready. If I ever say I can't reach your bookmarks, this helper just needs
  switching back on there.
- **The commands, as a table** — a `Command | what it does` grid (like the Commands
  table above), one plain-language line each: `reshape` = re-sort a folder from scratch;
  `rename` = give everything short, clear names; `tidy` = quick cleanup; `merge` =
  combine folders; `find` = search; `add` = save a link; `audit` = find broken links;
  `sync`/`save` = keep everything saved. Put one real example under it
  (`/lodestar:bookmarks reshape Media`).
- **It's safe.** "Looking things up never changes anything. Before I change or delete
  anything I show you exactly what I'm about to do and wait for your OK — and I keep a
  backup, so any change can be undone."
- **Your stuff stays yours.** "Everything lives in a private folder on your own
  computer — nothing about your bookmarks is ever shared or made public."

Keep the whole thing to about a screen. Detail on demand, not by default.

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
