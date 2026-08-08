# Patching

Every write goes through a patch file. Nothing edits the Bookmarks JSON directly.

## Format

```json
{"ops": [
  {"op": "mkdir",   "name": "Languages", "to_guid": "<folder guid>"},
  {"op": "move",    "guid": "<node guid>", "to_guid": "<folder guid>"},
  {"op": "rename",  "guid": "<node guid>", "title": "New name"},
  {"op": "add",     "url": "https://…", "title": "…", "to_guid": "<folder guid>"},
  {"op": "delete",  "guid": "<node guid>"},
  {"op": "reorder", "guid": "<folder guid>", "order": ["<guid>", "<guid>", …]}
]}
```

Operations run in order. `move`, `rename` and `delete` work on folders and bookmarks
alike — a folder guid moves the whole subtree.

Unknown keys on an op are ignored, which is deliberate: patches exported from the
cleanup report carry `title`, `path` and `category` alongside each `guid` so a human
or a model can see what a patch does without resolving identifiers. Keep that habit
when you author a patch by hand — a delete list of bare guids is unreviewable.

Targets take `to_guid` (preferred) or `to_path` as an array starting with the root key:
`["bookmark_bar", "Work", "DevOps"]`. Use `to_guid` wherever possible — folder names
can contain `/` and other separators, and an array avoids the ambiguity entirely.

A `mkdir` earlier in the same patch cannot be targeted by guid from a later op, because
the guid does not exist until the patch runs — target it by `to_path` instead. `mkdir`
is idempotent: if a folder of that name already exists in the destination it is reused
and logged as such, so `mkdir` + `to_path` in one patch is safe and never produces a
duplicate folder.

Operations that would destroy data are rejected before anything is written:

- moving a folder into itself or into one of its own descendants
- targeting a bookmark instead of a folder (Chromium drops `children` on url nodes)
- moving, renaming or deleting one of the three Chrome root folders
- adding anything that is not an `http://` or `https://` URL
- a `to_path` where any segment matches more than one sibling folder — two folders
  can legitimately share a name, so the tool refuses to guess and asks for a guid

Get guids from `bm.py folder <fragment>` — it lists folders and bookmarks with a
leading `kind` column, so a destination folder guid comes straight out of it.
`bm.py search` returns `parent_guid` as its second column, which is usually the
destination you want when filing next to a sibling. `bm.py tree` gives the whole
folder skeleton but costs several thousand tokens, so reach for it last.

`add` refuses a URL that is already bookmarked anywhere in the tree, naming where it
lives; pass `"allow_duplicate": true` on the op to override. The comparison ignores
scheme, `www.`, host case, a trailing slash and tracking parameters, so the `https://`
version of a page saved years ago as `http://` is caught. The URL is stored exactly as
given — normalization is only for the comparison.

## Applying

```bash
bm.py apply patch.json --dry-run     # prints the action list, writes nothing
bm.py apply patch.json               # refuses while Chrome runs
```

Every run, in this order: count the nodes, apply the ops in memory, **check the node
count moved by exactly what the ops account for**, back the file up and verify the
backup parses, write via a temp file and rename, then re-read the written file and
confirm it holds what was intended. If the read-back disagrees, the backup is copied
straight back and the command fails.

The integrity check is what catches the class of bug where an operation quietly loses
a subtree — the tree stays valid JSON with a correct checksum, so nothing else would
notice. If it ever trips, nothing has been written; report the numbers rather than
retrying.

The dry run is not optional. Show its output to the user and get approval before the
real run — it is the only readable "before/after" that exists, since Chrome's UI has
no diff.

## Live restructuring via `exec` — synced profile, Chrome open

The `apply` flow above rewrites the Bookmarks file and needs Chrome closed. It does not
work on a profile signed in with sync: the sync server rewrites the file back on the
next merge, silently undoing a file edit (proven twice — a delete got resurrected, and
re-enabling sync after an edit duplicated the tree). When `AccountBookmarks` exists
(`bm.py status` shows it as the bookmarks file, and `apply` refuses), writes go through
the browser extension instead, by node **id**, while Chrome stays open:

```bash
bm.py exec ops.json          # preview (default) — prints the action list
bm.py exec ops.json --go     # backs up the account store, then applies via the extension
```

Op shape — ids come from `bm.py call tree`, not guids:

```json
{"ops": [
  {"op": "move",   "id": "5305", "parentId": "7966"},
  {"op": "move",   "id": "7964", "parentId": "5268", "index": 4},
  {"op": "update", "id": "7538", "title": "Finance"},
  {"op": "remove", "id": "7540"}
]}
```

`exec` has no create op. Make folders with
`bm.py call create --arg '{"node":{"parentId":"<id>","title":"<name>"}}'`, which returns
the new id. A standalone `create` does **not** back up (only `exec --go` does), so take
a backup before a batch of creates.

Two rules make a multi-step restructure safe:

- **Build by id and pre-check.** Fetch a fresh `call tree`, index it by id, and assert
  every source and target id in the op list is present before writing. A missing id
  means the tree drifted since you planned — stop, do not write.

- **`exec` validates the whole list against ONE snapshot taken before it runs.** A
  `remove` is checked for emptiness against that snapshot, so you cannot empty a folder
  and remove it in the same run — the snapshot still shows its children and `exec`
  refuses. Split the work into phases and re-fetch the tree between them. Nested empties
  therefore collapse one level per phase: emptying inner folders in phase N leaves their
  parent empty for phase N+1. Do the folders-first reorder (re-`move` with an explicit
  `index`) in the final phase, once the folder set has settled.

Each phase is preview → show the user → `--go`. `--go` backs up the account store first,
so every phase is independently recoverable via `bm.py backups` / `restore`. A folder
`remove` only ever succeeds on an empty folder — `chrome.bookmarks.remove` refuses a
non-empty one — which is a safety net, not an obstacle: it is why the phasing is forced.

## Why Chrome must be closed

Chrome holds the bookmark tree in memory and rewrites the file on exit. Edits made
while it runs are silently discarded at shutdown. `apply` and `restore` both check and
refuse, and the check **fails closed**: if it cannot determine whether Chrome is
running, it assumes it is.

The `BM_ALLOW_RUNNING=1` escape hatch exists for exercising the write path against a
copy of the file. It must never be used against a live profile. `bm.py status` reports
in red when it is set.

## Sync — treat deletions as one-way until proven otherwise

`sync_metadata` at the top of the Bookmarks file is Chromium's per-entity sync tracker.
An externally applied patch leaves it inconsistent: deleted nodes keep orphan entries
and new nodes have none. Chromium validates it on load and, on mismatch, discards it
and performs an initial merge against the server — a *merge*, in which entities the
server still knows about can be **re-created locally**.

This has not been verified empirically on a live profile. Until it is, do not promise
the user that a deletion sticks, and do not promise that it propagates either. The
safe procedure for any patch containing `delete`:

1. Pause bookmark sync in `chrome://settings/syncSetup`.
2. Quit Chrome.
3. `bm.py apply`.
4. Reopen Chrome and confirm the tree looks right.
5. Re-enable sync.

Say plainly, before any deletion: the local backup restores this machine, and it does
not necessarily undo what has already reached the account. Treat deletion as an
outward-facing action needing explicit approval — not implied consent from an earlier
"yes".

## Recovery

```bash
bm.py backups            # every snapshot, node counts, why it was taken
bm.py restore --last     # roll back one step
bm.py restore Bookmarks.<timestamp>
```

A backup is taken before every `apply`, and also before every `restore` — rolling back
is itself a change, and the state you are leaving may turn out to have been the good
one. Backups are pruned to `backup_keep` (default 30, never below 5) and each carries
a `.info` sidecar with its node count, so `bm.py backups` shows at a glance which
snapshot predates a loss.

`restore` works even when the current Bookmarks file is unparseable — a file truncated
by a crash or a full disk is exactly the case it exists for, so it treats what it is
replacing as opaque bytes and snapshots it anyway. It does validate the backup it is
restoring *from*, and refuses if that one is corrupt.

If the integrity check reports a mismatch, it names the first op whose real effect
differed. The usual cause is two ops in one patch touching the same subtree — for
example deleting a folder and separately deleting a bookmark inside it. Split them or
drop the redundant one; do not retry the same patch.

Chrome also keeps its own `Bookmarks.bak` next to `Bookmarks`, holding the state at the
last clean startup. It is a second net, not a substitute — it is overwritten on every
launch.

After restoring, run `bm.py sync`: the index still describes the tree you just undid.

## After applying

1. User reopens Chrome.
2. `bm.py sync` — paths in the index catch up with the moves.
3. `bm.py save "<what changed>"` — commit and push the index.

If step 2 refuses because too many indexed bookmarks are missing, do **not** reach for
`--prune`. That guard exists precisely for the case where something went wrong; check
the profile path in `bm.py status` first.
