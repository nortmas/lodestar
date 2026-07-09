# Bootstrap (Tier 2)

Codify customizing Bootstrap through its Sass API, not fighting compiled CSS. Balance policy applies: match how the repo already imports and themes Bootstrap.

## Decisions worth encoding

- **Use the framework, don't reinvent it.** Reach for the grid (`row`/`col-*`), utilities (spacing, flex, display), and components (`btn`, `card`, `modal`) before writing custom CSS for layout or common patterns.
- **Customize via Sass, not `!important`.** Override `$primary`, `$spacers`, `$font-*`, and the theme maps before `@use "bootstrap"`, so utilities and components regenerate consistently. Overriding compiled `.css` with `!important` fights specificity, breaks on upgrade, and desyncs utility classes from your theme. See `./sass.md`.
- **Import only what you use.** Prefer per-component Sass imports (functions, variables, mixins, then the needed components) over the full bundle to trim CSS. Mirror this for JS — import the components used, or use the bundle, but be consistent across the app.
- **One utility system.** Do not mix Bootstrap with a conflicting utility framework (e.g. Tailwind) — colliding resets and utility names cause specificity wars — UNLESS the repo deliberately runs both with a scoping/prefix strategy.
- **Semantic components over ad-hoc markup.** Use `<button class="btn btn-primary">`, `card`, `alert` rather than re-styling bare `<div>`s. See `../../concerns/ui-ux.md`.

## Example

❌ Bad — overriding compiled CSS with `!important`:

```css
/* Fights Bootstrap's cascade; buttons and badges now drift from the theme. */
.btn-primary {
  background-color: #6f42c1 !important;
  border-radius: 0 !important;
}
```

✅ Good — set the Sass variables so the whole theme regenerates:

```scss
// Override before importing; every component + utility picks it up.
$primary:              #6f42c1;
$border-radius:        0;
@use "bootstrap/scss/bootstrap" with (
  $primary: $primary,
  $border-radius: $border-radius
);
```

Source: best-practice · Confidence: high
