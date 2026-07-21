---
name: design-variations
description: Generate a specified number of genuinely distinct design variations of
  a UI element or page, packaged as a single self-contained interactive HTML
  artifact with click-to-comment feedback, localStorage persistence, and JSON
  export. Use when the user asks to explore design alternatives, produce options
  for review, iterate on a component's look, or create pickable options for a UI
  decision. Variations are styled from the project's own live design system
  (discovered per run — never a hardcoded guide) and obey the project's documented
  styling rules if any. Triggers on '/lodestar:design-variations'. Pairs with
  '/lodestar:design-fresh', which decides the creative direction the variations
  explore.
---

# Design Variations

Produce N visually distinct design variations of a referenced element or
description, rendered in one self-contained HTML artifact with a built-in
feedback overlay. The reviewer opens the file in a browser, clicks anywhere on
any variation to leave a comment, and exports all feedback as JSON.

This skill is the **packaging mechanism**. For the *creative direction* of the
variations — a real aesthetic reset, trend research, and cross-session memory so
the set does not repeat past projects — run `/lodestar:design-fresh` first and
feed its chosen "worlds" in as the variations to render.

## When to use

Trigger on requests like:
- "Create 4 design variations for the pricing card."
- "Give me 3 options for the table header."
- "Show me a few ways this button could look."

Do NOT use for:
- Implementing an accepted design — that is product code; run it through the
  project's workflow (offer `/lodestar:workflow`).
- One-off styling tweaks to a single existing component — just edit it.

## Hard rules

1. **Discover the project's design system every run.** Never hardcode hex values
   or font names. Read `references/design-system-discovery.md` and extract live
   tokens from whatever the project actually uses (Tailwind config, CSS custom
   properties, a design-token file, existing components, a mockup/Storybook if
   present). Express variations against those tokens.
2. **Obey the project's own styling rules if it has any** (`.claude/rules/`,
   `CLAUDE.md`, a style guide, `CONTRIBUTING.md`). If none exist, follow the
   discovered design system and general good taste.
3. **Use the template verbatim.** Copy `assets/template.html` and only substitute
   the `{{...}}` placeholders. Do not reimplement the feedback overlay; changes to
   it go into the template, not per-artifact.
4. **Variations must be genuinely distinct.** Apply the Distinctness Test in
   `references/ux-principles.md`. If two variations differ only in padding or a
   shade, one does not belong.
5. **Save to a project-appropriate location.** Prefer an existing docs/design
   directory; otherwise create a `design-variations/` folder at the project root.
   Ask if the right location is unclear. Never scatter files at random.

## Workflow

### Step 1 — Confirm the brief

Confirm in one message: the **target element** (component name, path, or
description), the **number of variations** (default 3 — ask if unclear), and any
**constraints** (must fit one row, dark surface, shown at a given size). Ask one
clarifying question at a time; do not batch.

### Step 2 — Discover the live design system

Follow `references/design-system-discovery.md`. Read the token source(s) the
project actually uses and 1–3 representative components closest in role to the
target, so variations riff on the established design rather than re-propose it.
Note the project's radius/shadow language, spacing rhythm, and fonts.

### Step 3 — Plan the axes

Read `references/ux-principles.md`. Pick 2–3 orthogonal variation axes for the set
(emphasis, depth, density, shape language, framing, accent placement). Each
variation sits at a distinct point on those axes. Write the axis choice per
variation before coding — it becomes the `dv-variation-desc`.

### Step 4 — Generate the artifact

1. Read `assets/template.html` (the only template) and
   `assets/variation-example.html` (the exact per-variation structure).
2. Copy the template to `<chosen-dir>/<slug>.html`, `<slug>` kebab-cased from the
   target element (append `-v2`, `-v3` if it exists).
3. Replace placeholders:
   - `{{ARTIFACT_TITLE}}` — human title, e.g. `Pricing card — 3 variations`.
   - `{{ARTIFACT_ID}}` — the slug (localStorage key).
   - `{{FONT_LINKS}}` — any webfont `<link>`/`@import` the discovered design system
     needs (leave empty to fall back to the system stack).
   - `{{TOKENS_COLORS}}` — the live-extracted colours, keyed by the project's own
     token names, injected into `tailwind.config.theme.extend.colors`.
   - `{{TOKENS_FONTS}}` — same for `fontFamily`.
   - `{{VARIATIONS}}` — the N `<section>` blocks, each matching the example.
4. Each variation: unique `data-variation` slug, a human `data-variation-label`
   used in exported JSON, and a `dv-variation-title` + `dv-variation-desc` naming
   the design decision it tests. Style with the project tokens — no inline hex,
   no font family outside the discovered system.

### Step 5 — Self-critique before handing off

Re-read the variations and verify: the Distinctness Test passes for every pair;
there is at least one conservative and one bolder option; all variations still
read as this project; the accessibility floor in `references/ux-principles.md` is
met. Regenerate any variation that fails.

### Step 6 — Hand off

Report the absolute path, how to open it (`open <path>` — static file, no
server), a one-sentence summary per variation (what decision each tests), and a
reminder the reviewer can click to comment, click a pin to edit/delete, Export
JSON, or Clear. If the target is normally dark, note the artifact renders the
light-mode tokens by default and offer a dark pass.

**Note the CDN dependency.** The template loads Tailwind and any webfont from a
CDN, so the artifact needs a network connection and a chosen webfont can silently
fall back to a system font. If a variation depends on a specific typeface, open
the file yourself and confirm the font actually applied (not a silent fallback)
before handing off — and tell the reviewer the file is online-only.

## Iteration

When the reviewer pastes back an Export JSON payload: parse it (each comment has
`variationId`, `variationLabel`, `xPct`, `yPct`, `text`, `createdAt`), group by
`variationId` to see which variation drew the strongest feedback, and propose a
next-round artifact — typically 2–3 *tightened* variations responding to the
feedback, saved as a new `-v2` file so history stays intact.

## Promoting an accepted variation

Once a winner is picked: translate it into the project's own source of truth
(the design-token file, the component library, or a living mockup if the project
keeps one), confirming the diff first if it touches a committed file. Then
implement it as product code through the project's workflow (offer
`/lodestar:workflow`). Keep the exploration artifact as the decision record — do
not delete it.

## Bundled resources

- `assets/template.html` — self-contained shell with the feedback overlay. Copy,
  fill placeholders, save. Do not edit inline.
- `assets/variation-example.html` — canonical structure for one variation
  `<section>`. Every variation follows this skeleton.
- `references/design-system-discovery.md` — how to find and extract a project's
  live tokens and component vocabulary. Loaded as needed.
- `references/ux-principles.md` — Distinctness Test, variation axes,
  anti-patterns, accessibility floor. Loaded as needed.
