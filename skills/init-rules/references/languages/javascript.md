# JavaScript conventions (Tier 2)

For plain JS (no TypeScript). Match the repo's module system and lint config first; the rules below are defaults.

## Modules
- Prefer ESM (`import`/`export`) over CommonJS (`require`/`module.exports`) in new code. Follow the repo — mixing systems in one package causes interop pain (`__esModule`, default-export mismatches).
- Keep module boundaries explicit: export the public surface, keep helpers unexported. Avoid deep imports into another module's internals.
- Avoid barrel `index.js` re-export files in hot paths; they defeat tree-shaking and can create circular imports.

## Bindings and equality
- Use `const` by default, `let` when reassignment is real. Never `var` — it is function-scoped and hoists, causing closure bugs in loops.
- Always `===` / `!==`. `==` triggers coercion (`0 == ''`, `null == undefined`). The one accepted idiom is `x == null` to catch both `null` and `undefined` — only if the repo already uses it.

```js
// ❌ Bad: var leaks past the block; == coerces
for (var i = 0; i < items.length; i++) {
  if (items[i].id == wanted) return items[i]; // '3' == 3 is true
}

// ✅ Good: block scope + strict equality
for (const item of items) {
  if (item.id === wanted) return item;
}
```

## Async
- Use `async`/`await` over raw `.then()` chains for readability and correct error propagation. Wrap awaited calls that can throw in `try/catch`.
- Run independent async work concurrently with `Promise.all`, not sequential awaits in a loop.
- Never leave a promise unhandled (no floating promises); either `await` it or attach a `.catch`.

```js
// ❌ Bad: sequential awaits, no error handling
const user = await getUser(id);
const posts = await getPosts(id); // waits needlessly

// ✅ Good: concurrent, errors surface to caller's try/catch
const [user, posts] = await Promise.all([getUser(id), getPosts(id)]);
```

## State and null-safety
- Do not mutate shared state or function arguments. Return new objects/arrays (`map`, `filter`, spread) instead of mutating in place.
- Use optional chaining `a?.b?.c` and nullish coalescing `x ?? fallback`. Prefer `??` over `||` when `0`/`''`/`false` are valid.

```js
// ❌ Bad: mutates the caller's array
function addTag(item, tag) { item.tags.push(tag); return item; }

// ✅ Good: returns a new object, leaves input untouched
function addTag(item, tag) { return { ...item, tags: [...item.tags, tag] }; }
```

## Types without TypeScript
- Document public functions with JSDoc `@param`/`@returns` types. With `// @ts-check` or a `checkJs` tsconfig, editors type-check JS from JSDoc — a cheap safety net short of migrating.

Source: best-practice · Confidence: high
