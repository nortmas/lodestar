# Flux UI (Tier 3)

Flux is Livewire's first-party UI kit. Flux-specific guidance only; for component
size and state see `../laravel/livewire.md`, for utilities see
`../frontend/tailwind.md`. Balance policy: a consistent existing pattern wins
unless it is a security/correctness/performance defect.

## Rules
- **Prefer Flux components over ad-hoc markup.** Use `<flux:button>`,
  `<flux:input>`, `<flux:modal>`, `<flux:field>` etc. instead of hand-rolled Blade
  + Tailwind that re-implements the same control — you lose accessibility,
  keyboard handling, and dark-mode for free otherwise.
- **Theme through Flux, not overrides.** Set the palette via Flux's theming
  (accent color, appearance) and design tokens rather than fighting component
  internals with `!important` utilities. Small utility tweaks are fine; wholesale
  restyling means you picked the wrong component.
- **Stay inside the design system.** Do not mix a second component library for the
  same primitives; consistency beats one-off custom widgets.
- Flux Pro components require a licensed install — do not reference Pro components
  in a repo that only has the free tier.

❌ Bad — re-implementing a Flux control
```blade
<button class="rounded bg-blue-600 px-4 py-2 text-white" wire:click="save">Save</button>
```
✅ Good — use the component
```blade
<flux:button variant="primary" wire:click="save">Save</flux:button>
```

## Research hook
On activation, `WebSearch` `"livewire flux <installed-version> best practices"`.
Prefer the official docs (fluxui.dev), then cross-check one reputable source.
Confirm the component set and theming API for the installed major and codify
findings with provenance `researched` + source URL + retrieval date. Never block
on a failed search — fall back to the rules above.

Source: best-practice · Confidence: medium
