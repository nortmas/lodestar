---
name: design-fresh
description: Make UI design intentional, trend-aware, and genuinely varied across
  projects — not the same widgets recolored. Baseline mode raises the floor on any
  UI/frontend/visual task (one cohesive aesthetic, real typography, atmosphere over
  flat fills, UX first). Divergence mode forces a true creative reset with trend
  research and reference-backed aesthetic "worlds". Reads and appends a
  cross-session design journal so each project deliberately diverges from the last.
  Triggers on '/lodestar:design-fresh', on any UI/frontend/visual design task, and
  especially on variety or dissatisfaction cues — "do it differently", "experiment",
  "another variant", "fresh", "new concept", "make it interesting", "this is
  boring", or any sign (in any language) that a first pass is unsatisfying.
---

# Design Fresh

Two modes. **Baseline** raises the floor on any UI work. **Divergence** — the
important part — triggers on variety/dissatisfaction cues and forces a real
creative reset instead of rearranging the same widgets.

The problem this exists to solve: left alone, design converges on one
statistically common look and only recolors it between projects ("AI slop").
This skill names the axes, pulls real references, and — via the **design
journal** — remembers what was already shipped so each project diverges on
purpose.

## Design journal — read first, append last (every design task, both modes)

This round-trip is the whole point of the skill; it is not optional dressing.

- **Before anything else** — before proposing an aesthetic, before writing a
  line of markup — read `~/.claude/design-journal.md` (create it if missing).
  This is the first action of a design task; if it hasn't happened, stop and do
  it. Note the aesthetics, fonts, palettes, and structural patterns recent
  projects already used — the goal is to **not** repeat them here.
- **After finishing, before claiming done:** append one short entry —
  `date · label · chosen world · fonts · palette · key structural patterns`. A
  few lines, no more. "Done" without this entry is incomplete work.
- **`label` is a generic descriptor** — the product *type* or domain
  ("analytics dashboard", "marketing landing", "study app"), never a client
  name, repository path, or anything identifying. Never store secrets or
  internal URLs. It is a personal, user-global file, not plugin content, but
  treat it as if it could be shared.

## Baseline mode (any UI/frontend/visual task)

- Commit to **one cohesive, intentional aesthetic** — an atmosphere, not a
  widget dump.
- **Typography carries the design:** avoid Inter/Roboto/system defaults; use real
  scale + weight contrast.
- **Atmosphere and depth over flat grey fills.**
- **Readability and UX are the hard guardrail** — always, in both modes.
- Habitual patterns stay available as a *default* — fine when nothing calls for
  more. They are not the answer when the ask is "fresh".

## Divergence mode (the important part)

Triggered by the cues in the description, or **any sign of dissatisfaction with a
first pass**. When triggered, do all five — do not shortcut back to the safe
register:

1. **Stop and genuinely reset.** Consciously step away from the habitual defaults
   (named in `references/divergence-playbook.md` as a reset checklist, not a
   blacklist). Ask: *what aesthetic world* — atmosphere, texture, scale, motion,
   materiality — not *what widget layout*.
2. **Research current trends + references.** Do a **year-aware web search** for
   design directions relevant to this product's domain. Name concrete
   references/inspirations — do not invent from memory.
3. **Offer 2–4 distinct WORLDS, not widget tweaks.** Each atmosphere-level and
   genuinely different, with a one-line rationale + a reference pointer + a quick
   mock. Prefer handing the mocks to **`/lodestar:design-variations`** to render
   them as one pickable, click-to-comment artifact. Wait for a pick before
   investing.
4. **Build ONE bold, well-executed version** of the chosen world — not three
   timid ones. UX stays the guardrail.
5. **Verify visually before claiming done.** Render it (agent-browser works even
   when the Chrome MCP extension is "not connected") and screenshot. For anything
   with alternating colours — zebra rows, dividers, states — confirm by eye/pixel
   that no two adjacent colours blend. No "done" claim without a look.

## Companion skills

- **`/lodestar:design-variations`** — packages the divergence-mode worlds (or any
  element) into an interactive pickable artifact. `design-fresh` decides *which
  worlds*; `design-variations` renders them for review.
- **`ui-ux-designer`** subagent — use as an adversarial critic on the chosen world
  before finalizing.
- Complements the installed **`frontend-design`** skill, which has no
  cross-session memory and does not force divergence on dissatisfaction — this
  skill adds both.

## Reference

`references/divergence-playbook.md` — the aesthetic-axes checklist, the named
recurring-defaults reset list, the world-option template, and trend-research
prompts. Load it when entering divergence mode.
