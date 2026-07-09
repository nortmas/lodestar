# Tailwind CSS (Tier 2)

Tailwind-specific guidance only. For component structure and framework idioms see
the detected frontend framework file (`../../frameworks/react.md` etc.). Balance
policy: a consistent existing pattern wins unless it is a
security/correctness/performance defect.

## Utility-first, but extract repetition
- Compose utilities in markup. When the same utility cluster repeats, extract a
  **component** (a Blade/React/Vue component or a `@layer components` class) — do
  not sprinkle `@apply` across the stylesheet to fake components; that recreates
  the CSS-bloat problem Tailwind avoids. Reserve `@apply` for genuinely shared
  primitives (`.btn`), not one-offs.

## Design tokens live in the theme
Put spacing, colors, fonts, radii in the theme (`tailwind.config` `theme.extend`,
or `@theme` in v4) and reference the named tokens. Arbitrary values (`w-[327px]`,
`text-[#3b82f6]`) are escape hatches — occasional use is fine, but a token that
recurs belongs in the config so it stays consistent and themeable.

❌ Bad — hardcoded arbitrary values scattered everywhere
```html
<button class="bg-[#3b82f6] px-[13px] py-[7px] rounded-[6px] text-[15px]">Save</button>
<a class="text-[#3b82f6] mt-[13px]">More</a>   <!-- same magic numbers, no single source -->
```
✅ Good — theme tokens, extracted component
```js
// tailwind.config.js
theme: { extend: {
  colors: { brand: '#3b82f6' },
  spacing: { 'btn-y': '0.5rem', 'btn-x': '0.875rem' },
} }
```
```html
<button class="bg-brand px-btn-x py-btn-y rounded-md text-brand">Save</button>
```

## Content / purge config
Keep `content` (v3) / source detection (v4) globs accurate so used classes are not
purged and unused CSS is dropped. Never build class names by string concatenation
(`` `text-${color}` ``) — Tailwind cannot see them and they get purged; use full
class names behind a lookup map.

## Consistent ordering
Run `prettier-plugin-tailwindcss` so class order is canonical and diffs stay small;
do not hand-order classes.

Source: best-practice · Confidence: high
