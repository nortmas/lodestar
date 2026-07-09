# Base — core principles (Tier 1)

> **Balance meta-rule (inherited by every generated rule).**
> Prefer the codebase's consistent existing pattern over generic best practice. Use best
> practice only when no consistent pattern exists, or when the existing pattern is a
> **security, correctness, or performance defect**. Working consistency beats theory; safety
> beats consistency. See `../balance-policy.md` for the full algorithm.

Universal principles the skill draws on when a concern has no more specific layer. Keep any
generated rule token-frugal — encode the project's decision, not a software-engineering lecture.

## Principles worth codifying (only if the repo doesn't already have its own take)

- **Consistency over correctness-in-isolation.** One project-wide way to do a thing beats a
  locally "better" way that no other file uses. This is the meta-rule in daily form.
- **Explicit over implicit.** Name things, type things, surface errors. No magic globals, no
  silent fallbacks that hide failure.
- **Small units.** Functions ≤ ~30 lines, files ≤ ~300 lines, nesting ≤ 3, params ≤ 4,
  cyclomatic complexity ≤ ~10 — tunable defaults, not dogma.
- **Fail fast, fail loud.** Validate at boundaries; throw/return errors early; never swallow.
- **Single responsibility.** A unit does one thing; a change has one reason.
- **DRY within reason.** Extract on the third repetition, not the first — premature abstraction
  is its own debt.
- **Least surprise.** Follow the idioms a competent reader of this stack would expect, unless
  the codebase has deliberately chosen otherwise (then follow the codebase).

## How base rules interact with specific layers

Precedence: `framework > language > base`. A base rule only surfaces in generated output when no
language/framework layer speaks to the same point, or to supply a cross-cutting default (naming,
architecture metrics, commit format). Never emit a base rule that a more specific layer already
covers — that just dilutes context.

## What NOT to codify from this file
Do not generate rules that restate general programming wisdom the model already knows
("write readable code", "avoid duplication"). Only turn a base principle into a project rule when
you can attach a **concrete, checkable** directive and, ideally, a real example from the repo.

Source: best-practice · Confidence: high
