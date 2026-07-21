# UX/UI Principles — What Makes a Good Variation Set

A "variation" is a genuinely distinct design direction, not a tweaked copy.
Before generating N variations, ensure each answers a different design question.

## The Distinctness Test

For every new variation, ask: **"If the reviewer picks this one, what does that
decision teach us about their preference?"**

Bad (no decision value):
- V1 accent button, V2 slightly-darker-accent button
- V1 padding 12px, V2 padding 14px

Good (each variation resolves a real question):
- V1: minimal / bordered — tests whether the element should recede onto the surface
- V2: accent-led — tests whether the accent should carry the hierarchy
- V3: elevated with depth — tests whether layered surfaces reinforce nesting
- V4: dense, label-forward — tests a tighter information rhythm

## Variation axes to consider

Pick 2–3 orthogonal axes per set. Do not vary everything at once — the reviewer
must be able to isolate which change they prefer.

| Axis | Options |
|---|---|
| Emphasis | neutral · accented · bold |
| Depth | flat · bordered · surface-layered |
| Density | airy · balanced · dense |
| Shape language | sharp · soft · pill |
| Type hierarchy | single-weight · two-weight · body + mono-label mix |
| Framing | inline · card · left-accent strip · split |
| Accent placement | left border · top tag · background wash · icon only |

## Modern trends that age well

Favor these — well-researched and unlikely to look dated in a year:

- **Restrained motion**: hover lift 1–2px, opacity on press; no parallax or
  spring-bounce on UI chrome.
- **High-contrast typography**: a strong size/weight ratio, not a gentle
  progression.
- **Asymmetric emphasis**: one element carries the visual weight per view;
  everything else recedes.
- **Functional colour**: colour signals meaning (state, role, diff), not
  decoration.
- **Generous whitespace on a tight grid**: a consistent spacing scale, a capped
  max width, no freeform margins.

## Anti-patterns to avoid

- **Generic AI aesthetic**: purple→blue gradient backgrounds, glassmorphism
  everywhere, unmotivated large radius on everything, Inter + one accent.
- **Decorative icons** that add no meaning.
- **Shadow soup**: competing elevations with no depth hierarchy — prefer a
  deliberate scale or hairline borders.
- **Dual accent colours** on one element — dilutes the signal.
- **Skeuomorphic effects** (inset shadows, hard bevels, 3D gradients) fighting a
  flat, token-driven system.
- **Font zoo**: a third font family introduced just for variety.
- **Raw hex** for a colour that already has a token.

If the project documents its own bans (e.g. no emoji, a fixed type system),
those override this list — honor them.

## Accessibility floor

Every variation must meet these, non-negotiable:

- Body text ≥ 14px, line-height ≥ 1.4.
- Text/background contrast ≥ 4.5:1 (AA body), ≥ 3:1 for large text — check
  against the actual injected values, light and dark if a dark variant is shown.
- A visible focus state on every interactive element (do not strip
  `:focus-visible` when restyling).
- Colour is never the only signal for state — pair it with an icon or label.
- Minimum tap target 40×40px for interactive elements.

## Self-critique before writing the file

1. **Distinctness**: is choosing between any two a meaningful decision?
2. **Consistency**: do all variations still read as this project?
3. **Range**: is there at least one conservative and one bolder option?
4. **Labels**: does each `dv-variation-title` name the design decision, not just
   a number? Good: "V2 — Accent-led card". Bad: "Variation 2".
