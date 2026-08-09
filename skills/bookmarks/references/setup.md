# First-run setup

Setup is an **interview**, not a form. The tree already encodes how its owner thinks;
your job is to read that back to them and ask about the parts you cannot infer.
Never present a generic questionnaire, and never guess a rule you could ask about.

## 1. Data directory

Everything personal lives outside this repository, by default in
`~/.claude/bookmarks/` (override with `BM_DATA_DIR`):

```
config.json        settings and thresholds — committed
config.local.json  machine-specific overrides — gitignored
profile.md         taxonomy rules in prose, read before every proposal — committed
index.jsonl        one line per bookmark — committed
index.db           FTS5 index rebuilt from index.jsonl — gitignored
backups/           timestamped copies of the Bookmarks file — gitignored
```

The directory should be a **private** git repository. Bookmark collections expose
finances, health, employer, and home address; a public repo is not an option. Confirm
the remote is private before the first push.

```bash
git clone <private-remote> ~/.claude/bookmarks   # or: git init && git remote add origin …
cat > ~/.claude/bookmarks/.gitignore <<'EOF'
index.db
backups/
config.local.json
EOF
```

`config.json` and `profile.md` are committed on purpose: the answers to the interview
are as valuable as the index, and losing them means doing it again. Anything tied to
one machine — the Chrome profile name, an absolute `bookmarks_file` path — belongs in
`config.local.json` so a second machine can override it without a merge conflict.

## 2. Read the tree before asking anything

```bash
bm.py profile-scan
```

This prints observations only: root order and name lengths, bare links at root level,
subfolder names reused across branches, language distribution, staging and archive
candidates, and health counts at the current thresholds.

Read it properly. Every block is a question you no longer have to ask blind, and an
observation you can quote back — which is what makes the interview feel like a
conversation instead of an intake form.

## 3. The interview

Ask in rounds of two to four questions, grounded in what the scan showed. Offer a
recommended answer whenever the tree implies one. Stop when you can write the profile
without inventing anything.

### Round 1 — what each root is for

The single most important round, and the one you cannot skip. For each top-level
folder, you need three things: **what goes in it**, **what role it plays**, and
**how long things stay**.

Ask about the roots whose purpose is not obvious from the name, and confirm the ones
that are. Useful framings, adapted to what you saw:

- "You have N top folders. Which of them are work, which are personal, and which are
  reference material you keep regardless of any project?"
- "Is any of these meant for things that are only relevant right now — a folder you'd
  expect to empty out over time?" → that is the staging root, and it needs a TTL.
- "Is there a folder where finished things go instead of being deleted?" → archive.

Roles map to retention policy, which is what the audit later acts on:

| Role | Meaning | Retention |
|------|---------|-----------|
| `project` | tied to something with an end | leaves when the thing ends |
| `area` | ongoing responsibility, no end date | stays while the responsibility does |
| `resource` | reference material | stays indefinitely; age means nothing |
| `archive` | finished, kept for retrieval | stays, never surfaced by default |

If the scan found a staging folder, ask **how long is too long** for something to sit
there. That number becomes `hot_ttl_days`.

### Round 2 — the shape and why it is that shape

The scan tells you the shape; only the user can tell you the reason, and the reason is
what constrains future proposals.

- **Root order.** If it is not alphabetical, ask what the order means. Priority?
  Frequency? Something else? Reordering roots is off-limits until you know.
- **Root name length.** If names are conspicuously short, ask why. "Fits on a small
  screen" is a hard constraint that forbids adding roots and lengthening names — very
  different from someone who just likes short names.
- **Bare links at root level.** If the scan found them, ask whether that row is a
  quick-launch strip. If so it is not taxonomy and must never be reorganized.
- **Depth tolerance.** Show the depth histogram and the count of deep bookmarks, then
  ask the trade-off directly: is a correct-but-deep hierarchy better than a rough
  shallow one, or the reverse? This answer governs every reorganization proposal.

### Round 3 — language and naming

- If the scan shows mixed scripts, ask whether the split follows a rule — certain
  topics in one language, the rest in another — or whether it just happened. A rule
  must be preserved; an accident may be worth normalizing.
- Ask about casing and separators only if the scan shows inconsistency.
- Ask whether bookmark titles are theirs to rewrite. Some people keep raw page titles
  deliberately; others have been hand-shortening for years. Look at the title length
  distribution before asking — if a good share are very short, they have a habit, and
  the question is whether to apply it to the rest.

### Round 4 — deletion

This is where trust is won or lost, so be concrete.

- "What would you never want deleted, even if it is ancient and you have never opened
  it?" → the evergreen categories.
- "Is there a technology or a period in here that is simply over?" → the one bulk
  deletion category worth pursuing.
- "For links that are dead: delete outright, or list for review?" Some people want
  404s gone without ceremony; nobody wants a 403 deleted.

Say plainly, before any of this: **age alone is not a reason to delete**, and if sync
is on, deletions travel to every device.

### Round 5 — thresholds

Only after the above. Show the counts from the scan at the current defaults and ask
whether they look right. The numbers are meaningless in the abstract and obvious in
context: "172 folders hold 2 or fewer bookmarks — should those be collapsed, or are
small folders intentional?"

Defaults to confirm or change:

| Key | Default | Question it answers |
|-----|---------|--------------------|
| `cold_days` | 1095 | how long untouched before it is worth a look |
| `thin_folder_max` | 2 | how small is too small for a folder to exist |
| `deep_level` | 5 | how many clicks is too many |
| `fat_folder_min` | 21 | how big before a folder should split |
| `hot_ttl_days` | 180 | how long something may sit in staging |

## 4. Write the config

```json
{
  "profile": "Default",
  "hot_folder": "Hot",
  "archive_folder": "Archive",
  "thresholds": {
    "cold_days": 1095,
    "thin_folder_max": 2,
    "deep_level": 5,
    "fat_folder_min": 21,
    "hot_ttl_days": 180
  }
}
```

Omit `hot_folder` when there is no staging root — the audit simply skips that section.
Machine-specific keys (`profile`, `bookmarks_file`) go in `config.local.json` if the
repo is shared across machines.

Find Chrome profiles with:

```bash
find ~/Library/Application\ Support/Google/Chrome -maxdepth 2 -name Bookmarks -not -name '*.bak'
```

## 5. Write profile.md

Prose, in the user's own words where possible. This is what you read before every
proposal, so write it to be re-read, not to be complete.

```markdown
# Bookmark profile

## Roots
| Folder | Contains | Role | Retention |
|--------|----------|------|-----------|

## Hard constraints
- <things that must never happen, and why — the "why" is what makes them stick>

## Naming and language
- <casing, language rule, title policy>

## Lifecycle
- <what moves where when it goes stale>

## Deletion
- <always safe / never touch>

## Open questions
- <anything the user was unsure about — revisit rather than assume>
```

Show it and let them correct it. Expect corrections; that is the point.

## 6. First index

```bash
bm.py sync                 # every bookmark gets a record
bm.py save "initial index and profile"
```

At this point search is **keyword matching only**. It finds what it is literally
spelled, which is genuinely useful, but it is not the semantic search the skill
promises: a paraphrase, an inflected word, or a query in the other language will miss
things that are sitting right there.

## 7. Enrichment — the step that makes search work

Do not present this as optional polish. Present the cost, then do it:

```bash
bm.py dump --limit 100                # read the batch, write JSONL, then:
bm.py ingest batch.jsonl
```

Repeat the same two commands until `dump` reports `0 bookmarks in this batch`. Never
add `--offset`: `dump` is a queue that already excludes enriched records, and paging it
would skip work while still terminating cleanly. It is resumable across sessions, so
an interrupted run costs nothing.

Quote both sides of the cost before starting — roughly 60 input and **90 output**
tokens per bookmark, and output is the expensive half. Commit every few batches with
`bm.py save`.

Field definitions and what makes a good tag are in `index.md`.

## 8. Confirm the safety net

```bash
bm.py status      # profile path, index size, Chrome state, backup count
bm.py backup "baseline before any changes"
```

Take that first backup before the user's first write session, and tell them
`bm.py restore --last` is how they undo a step. `backup_keep` in `config.json` controls
retention (default 30, never below 5).

## 9. The Chrome helper — only if the profile is synced

Skip this on an unsynced profile: `bm.py apply` writes the file directly and no helper is
needed. If `bm.py status` shows the bookmarks file as `AccountBookmarks`, the profile is
signed in with sync and every write must go through the browser extension instead (see
`references/patching.md`, "Live restructuring"). Two pieces:

**The bridge** — a localhost relay between the skill and the extension. You do **not**
start it by hand: any `bm.py call`/`exec` runs `ensure_bridge()` first, which spawns a
detached `bm.py bridge` on 127.0.0.1:8787 if nothing is listening and waits for it to come
up (log at `~/.claude/bookmarks/bridge.log`). It then stays running across sessions until
the machine reboots or it is killed (`pkill -f "bm.py bridge"`). Start it manually only to
debug:

```bash
bm.py bridge        # 127.0.0.1:8787
```

**The extension** — loaded once by the user, in plain terms:

1. Open `chrome://extensions`.
2. Turn on **Developer mode** (top-right).
3. **Load unpacked** → choose
   `~/.claude/skills/lodestar/skills/bookmarks/extension`.

It appears as **"Bookmark Agent Bridge"**. Leave it enabled. It self-heals: a
`chrome.alarms` wake fires every minute so the worker reconnects to the bridge on its own
after the bridge restarts or Chrome reaps the idle worker — no clicking required. Chrome
may still fully switch off an unpacked extension between restarts; if writes stop for good,
re-enable it here.

Confirm the whole path end to end:

```bash
bm.py call ping     # {"ok":true} means bridge + extension are both live
```

`{"error":"extension not connected"}` means the bridge is up but the extension has not
(re)connected yet — normal for up to a minute right after the bridge auto-starts from cold,
because the worker reconnects on its once-a-minute alarm. If it persists, reload the
extension at `chrome://extensions`. A connection-refused error should not happen now that
`bm.py` auto-starts the relay; if it does, the relay failed to launch — run `bm.py bridge`
by hand to see the error.
