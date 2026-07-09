# Accessibility (Tier 2 — CRITICAL carve-out)

Everything here is part of the critical carve-out, on par with correctness. An
inaccessible existing pattern does NOT win the balance policy: never codify it as
the project rule just because the codebase repeats it. Emit the correct rule plus
a migration note pointing at the offending markup. Missing labels, no keyboard
access, poor contrast, absent focus states, and non-semantic markup are defects,
not style. Framework specifics: `../frameworks/vue.md`, `../frameworks/react.md`;
contrast tokens: `../packages/frontend/tailwind.md`.

## Semantic HTML over div-soup
Use the element that carries the meaning — `<button>`, `<a>`, `<nav>`, `<main>`,
`<ul>`, `<h1>`–`<h6>` in order. Semantics give assistive tech the roles, states,
and keyboard behavior for free. A `<div onClick>` has none of it.

❌ Bad — clickable div: no role, not focusable, no keyboard, no Enter/Space
```html
<div class="btn" onclick="save()">Save</div>
```
✅ Good — a real button: role, tab stop, keyboard activation, all native
```html
<button type="button" onclick="save()">Save</button>
```

## Label every input
Every control has an accessible name: a `<label for>` (preferred, also enlarges
the hit target) or an `aria-label`/`aria-labelledby` when no visible label exists.
Placeholder text is NOT a label — it vanishes on input.

❌ Bad — placeholder is not a name
```html
<input type="email" placeholder="Email" />
```
✅ Good — associated label
```html
<label for="email">Email</label>
<input id="email" type="email" />
```

## Keyboard operability
Everything usable by mouse is usable by keyboard. Preserve a logical focus order
(follow DOM order; avoid positive `tabindex`), keep a visible focus ring (never
`outline: none` without a replacement), and never trap focus except in a modal
that also returns focus on close.

## Color contrast (WCAG AA)
Body text needs a contrast ratio of at least 4.5:1 against its background (3:1 for
large text and meaningful UI/graphic boundaries). Never convey information by color
alone — pair it with text or an icon. Prefer contrast-checked theme tokens.

## Images: alt for meaning, empty for decoration
Meaningful images need `alt` describing their content or function. Purely
decorative images take `alt=""` so screen readers skip them — omitting `alt`
entirely makes the reader announce the file name instead.

```html
<img src="chart.png" alt="Revenue up 20% in Q3" />   <!-- meaningful -->
<img src="swoosh.svg" alt="" />                        <!-- decorative -->
```

## ARIA only when native semantics fall short
Prefer native elements; reach for ARIA only when no native element fits. Incorrect
or redundant ARIA (`role="button"` on a `<button>`, a wrong `aria-*`) is worse than
none — it overrides real semantics. First rule of ARIA: don't use ARIA.

## Announce form errors
Mark invalid fields with `aria-invalid="true"` and link the message via
`aria-describedby` so it is read with the field. Do not rely on red border alone.
Pairs with the form UX guidance in `ui-ux.md`.

```html
<label for="pw">Password</label>
<input id="pw" type="password" aria-invalid="true" aria-describedby="pw-err" />
<p id="pw-err">Must be at least 8 characters.</p>
```

## Respect reduced motion and target size
Gate non-essential animation behind `@media (prefers-reduced-motion: reduce)`.
Interactive targets should be at least 24×24 CSS px (44×44 for primary touch
actions) with adequate spacing.

## Carve-out reminder
If the codebase ships clickable divs, unlabeled inputs, `outline: none`, or
color-only signaling: do NOT write a rule matching it. Emit the correct rule and a
migration note flagging the markup for remediation.

Source: best-practice · Confidence: high
