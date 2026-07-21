# Divergence Playbook

Load this when entering divergence mode. It makes the reset concrete.

## The recurring defaults to consciously reset from

These are the patterns reached for on autopilot and recolored per project. They
are **not banned** — they are a default. In divergence mode, reconsider each one
deliberately; if it stays, it must be a *choice*, not a reflex:

- Cards as rounded rectangles with a **coloured vertical accent bar on the left**.
- The stat-block skeleton everywhere: **uppercase label → big number → thin
  progress bar underneath**.
- Pill-shaped chips, uppercase "eyebrow" mini-labels, one uniform corner-radius
  on everything.
- Flat dark surface with evenly-spaced grey cells.
- One accent colour, recoloured per project, doing all the work.

If a draft contains three or more of these, it is the safe register — not a
divergence. Reset.

## Aesthetic worlds are chosen along these axes (not widget layout)

A different *layout of data* is not a different world. A world differs in
atmosphere. Vary these:

| Axis | Range |
|---|---|
| Atmosphere / mood | clinical · warm · editorial · brutalist · retro-futurist · organic · luxe · playful |
| Surface & material | flat · paper/texture · glass · metal · matte depth · print-like |
| Light | even/ambient · dramatic/directional · glow/emissive · high-key · noir |
| Scale & density | monumental type · tight editorial grid · airy · data-dense terminal |
| Shape language | sharp/geometric · humanist-soft · hand-drawn · mixed radius with intent |
| Colour role | monochrome + one signal · duotone · full palette · muted earth · neon-on-dark |
| Typography | display serif · grotesque · mono-forward · condensed · variable-weight |
| Motion / materiality | still · restrained micro-motion · physical/springy · cinematic reveal |
| Composition | centered · asymmetric · broken grid · layered/collage · single focal |

Pick a coherent *combination* per world. Two worlds must differ on several axes,
not one shade.

## World-option template (present before building)

For each of the 2–4 worlds:

- **Name** — a short evocative label ("Swiss editorial", "Warm terminal",
  "Brutalist print").
- **One-line rationale** — why it fits this product.
- **Reference** — a concrete pointer from the trend search (site, movement,
  designer, era) — not "modern and clean".
- **Mock** — an ASCII sketch, or hand it to `/lodestar:design-variations` to
  render all worlds as one pickable artifact.

## Trend research prompts (year-aware)

Search the current year explicitly. Useful queries:

- "<product type> UI design trends <year>"
- "<domain> web design inspiration <year> awwwards"
- "<aesthetic> interface examples" (e.g. "editorial dashboard", "brutalist SaaS")
- Reach for real reference galleries, not generic advice.

Name what you found. If the search turns up nothing useful, say so — do not
silently fall back to the default look.

## Reference catalogue of aesthetics

`github.com/voltagent/awesome-design-md` is a curated set of `DESIGN.md` files
distilled from 70+ real brand design systems, spanning worlds a default SaaS
look never reaches — retro web (Dell 1996, Nintendo 2001), automotive (Ferrari,
Tesla), retail (Nike, Starbucks), editorial/media (The Verge, Apple), fintech,
AI platforms. Browse the README or `preview.html`, or fetch a specific
`design-md/<brand>.md` for concrete tokens and type/colour/material choices.

Use it to **widen the vocabulary of atmospheres**, not to clone. Two hard rules:

- **Inspiration, not imitation.** Extract *principles* — how a system handles
  hierarchy, materiality, density, motion — then build a world that fits *this*
  product. Reproducing one brand's system wholesale is just a different flavour
  of convergence.
- **Never pass work off as another brand.** Do not ship a UI that impersonates a
  real company's identity (its name, logo, exact palette-as-signature) for a real
  product. Reference the moves, not the mask.

## Verification checklist (before "done")

- Rendered in a real browser (agent-browser or Chrome MCP) and screenshotted.
- Alternating colours (zebra, dividers, hover/active states) checked by eye — no
  two adjacent colours blend.
- Typography actually loaded (not silently falling back to a system font).
- Readability/contrast holds at the chosen atmosphere.
