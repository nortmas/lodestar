# Design-System Discovery — Extract Live Tokens From Any Project

Never hardcode a project's colours, fonts, radii, or spacing. Discover them each
run from whatever the project actually uses, so variations read as *this*
product. Read in the order below and stop once you have a coherent token set.

## 1. Documented rules first

If the project documents styling conventions, they win. Check:

- `.claude/rules/` (a styling/design rule), `CLAUDE.md`, `AGENTS.md`
- a `STYLEGUIDE`, `DESIGN`, or `CONTRIBUTING` doc
- a design-tokens file (`tokens.json`, `theme.ts`, a Figma export)

Honor bans and mandates found there (allowed fonts, "no emoji", semantic tokens
over raw hex, radius/shadow language). These are constraints, not suggestions.

## 2. The token source the project actually uses

Pick whichever exist, in rough priority:

| Source | What to extract |
|---|---|
| Tailwind config (`tailwind.config.*`) | `theme.extend.colors`, `fontFamily`, `fontSize`, `borderRadius`, `keyframes`/`animation` |
| CSS custom properties (`:root { --… }`, a `globals.css`/`variables.css`) | colour values (light + any dark/theme block), radius, shadow, spacing scale |
| CSS-in-JS / theme object (`theme.ts`, styled-components/MUI theme) | palette, typography, shape, spacing |
| Design-token JSON | the canonical values |
| SCSS/Less variables | `$color-*`, `$font-*`, `$radius-*` |

Capture: colour tokens **by their real names**, the font families, the corner
radius scale, the shadow/elevation language, and the spacing rhythm. If light and
dark are both defined, note both — the artifact injects light-mode values by
default (see the SKILL for a dark pass).

## 3. A rendered ground truth, if one exists

If the project keeps a rendered mockup, a Storybook, a living style page, or a
deployed instance, look at it (or screenshot it) **before** inferring look from
code — it shows the *intended* density, radius, and shadow weight more faithfully
than markup. Read it for grammar; do not copy its markup verbatim.

## 4. Representative components

Read 1–3 existing components closest in role to the target (a card for a card, a
button/primitive for a button). Variations should riff on the established
primitive and class composition, not ignore it.

## What NOT to hardcode

- Any colour that already exists as a token — use the token, not a raw hex.
- Any font family outside what the project's system defines. Do not add a "fun"
  third font for variety unless the brief explicitly invites a new typeface.
- Animations not present in the project's config.

If a variation deliberately proposes a **new** token (a new accent, a new
typeface), call it out in that variation's `dv-variation-desc` so the reviewer
knows it is a proposed addition, not an existing token.

## When the project has no design system at all

Greenfield or a bare page with no tokens: this is exactly when to run
`/lodestar:design-fresh` first to choose a deliberate aesthetic (fonts, palette,
atmosphere) informed by trend research and the cross-session journal — then
express that choice as the token set injected into the artifact. Do not default
to Inter + one purple accent.
