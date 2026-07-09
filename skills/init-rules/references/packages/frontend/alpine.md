# Alpine.js (Tier 2)

Alpine-specific guidance for the installed major (Alpine 3.x). For the Livewire
side of a TALL stack see `../laravel/livewire.md`. Balance policy: a consistent
existing pattern wins unless it is a security/correctness/performance defect.

## Keep logic minimal and in `x-data`
- Alpine is for sprinkles of interactivity, not an application framework. Keep
  component state and small handlers inside `x-data`; do not embed multi-line
  logic in `x-on`/`x-bind` expressions where it cannot be read or tested.

## Extract reusable behavior to `Alpine.data()`
- Repeated inline `x-data="{ ... }"` objects belong in a named `Alpine.data()`
  component registered once, then referenced by name. This gives one source of
  truth and keeps markup declarative.

```html
<!-- ❌ Bad: inline spaghetti — logic, fetch, and state crammed in the attribute -->
<div x-data="{ open: false, items: [], async load() {
       this.items = await (await fetch('/api/items')).json();
       this.open = true; } }" x-init="load()">
  <button @click="open = !open ? (load(), true) : false">Toggle</button>
  <ul x-show="open"><template x-for="i in items"><li x-text="i.name"></li></template></ul>
</div>

<!-- ✅ Good: named Alpine.data component, declarative markup -->
<div x-data="itemList" x-init="load()">
  <button @click="toggle()">Toggle</button>
  <ul x-show="open"><template x-for="i in items" :key="i.id"><li x-text="i.name"></li></template></ul>
</div>
<script>
  Alpine.data('itemList', () => ({
    open: false,
    items: [],
    async load() { this.items = await (await fetch('/api/items')).json(); },
    toggle() { this.open = !this.open; },
  }));
</script>
```

## `x-show` vs `x-if`
- `x-show` toggles CSS `display` — element stays in the DOM. Use for frequently
  toggled content and anything that must keep its state.
- `x-if` (on a `<template>`) adds/removes the element. Use for expensive subtrees
  or content that should not exist until needed. Do not reach for `x-if` just to
  hide something you toggle often — that thrashes the DOM.

## TALL stack: don't duplicate server state
- In a Livewire component, Livewire owns server state. Do not mirror it in a
  parallel Alpine `x-data` copy that drifts. Bridge with `@entangle` (or `$wire`
  in Livewire 3) so the value is shared, and use `wire:` for server round-trips,
  `x-` for purely client-side UI (dropdowns, tabs, transitions).

```html
<!-- ❌ Bad: Alpine keeps its own `count`, Livewire keeps another — they diverge -->
<div x-data="{ count: 0 }"><span x-text="count"></span></div>

<!-- ✅ Good: entangle the Alpine value with the Livewire property -->
<div x-data="{ count: $wire.entangle('count') }"><span x-text="count"></span></div>
```

Source: best-practice · Confidence: high
