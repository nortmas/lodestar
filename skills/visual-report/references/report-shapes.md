# Report shapes catalog

The information architecture. Pick a shape per block of the report, then compose it
from the classes the template already styles (`assets/report-template.html`,
`assets/section-example.html`). Do not restyle.

## The pyramid: progressive disclosure

Order the page so the reader gets the answer first and the detail last. This
generalizes any multi-item report.

1. **Metric cards** (`.vr-metrics` / `.vr-metric`): the headline numbers, read in
   one glance.
2. **Top-N priorities** (`.vr-topn` / `.vr-topn-row`): the ranked attention queue,
   before any detail section.
3. **Sections of items** (`.vr-section` / `.vr-item`): the findings, each explained.
4. **Collapsible drilldown** (`details.vr-drill`): deep context and the long tail,
   folded away so the main flow stays scannable.

Wide-to-narrow. The reader stops at the level that answers their question.

## Shapes and when each fits

### Metric cards
- **Fits:** 3 to 5 standalone scalars the reader needs immediately (counts, a
  percentage, a total).
- **Markup:** `<div class="vr-metrics">` of `<div class="vr-metric" data-tone="...">`
  each holding `.vr-metric-value` + `.vr-metric-label`.
- **Tone:** `data-tone="crit|high|med|ok"` colours the value. Omit `data-tone` for a
  neutral number. (There is no `low` tone on a metric.)

### Top-N priority list
- **Fits:** "what to fix first", the few items with the highest impact-over-effort,
  ranked, ahead of the full detail.
- **Markup:** `<div class="vr-topn">` of `<div class="vr-topn-row">`, each with a
  `.vr-topn-rank` number and a `.vr-topn-body` (bold lead sentence + one line of
  why). Links use `.vr-topn-body a`.

### Item / finding list
- **Fits:** the body of most reports, a set of findings, each needing a title,
  severity, plain-English explanation, and evidence.
- **Markup:** `<section class="vr-section">` with an `<h2>` and optional
  `.vr-section-note`, holding `<article class="vr-item" data-sev="...">`.
- **Severity:** `data-sev="crit|high|med|low|ok"` on the item drives the left
  border; the matching `<span class="vr-chip" data-sev="...">` drives the chip
  colour. Extra plain `.vr-chip` spans carry tags (a CWE id, a class name).
- **Inside an item:** `.vr-item-head` (title `.vr-item-title` + chips), then
  `.vr-explain` (plain English), then `.vr-evidence` (monospace file:line/code),
  then optional `.vr-scope` for dedup-with-scope-merge.

### Comparison
- **Fits:** before/after, option A vs B, this vs baseline.
- **Markup:** no dedicated class. Compose one of:
  - a table wrapped in `<div class="vr-scroll">` so it scrolls on narrow screens;
  - a grouped-bar inline `<svg>` in a `.vr-figure` (ask `dataviz` for the spec);
  - two `.vr-item` blocks side by side within the section.

### Timeline
- **Fits:** events or metrics over time, a sequence of stages, a trend.
- **Markup:** no dedicated class. Use an inline `<svg>` line or step chart in a
  `.vr-figure` (chosen via `dataviz`), or an ordered list of `.vr-topn-row`s read as
  stages. For a trend of one series, a chart beats a table.

### Drilldown
- **Fits:** the full list behind a summary, raw logs, per-item detail that would
  bury the main flow.
- **Markup:** `<details class="vr-drill">` with a `<summary>` and a
  `<div class="vr-drill-body">`. Collapsed by default.

## Map an arbitrary input to a shape

- Standalone number the reader needs first → **metric card**.
- "Which of these do I act on first?" → **top-N list**.
- A set of findings, each with cause and evidence → **item list**, one section per
  theme.
- The same finding repeated across many places → one **item** + `.vr-scope`, not
  many items.
- Two things measured the same way → **comparison** (table or grouped bars).
- Values across time or ordered stages → **timeline** (chart or staged rows).
- A long tail or raw detail that would overload the page → **drilldown**.
- A distribution, a trend, or a part-to-whole worth showing → a **chart** inside the
  relevant section.

## Rich content blocks

All self-contained, no library, no CDN.

### Code block
- **Fits:** a snippet, a fix, a config, a command. More than the one offending line
  (that stays in `.vr-evidence`).
- **Markup:** `<pre class="vr-code" data-lang="php">` with HTML-escaped code
  (`&lt; &gt; &amp;`). The template's inline highlighter colours comments, strings,
  numbers, keywords, and calls at load (`.tok-*`), in both delivery modes. Escaping
  is mandatory, raw `<script>`/`<img>` would execute before the highlighter runs.
  `data-hl="off"` keeps a block verbatim; hand-wrap `.tok-*` spans for full control.
  No syntax library is bundled, so highlighting is approximate, not a full parser.

### Table
- **Fits:** a small grid, category by measure (findings per service, options by
  attribute). Not a substitute for prose on a single row.
- **Markup:** `<table class="vr-table">` with a `<caption>` title and a `<th>` header
  row, wrapped in `<div class="vr-scroll">` so a wide table scrolls instead of
  breaking the column. Even rows are zebra-striped by the template.

### Formula
- **Fits:** a scoring rule or derivation where the equation reads better than a
  sentence. Rare, use sparingly.
- **Markup:** native MathML in `<div class="vr-math"><math display="block">...</math></div>`.
  Browsers render MathML with no library. KaTeX/LaTeX is not available (it needs a CDN).

## Charts are chosen elsewhere

Do not pick the chart type here. Load the `dataviz` skill: it maps the data shape to
a chart and applies the "earn its place" rule. Every chart is inline `<svg>` using
the `--vr-cat-*` palette vars, placed in a `.vr-figure` (wrap wide ones in
`.vr-scroll`).

For a category-by-severity breakdown (findings per service, per audit, per module),
prefer a **horizontal stacked bar**: one row per category, segments by severity, a
shared left baseline, the total at the end, and a full-word legend (`.vr-legend`)
below. It aligns and reads better than vertical columns and scales to many rows.
Give every segment a `data-tip="Label: N findings"` (full words, never `Crit`/`Std`/
`Cos`); the template renders it as a styled, in-theme, cursor-following tooltip
(SVG cannot use the CSS `::after` tooltip, so charts rely on this handler). If the
metric tiles already carry the same numbers, one proportion bar is enough: do not
also add a redundant column chart. See `assets/section-example.html`.

## Navigation for a multi-page report

One long scroll works up to a few sections. Past that, split the report into pages
(one `<section class="vr-tabpage" data-tab="ID">` each) and give it a navigation,
never a flat button row that wraps onto a second line. Two patterns, both in
`assets/nav-example.html`:

- **Two-level top nav** (primary pills + contextual sub-tabs). Good for a small,
  two-axis set (for example service, then section). Compact vertically.
- **Left sidebar** (grouped items with a per-page count badge, red when the page
  carries a Critical). Better past about six pages: a vertical list never wraps and
  the badges show weight at a glance. Collapses to a `<select>` jump on narrow screens.

Keep a single Overview/dashboard page as the entry point and link into the other
pages from it with `data-goto="<tab-id>"`.
