# Reasoning procedure

Do this thinking before you render. The template is easy. The value is deciding
audience, structure, what to cut, which chart fits, and how to balance technical
detail with plain English. Work these steps in order.

## 1. Audience and purpose first

Name the reader and the decision the report drives. That sets the
technical-vs-plain-English balance.

- A developer fixing the findings wants file:line and the exact rule.
- A stakeholder deciding go/no-go wants the count, the risk, and what to do next.
- A mixed audience is the common case. Carry both layers in one report: a plain
  summary on top (`.vr-explain`), the technical detail beside it (`.vr-evidence`)
  or folded into a drilldown (`details.vr-drill`).

One report holds both. You do not pick technical or plain. You stack them.

## 2. Cut noise, keep essentials

An explicit filtering step. Decide what to leave out before you build.

- Drop items that do not change the reader's decision.
- Rank the rest. The top few belong in the top-N list; the long tail belongs in a
  drilldown.
- **Dedup-with-scope-merge.** The same issue in N places is ONE item that lists
  its scope, never N near-identical items. Write the finding once, then add a
  `.vr-scope` block: `<p class="vr-scope"><b>Also affects:</b> ...</p>`. Twelve
  copies of one SQL-injection pattern become one item whose scope names the twelve
  files.

Over-cutting is also a failure. Keep every essential. See common mistakes below.

## 3. Plain-English explanation on every item

Every item gets: what it means, and why it matters. Translate the jargon. Keep the
technical detail beside the explanation, never instead of it.

Map to the markup in `assets/section-example.html`:

- `.vr-explain` holds the plain-English paragraph. What happens, who is affected,
  what the consequence is. No jargon a non-specialist would miss.
- `.vr-evidence` holds the technical proof beside it: `file:line`, the offending
  code, the raw value. Monospace, kept but not leading.

An item with evidence and no explanation fails the skill. The reader who needs the
plain layer cannot use it.

## 4. Charts that earn their place

Delegate the chart choice to the built-in `dataviz` skill. Load it, let it pick the
chart type from the data shape, and apply its "a chart must earn its place" rule.

- If a sentence says it better, write the sentence and draw no chart. One number is
  a metric card, not a chart.
- Inline `<svg>` only. No CDN, no chart library, no remote image.
- Colour bars and series with the `--vr-cat-1` .. `--vr-cat-6` palette vars, so the
  chart matches the report in light and dark. Use `var(--vr-border)` for axes and
  `var(--vr-muted)` for labels.
- Wrap a wide chart in `.vr-scroll` and put it in a `<figure class="vr-figure">`
  with a `<figcaption class="vr-figcaption">`.

## 5. Redaction pass before any shareable output

Run this before you publish an Artifact or write a file you will circulate.

- Secrets to `[REDACTED:<kind>]`, for example `[REDACTED:api-key]`,
  `[REDACTED:password]`, `[REDACTED:token]`.
- Absolute home paths to `~`. `/Users/dmitryantonenko/www/app/.env` becomes
  `~/www/app/.env`.
- Never invent a value to fill a gap. If the input lacks a number, say so in the
  report.

## 6. Structure-plan checkpoint

For any non-trivial input, show this plan to the user BEFORE rendering. It is the
checkpoint that stops the report from missing detail or weighting the wrong thing.

```
Report plan
- Audience: <who reads it, what decision it drives>
- Delivery: <Artifact | local file>   (already chosen in Step 1)
- Sections:
    1. Metric cards: <the 3-5 numbers>
    2. Top-N: <how many, ranked by what>
    3. <Section name>: <n items>
    4. <Section name>: <n items>
- Charts: <chart type + what it shows, or "none, prose is enough">
- Cutting: <what you are leaving out, and the merges you made>
```

Keep it short. Wait for the user's OK, then build.

**Skip the checkpoint only for trivial input**: a handful of items with an obvious
shape, or the user asked for a quick render. When in doubt, show the plan.

## Common mistakes

- **Overloading.** Every finding as a top-level item, no drilldown, no merges. The
  reader drowns. Cut and fold.
- **Charting a single number.** One value is a metric card. A chart needs a
  comparison, a distribution, or a trend.
- **Dropping the plain-English layer.** Evidence with no `.vr-explain`. The
  non-specialist reader is locked out.
- **Over-cutting.** Merging away a distinction that mattered, or dropping an
  essential finding to look tidy. Cut noise, keep every essential.
- **Near-duplicate items.** The same issue listed N times instead of one item with
  a `.vr-scope` block.

## Clarity: the reader-question test (the last gate before delivery)

The author cannot see their own ambiguity: while writing you hold context the reader
does not, so a label that reads fine to you raises a question for them. The only
reliable fix is a separate pass in a different role. After the report is built,
re-read it as a skeptical first-time reader who knows nothing about the audit, and
put every number, label, chip, and chart axis through four questions:

- **Of what?** A subset count with no whole is unclear. `28` alone invites "of how
  many?". Write `28 / 32`.
- **What about the rest?** If `28 / 32 Confirmed` leaves 4, say what they are (a
  tooltip: "the other 4 are Likely, needing runtime access to confirm"). An
  unexplained remainder is a question left open.
- **What does this word mean?** Internal vocabulary is invisible jargon to the
  reader. Reword or add a tooltip.
- **Which axis?** A row of tiles must be one axis. Severity and verdict in the same
  row read as one partition and provoke "why don't these add up?".

If an element survives all four without a question, it is clear. If it raises one,
it is not: add the denominator, reword to plain English, attach a `data-tip`
tooltip, or cut it. Do not rely on noticing this while authoring; make it a
deliberate cold read.

**Tooltips are part of the design, not an afterthought.** Any non-obvious number or
label carries `data-tip="..."` with a plain-language explanation; the template
styles it on hover. It lets a tile stay compact while the "of what / what about the
rest" answer is one hover away.

**Worked anti-examples (all real, all caught only on a cold read):**

- `28 Confirmed` in a row of severity tiles. Three faults at once: no denominator
  (of what?), an unexplained remainder (the other 4?), and a verdict metric mixed
  into a severity row (which axis?). Fix: `28 / 32 Confirmed`, neutral tone (not a
  severity color), tooltip naming the remainder.
- `11 FAIL (confirmed)` and `141 Rules passing` as tiles. Jargon and a mismatched
  axis: the reader does not know the rule model. Fix: a uniform findings row
  (Critical / High / Medium / Low·Info / Confirmed `N / total`); the passed-rule
  count belongs in the "existing defenses" drilldown, not the headline tiles.
- A chart with axis labels `Crit / Std / Cos / Pass` and no tooltip. Abbreviations
  the reader must decode, and no hover to help. Fix: full words, a legend, a
  per-mark hover tooltip; and if the tiles already carry the same breakdown, drop
  the chart rather than repeat it cryptically.
