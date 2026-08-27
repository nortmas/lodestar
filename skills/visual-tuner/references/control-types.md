# Control types & the binding contract

The template ships a tiny engine that auto-wires any element with class `vt-ctl`.
You never write JS. You write markup with `data-*` attributes and a `<style>` that
reads the matching CSS variables. Every control follows the same contract.

## The data-attribute contract

| attribute        | required | meaning                                                        |
|------------------|----------|----------------------------------------------------------------|
| `data-var`       | yes      | CSS variable this control drives, e.g. `--x`                   |
| `data-prop`      | yes      | real CSS property name shown in the readout, e.g. `left`       |
| `data-unit`      | numeric  | appended to the numeric value: `px` / `rem` / `%` / `em` / `deg` — omit for unitless (`z-index`, `opacity`, `line-height`, `font-weight`) |
| `data-target`    | no       | element the var is set on (CSS selector); defaults to `:root`  |
| `data-selector`  | no       | readout grouping label (the CSS selector you'll paste into); defaults to `target` |

The engine, on load and on every `input`:
1. sets `data-var` on `data-target` to the value (with unit),
2. updates the live badge next to the label,
3. regrouped-by-`data-selector`, rewrites the readout as real `data-prop: value;` lines.

The **target's own `<style>` must read the variable**, e.g. `.connector { left: var(--x); }`,
so dragging updates the view with no reload.

## Range (numbers: positions, spacing, sizes, radius, thickness, opacity, z-index)

```html
<div class="vt-ctl-row">
  <label>Top padding <span class="vt-val"></span></label>
  <input type="range" class="vt-ctl" data-var="--pt" data-prop="padding-top"
         data-unit="px" data-target="#vt-target" data-selector=".card"
         min="0" max="48" step="1" value="16">
</div>
```

- **One axis, one control.** `left` and `top` are two sliders, never one. Add an axis the
  moment the user asks (e.g. they want to nudge horizontally too → add a `left` slider).
- **`value` = the CURRENT value from the code.** Read the source; start where it is now.
- **Sensible min/max/step.** Bracket the current value with headroom, don't span 0–1000.
  `step` fine enough to hit the target: `1` for px, `0.05` for rem/opacity, `0.5` for
  border thickness.
- **Units matter.** If the source uses `rem`, tune in `rem` (`data-unit="rem"`), so the
  pasted value drops straight in. Match the source's unit, don't convert.

## Color (fills, borders, text, shadow color)

```html
<div class="vt-ctl-row">
  <label>Border color <span class="vt-val"></span></label>
  <input type="color" class="vt-ctl" data-var="--bc" data-prop="border-color"
         data-target="#vt-target" data-selector=".card" value="#3b82f6">
</div>
```

The value shown and emitted is the hex. `value` must be the current color as hex
(convert named/rgb tokens to hex for the input's start).

## Font (family)

```html
<div class="vt-ctl-row">
  <label>Font family <span class="vt-val"></span></label>
  <select class="vt-ctl" data-var="--ff" data-prop="font-family"
          data-target="#vt-target" data-selector=".card">
    <option value="Inter, sans-serif">Inter</option>
    <option value="'Roboto Mono', monospace">Roboto Mono</option>
  </select>
</div>
```

**Options come from the project's real font stacks** (tailwind `fontFamily`, `@font-face`,
CSS `--font-*` vars) — not a generic list. Put the current stack first so it's the default.
The emitted value is the exact stack string.

## State switcher (hover / open / collapsed / active)

Render every state that matters so values are verified in all of them. The group sets an
attribute on the target; your target CSS keys off it.

```html
<div class="vt-states" data-state-target="#vt-target" data-state-attr="data-state">
  <button data-state-value="default" aria-pressed="true">Default</button>
  <button data-state-value="hover">Hover</button>
  <button data-state-value="open">Open</button>
</div>
```

```css
#vt-target[data-state="hover"] .card { /* hovered look */ }
#vt-target[data-state="open"]  .panel { display: block; }
```

Delete the states block entirely if the target is single-state.

## Matching the real component (do this before building)

1. **Find the real tokens.** Grep for CSS custom properties, `tailwind.config.*`
   (`theme.extend`), `@font-face`, and the component's own stylesheet. Copy the values in.
2. **Copy the real markup + styles** of the target into `{{TARGET}}`, then swap only the
   tuned properties to `var(--…)`. Everything else stays byte-identical so the tuner looks
   pixel-for-pixel like the app.
3. **Reproduce the surroundings** enough that alignment reads true — if tuning a connector
   between two cards, render both cards. Set `{{STAGE_BG}}` to the real app background.
4. **Start on current values.** Each control's `value` = what's in the source right now, so
   the tuner opens looking exactly like today and the user tunes *from* there.
