# Sass / SCSS (Tier 2)

Styling guidance for Sass/SCSS (Dart Sass, the only maintained engine). If the
project also uses Tailwind, see `./tailwind.md` — utilities usually replace most
custom SCSS. Balance policy: a consistent existing pattern wins unless it is a
security/correctness/performance defect.

## Use the modern module system
- Author with `@use` and `@forward`. The old `@import` is deprecated and slated
  for removal: it dumps everything into the global namespace, re-evaluates files
  repeatedly, and makes origins impossible to trace. Namespaced `@use` is
  explicit and loads each file once.

```scss
// ❌ Bad: deprecated @import, global namespace, deep nesting
@import 'variables';
@import 'mixins';
.card {
  .card__body {
    .card__title {
      .icon { color: $brand; }   // 4 levels deep — brittle, high specificity
    }
  }
}

// ✅ Good: @use with a namespace, shallow structure
@use 'variables' as v;
@use 'mixins' as mx;
.card__title { color: v.$brand; }
.card__title-icon { @include mx.icon; }
```

## Tokens live in one place
- Keep variables, colors, spacing, and breakpoints in a single tokens module
  (e.g. `_tokens.scss`) and `@use` it where needed. One source of truth prevents
  the drift you get when magic numbers are redefined per file.

## Avoid deep nesting (≤3)
- Cap selector nesting at three levels. Deep nesting produces long, high-
  specificity selectors that are hard to override and couple CSS to DOM shape.
  Follow the repo's convention — BEM (`block__element--modifier`) is a common one
  — so flat, meaningful class names replace nesting.

## Prefer CSS custom properties for runtime theming
- Sass variables are compile-time constants; they cannot change in the browser.
  For anything that switches at runtime (light/dark theme, user accents), expose
  CSS custom properties and let Sass set their defaults.

```scss
// ❌ Bad: Sass var can't change at runtime — no live theming
.btn { background: $brand; }

// ✅ Good: custom property is themeable at runtime; Sass seeds the default
:root { --color-brand: #{v.$brand}; }
.btn { background: var(--color-brand); }
[data-theme='dark'] { --color-brand: #{v.$brand-light}; }
```

Source: best-practice · Confidence: high
