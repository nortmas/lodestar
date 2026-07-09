# Pinia (Tier 2)

State management for Vue 3. For component idioms (`<script setup>`, `ref` vs
`reactive`, composables) see `../../frameworks/vue.md`. Balance policy: a
consistent existing pattern wins unless it is a security/correctness/performance
defect.

## One store per domain
- Model stores around domains (`useAuthStore`, `useCartStore`), not around
  screens. Keep each store focused; cross-store reads are fine by calling the
  other store inside an action/getter.

## Pick one store style and match the repo
- Pinia offers **setup stores** (a `defineStore` with a setup-like function) and
  **option stores** (`{ state, getters, actions }`). Both are valid — follow
  whatever the codebase already uses. Do not mix styles arbitrarily.

## Getters derive, actions mutate
- Derived values go in getters (they cache like `computed`). All state changes go
  through actions. Never mutate store state directly from a component — that
  scatters write logic, defeats devtools tracking, and makes changes untraceable.

```ts
// ❌ Bad: component reaches in and mutates store state directly
const cart = useCartStore();
cart.items.push(product);            // untracked mutation, logic lives in the view
cart.total += product.price;

// ✅ Good: state changes through an action; getter derives the total
export const useCartStore = defineStore('cart', {
  state: () => ({ items: [] as Product[] }),
  getters: { total: (s) => s.items.reduce((n, p) => n + p.price, 0) },
  actions: {
    add(product: Product) { this.items.push(product); },
  },
});
// component
cart.add(product);
```

## Keep components thin; don't over-store
- Components read state/getters and call actions — no business logic in the view.
- Not everything belongs in a store. Transient, view-local UI state (a dropdown's
  open flag, an input's draft value) should stay in component `ref`s. Reserve
  Pinia for state that is genuinely shared or must outlive a single component.

## Typed stores
- Type `state` so getters and actions infer correctly. In setup stores, type the
  `ref`s; in option stores, annotate the `state` return. Avoid `any` on store
  state — it silently erases safety across every consumer.

```ts
// ✅ typed state in an option store
state: (): { user: User | null; loading: boolean } => ({ user: null, loading: false }),
```

Source: best-practice · Confidence: high
