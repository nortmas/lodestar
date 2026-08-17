# Comment layer (review engine)

The click-to-comment margin cards baked into `assets/report-template.html`. This
documents exactly what the engine `<script>` implements. It is adapted from the
cookbook recipe `click-to-comment-html-review`, with two changes: content-hash
anchors instead of positional ids, and cards anchored to the element instead of a
point (no `xPct`/`yPct`).

## Gating

The engine is gated by the root attribute `<html data-review="on|off">`, filled from
the `{{REVIEW_MODE}}` slot.

- **`on`**: local-file review mode. The margin cards, toolbar, and click-to-comment
  are active.
- **`off`**: Artifact / read-only. The engine no-ops after the theme toggle
  (`if(document.documentElement.getAttribute('data-review')!=='on') return;`). The
  toolbar, gutter, and sheet button are hidden by CSS, and the content column
  centres with no reserved gutter.

The theme toggle button runs in both modes. Everything else is review-only.

## Anchoring: content-hash ids

On load, `assignAnchors()` gives every element matching `ANCHOR_SEL` a
content-hash id `data-cm-anchor="h<hash>"`. The hash is djb2 over the element's
trimmed `textContent`, first 120 chars. Collisions get a `_1`, `_2` suffix.

```
ANCHOR_SEL = '.vr-item, .vr-topn-row, .vr-metric, .vr-section > h2, .vr-explain, .vr-evidence, .vr-drill-body p, figcaption.vr-figcaption'
SECTION_SEL = '.vr-section > h2'
```

`SECTION_SEL` labels each comment with its section: `sectionOf(el)` walks the `<h2>`
headings with `compareDocumentPosition` and strips a leading number.

Content-hash ids are **stable across regeneration**, unlike positional ids. If the
report is rebuilt and an element's text is unchanged, its anchor id is unchanged, so
a comment on it survives. This is the key change from the cookbook original, whose
`a17` ids shifted whenever an element was inserted above.

## Storage and transport

Two stores, reconciled by fingerprint:

- **`#vr-seed`**: a `<script type="application/json" id="vr-seed">` block. The baked
  transport, written on "Save & download", read on open. Empty `[]` in the master
  copy. This is what makes the downloaded file self-contained.
- **`localStorage`**: the working copy, key
  `visual-report:<location.pathname slugified>`. Written on every edit so a stray
  reload costs nothing.

Reconciliation by fingerprint (djb2 hash + length of the seed JSON): on open, if the
stored fingerprint matches the file's seed, the reader has already worked on this
exact file, so their localStorage copy wins. If the fingerprint differs or is
absent, the seed is imported and the new fingerprint stamped. Net effect: **first
open imports the seed, then localStorage wins.**

After reconciliation, comments whose anchor no longer resolves are dropped
(`comments.filter(function(c){return c&&c.anchor&&anchorEl(c.anchor);})`).

"Save & download" (`buildAnnotatedHtml`) clones the document, strips the live card
nodes, writes `JSON.stringify(ordered(), null, 2)` into `#vr-seed`, and serves a
self-contained `.html` blob named `<file>-review.html`.

## Comment schema

Exactly as the engine writes it:

```json
{
  "id": "c_k3f9a2x_m8q1",
  "anchor": "h1a2b3c",
  "section": "Authentication",
  "quote": "Google SSO logs a user in on email match alone",
  "text": "Is email_verified actually checked upstream?",
  "status": "needs_agent_review",
  "replies": [
    { "author": "reviewer", "text": "Confirmed, no check.", "at": "2026-08-17T10:00:00.000Z" }
  ],
  "createdAt": "2026-08-17T09:50:00.000Z",
  "updatedAt": "2026-08-17T09:58:00.000Z"
}
```

- `status` is one of `needs_agent_review | needs_user_reply | resolved`.
- `quote` is the anchor element's trimmed text, first 80 chars.
- `createdAt` is set on create; `updatedAt` is set on edit and on status change.
- `replies[]` items are `{ author, text, at }`. A reviewer reply sets
  `author: "reviewer"`.

**No `xPct` / `yPct`.** Unlike the cookbook original, the report engine anchors a
card to the element, not to a point inside it, so it stores no percentage offset.

## UI

- **Wide screens (> 1100px):** margin cards render in the right gutter column
  (`#vr-gutter`), each positioned at its anchor's top. `positionCards()` de-collides
  downward: a card never overlaps the one above it.
- **Narrow screens (<= 1100px):** the gutter is hidden and cards collapse to a
  bottom sheet (`#vr-sheet`), toggled by the floating "Comments" button
  (`#vr-sheet-btn`). Cards render in static flow, no positioning.
- **Status chip** is click-to-cycle: each click advances
  `needs_agent_review → needs_user_reply → resolved → needs_agent_review`.
- **Per card:** Reply, Edit, Delete. Reply uses a one-line `window.prompt` and sets
  the card back to `needs_agent_review`. Clicking a card body (not a button) scrolls
  to and flashes its anchor.
- **Toolbar:** Theme, Clear all, Save & download. A count badge shows the comment
  total.

## The round-trip

1. You deliver a local `.html` with `data-review="on"`.
2. The reviewer opens it, clicks any commentable block, types a comment.
3. The reviewer hits **Save & download** and sends the baked `.html` back.
4. You read the `#vr-seed` JSON from that file to ingest the comments.

Live agent-reply-in-document is **not implemented** (that is v2). The `status` and
`replies` fields already exist so the future mode needs no format change: an agent
would set `status: needs_user_reply` and push a reply, and the same file round-trips.

## Gotchas

- **Content-hash anchors change if an element's text changes.** Editing report copy
  after comments exist can orphan a comment: the hash no longer matches, and the
  engine drops comments whose anchor no longer resolves. **Freeze the report before
  circulating it.** Small unavoidable edits can be re-attached by hand via the
  `quote` field. (This is milder than the cookbook's positional ids, where inserting
  any element shifted every later id.)
- **localStorage is keyed by path.** A copy of the file at a different path gets its
  own store, so duplicating a review file for a second reviewer is safe. Renaming or
  moving the file starts a fresh store, so save before moving.
- **Artifact mode cannot round-trip comments.** The published Artifact sandbox blocks
  page-initiated downloads, so "Save & download" does not work there. Artifact mode
  ships read-only with the engine off (`data-review="off"`). For the review
  round-trip, deliver a local file.
- **Margin cards need gutter width.** Below 1100px there is no room for the gutter,
  which is why the cards fall back to the bottom sheet.
