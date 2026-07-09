# UI/UX (Tier 2)

Cross-cutting UI/UX guidance for any frontend stack. Framework idioms live in
`../frameworks/vue.md` and `../frameworks/react.md`; utility/token mechanics in
`../packages/frontend/tailwind.md`. Balance policy: the codebase's own design
system and component conventions win over generic taste — override only for a
real defect (accessibility breaks are covered separately in `accessibility.md`).

## Use the design system, not one-off styling
Reference theme tokens (colors, spacing, radii, typography) — never hardcode a
magic hex or pixel value that duplicates a token. One-off styling drifts from the
system and blocks theming. See `../packages/frontend/tailwind.md` for token setup.

## Reuse components; consistent component API
Reach for the existing component before re-implementing. When authoring a shared
component, keep the API predictable: prop names match the system's convention,
sensible defaults, and one clear model for state — controlled OR uncontrolled, not
a muddle. Expose `value`+`onChange` (controlled) or `defaultValue` (uncontrolled),
never require both.

## Every async view has loading, empty, and error states
A view that fetches has four states, not one. Missing loading/error states are a
defect, not a style choice — the user is left staring at a blank or frozen screen.

❌ Bad — only the happy path; blank on load, silent on failure
```jsx
function Orders() {
  const { data } = useOrders();
  return <ul>{data.map((o) => <li key={o.id}>{o.name}</li>)}</ul>;
}
```
✅ Good — design-system components, all states, tokens not ad-hoc styles
```jsx
function Orders() {
  const { data, isLoading, error } = useOrders();
  if (isLoading) return <Spinner label="Loading orders" />;
  if (error) return <ErrorState onRetry={refetch} />;
  if (!data.length) return <EmptyState title="No orders yet" />;
  return (
    <Stack gap="sm">
      {data.map((o) => <OrderRow key={o.id} order={o} />)}
    </Stack>
  );
}
```

## Feedback on every action
Reflect the outcome of what the user did. Disable the trigger while a request is
pending so it cannot be double-fired; show a spinner or optimistic update. For
optimistic UI, always roll back and surface an error if the request fails.

❌ Bad — no pending state, double-submit charges twice
```jsx
<button onClick={submit}>Pay</button>
```
✅ Good — disabled + pending affordance
```jsx
<Button onClick={submit} disabled={isPending} loading={isPending}>
  {isPending ? "Processing…" : "Pay"}
</Button>
```

## Form UX
Validate inline near the field, on blur or submit — not only via a distant banner.
Error messages say what to fix, not just "invalid". Never wipe the user's input on
a failed submit; preserve every field. Associate errors with their input (see
`accessibility.md` for `aria-describedby`/`aria-invalid`).

## Responsive, mobile-first
Design for the small viewport first, layer enhancements up with min-width
breakpoints. Content must not overflow or require horizontal scroll on mobile.
Use the system's breakpoint tokens, not arbitrary widths.

## Avoid layout shift; consistent spacing scale
Reserve space for async content (skeletons, fixed dimensions, aspect-ratio boxes)
so incoming data does not shove the layout. Cumulative layout shift is a
measurable defect. Space with the scale (`gap`, spacing tokens) — not stray
margins that drift off the grid.

## Don't reinvent native controls
Use real `<select>`, `<input type="date">`, `<a href>`, `<dialog>` and friends
before hand-rolling a JS replacement. Native controls bring keyboard, focus, and
platform behavior for free; custom ones usually shed it. If the design system
already wraps a native control, use that wrapper.

Source: best-practice · Confidence: high
