---
name: visual-tuner
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash
description: Use when a CSS value is hard to hit by eye from a worded description — positions/offsets, padding/margin/gap, sizes, border-radius, line thickness, z-index, colors, fonts, opacity, shadows — and blind iteration would waste round-trips. Instead of guessing, generate one self-contained interactive HTML "tuner" that renders the REAL target component with the tunable properties exposed as live controls (sliders, color pickers, font pickers). The user drags until it looks right, the page shows exact CSS values, they send them back, you paste them into the source verbatim. Zero guessing, zero ping-pong. Triggers on '/visual-tuner' and on pixel-fit asks — "nudge / align / a bit more / a touch less / move it" — where words can't pin the number.
---

# Visual Tuner

When a CSS value is a matter of taste or pixel-fit, **don't guess and don't iterate blind.**
Build a small interactive HTML page that renders the *real* component and exposes the
properties in question as live controls. The user drags until it looks right; the page
prints the exact CSS; they paste it back; you drop it into the source verbatim.

The template is the easy part. The value is: matching the real component pixel-for-pixel,
picking the right control per axis, and starting every control on the current value.

## When to use

- A pixel-fit edit that won't converge in 1–2 tries (connectors, alignment, spacing rhythm,
  fine typography).
- The user says "nudge / align / a bit bigger / a touch less / move it" and words can't
  pin the exact number.
- Any color / font / size where taste decides, not logic.

## When NOT to use

- The value is determined by logic or a spec (compute it, don't tune it).
- A one-liner you'll obviously get right first try.
- Building a shareable report or design exploration → `/lodestar:visual-report` or
  `/lodestar:design-variations`. The tuner is a private local scratch tool, never an Artifact.

## Workflow

1. **Pin the target and the axes.** Name the exact element and the exact list of properties
   to tune. If either is unclear, ask **one** question, then proceed.

2. **Match the real thing.** Grep the project for the real tokens (CSS custom properties,
   `tailwind.config.*` `theme.extend`, `@font-face`, the component's stylesheet). Copy the
   real markup + styles into the target so the tuner looks pixel-for-pixel like the app —
   no abstract stand-ins. Reproduce enough surroundings that alignment reads true, and set
   the stage background to the real app background. See `references/control-types.md`.

3. **Build from the template.** Copy `assets/tuner-template.html` and fill the `{{...}}`
   slots: title, stage background, target markup (tuned props read `var(--…)`), one control
   per axis, and a state switcher if the element has states. Each control's **start value =
   the CURRENT value from the source**, so the page opens looking exactly like today. Control
   types and the full binding contract are in `references/control-types.md`.

4. **Open a FRESH file (anti-cache).** Write to a new filename each session (or add a version
   suffix) and open it:
   ```
   open <path-to-fresh-file>.html
   ```
   Reusing a filename makes the browser serve the old cached page — the #1 cause of
   "nothing changed". Then say, in one line: *"drag until it looks right, send me the CSS block."*

5. **Apply verbatim.** Paste the returned values into the source **exactly as given** — don't
   "improve" or re-guess them. Rebuild / refresh the app preview if the project has that step,
   and confirm the result. If a value can't be applied as-is, say why; never change it silently.

## Hard rules

1. **Match the real component.** Real tokens, real markup, real background. Controls start on
   the current source values. No abstract mockups.
2. **One axis, one control** — and add an axis the moment it's asked for (need `left` for
   alignment? add a `left` slider). Numeric = labelled range with the right unit
   (px/rem/%/em) and sensible min/max/step + live value. Color = native color input + hex.
   Font = select of the project's real font stacks.
3. **Every control drives a CSS variable on the target** (`--x`) so dragging updates the view
   with no reload.
4. **Always show a big, monospace, copyable block** of the final CSS (`property: value;`) —
   easy to send as text or a screenshot.
5. **Render the states that matter.** If the element has states (hover / open / collapsed),
   add a state switcher so values are checked in all of them.
6. **Fresh filename + `open`.** Never overwrite the last tuner's name; anti-cache.
7. **Apply values verbatim.** No silent re-tuning. If a value won't fit as-is, explain why.
8. **Local file only.** Never publish the tuner as an Artifact or send it anywhere — it's a
   scratch tool opened in the browser.

## Bundled resources

- `assets/tuner-template.html` — the one self-contained tuner shell (header + control panel +
  live stage + copyable CSS readout) with a zero-config wiring engine and `{{...}}` slots.
  One template; only the target markup, control list, and start values change per use.
- `references/control-types.md` — the `data-*` binding contract and the range / color / font /
  state control recipes, plus how to match the real component's tokens and markup.
