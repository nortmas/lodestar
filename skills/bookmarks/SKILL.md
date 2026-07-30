---
name: bookmarks
description: Search, file, audit and reorganize Chrome bookmarks via a sidecar index
disable-model-invocation: true
---

# Bookmarks

Runs only when explicitly invoked as `/lodestar:bookmarks` — never auto-triggered.

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
any session that touches bookmarks: it reports the profile path, index size, whether
Chrome is running, and whether the safety guard has been disabled.

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

Given a URL: fetch nothing, infer from the URL and the user's existing taxonomy.
Find the folder where sibling bookmarks of the same kind already live —
`bm.py search` on terms from the URL is the fastest way to see where similar things
sit. Propose one destination plus a fallback, then build an `add` op.

Respect whatever `profile.md` records about the root level. Where the top level is a
quick-access row rather than a category system, adding a root or lengthening a name
costs the user something real — check before doing either.

### Audit

`bm.py report` prints cleanup candidates grouped by reason, plus folder health.
`bm.py stats` gives the health metrics. `bm.py check-links` runs the HTTP sweep and
caches results in the index.

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

## Writing changes

Always in this order:

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
