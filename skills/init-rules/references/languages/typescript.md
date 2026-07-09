# TypeScript conventions (Tier 2)

Codify the repo's actual `tsconfig.json` / ESLint config; the rules below are defaults when the repo has no strong signal.

## Compiler strictness
- Require `strict: true`. It implies `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`, and more; never relax individual flags to silence errors.
- Add `noUncheckedIndexedAccess` when the repo already uses it — index access then yields `T | undefined`, forcing a guard.
- Treat type errors as build failures in CI. `// @ts-ignore` is a last resort; prefer `// @ts-expect-error` with a reason so it self-removes when the underlying issue is fixed.

## Typing at boundaries
- Untyped external input (JSON, `fetch`, `JSON.parse`, event payloads) is `unknown`, never `any`. Narrow with a type guard or a schema validator (zod/valibot) before use.
- `any` disables checking transitively — one `any` poisons everything it touches. Ban it in `lint`; reach for generics or `unknown` instead.

```ts
// ❌ Bad: any bypasses every downstream check
function parseUser(raw: any) {
  return { id: raw.id, name: raw.name }; // no guarantees, silent at runtime
}

// ✅ Good: unknown forces validation at the boundary
function parseUser(raw: unknown): User {
  return UserSchema.parse(raw); // zod throws on shape mismatch
}
```

## Modeling
- Model mutually-exclusive states as a discriminated union with a literal `kind`/`type` tag, not a bag of optional fields. `switch` on the tag gets exhaustiveness checking via a `never` default.
- Prefer union literals over `enum`. Enums emit runtime code and have quirky numeric behavior; `type Status = 'idle' | 'loading' | 'done'` is erased and infers cleanly. Follow the repo if it standardizes on `const enum` or string enums.
- Use `interface` for object/contract shapes that may be extended; `type` for unions, tuples, mapped, and function types. Pick one for plain objects and stay consistent with the repo.
- Use `as const` for literal tuples and config objects to preserve narrow literal types instead of widening to `string`/`number`.

```ts
// ❌ Bad: optionals allow impossible combinations (data + error both set)
interface Result { loading: boolean; data?: User; error?: Error; }

// ✅ Good: discriminated union makes illegal states unrepresentable
type Result =
  | { kind: 'loading' }
  | { kind: 'ok'; data: User }
  | { kind: 'err'; error: Error };
```

## Escape hatches
- Avoid non-null `!`. It asserts away `null`/`undefined` with zero runtime check and rots as code changes. Use a guard, optional chaining, or a default.
- Prefer `x ?? fallback` over `x || fallback` when `0`, `''`, or `false` are valid values.

```ts
// ❌ Bad: ! hides a real null; crashes at runtime if the element is missing
const el = document.querySelector('#app')!;

// ✅ Good: narrow explicitly
const el = document.querySelector('#app');
if (!el) throw new Error('#app not found');
```

## Tooling
- Codify the repo's ESLint + Prettier setup as the source of truth (`typescript-eslint` for type-aware rules). Do not hand-format against Prettier; run it.
- Formatting is not a review topic once Prettier runs in CI or pre-commit — never argue style in PRs.

Source: best-practice · Confidence: high
