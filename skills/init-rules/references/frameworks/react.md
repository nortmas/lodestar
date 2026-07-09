# React (Tier 3)

Balance policy: an existing consistent codebase pattern wins over textbook advice
unless it is a security, correctness, or performance defect.

## Rules

- **Rules of Hooks.** Call hooks at the top level of a component or custom hook
  only — never inside conditions, loops, or nested functions. Order must be
  identical on every render.
- **useEffect is for synchronization, not logic.** Reach for an effect only to
  sync with something external (DOM, network, subscription, non-React widget).
  Data transforms belong in render as derived state; responses to user actions
  belong in event handlers. If nothing external is involved, delete the effect.
- **Every effect needs correct deps + cleanup.** List every reactive value read
  inside; return a cleanup for subscriptions/timers/aborts. Do not disable the
  exhaustive-deps lint to silence a bug — fix the dependency.
- **State layering.** Start local (`useState`). Lift only when genuinely shared.
  Cross-cutting → Context. High-frequency or app-wide → an external store
  (Zustand/Redux/Jotai). Do not put derived-from-props data in state.
- **Memoize only after profiling.** Add `useMemo`/`useCallback`/`memo` when a
  real render cost is measured, not by default — they cost memory and complexity.
- **Keys must be stable and unique** across renders. Never use the array index
  when the list can reorder, insert, or delete.

## ❌ Bad — effect duplicating state that should be derived

```jsx
function Cart({ items }) {
  const [total, setTotal] = useState(0);
  // Extra render, stale-risk, no external system to sync with.
  useEffect(() => {
    setTotal(items.reduce((s, i) => s + i.price, 0));
  }, [items]);
  return <p>{total}</p>;
}
```

## ✅ Good — compute during render

```jsx
function Cart({ items }) {
  const total = items.reduce((s, i) => s + i.price, 0);
  return <p>{total}</p>;
}
```

## Research hook

On activation, `WebSearch` `"react <installed-version> best practices"`. Prefer
official docs (react.dev), then cross-check a second reputable source. Codify
findings with provenance `researched` + source URL + retrieval date. Never block
on a failed search — fall back to the rules above.

Source: best-practice · Confidence: medium
