---
name: explain
description: For a developer — walk through a change, mechanism, bug, task, decision or concept on one concrete example, in ordinary words
disable-model-invocation: true
---

# Explain

Make the subject genuinely understood. Not summarized — understood.

The audience is whoever asked, usually a developer, not always the author of the thing being
explained. Mechanism is welcome; what they lack is a model of *why* it works and *why the
obvious alternative does not*.

Explain only. Do not judge the approach or propose changes — that is `/lodestar:audit-solution`.

## Subject and scope

Whatever follows `/lodestar:explain` is the subject. With no argument, the subject is the
thing just worked on in this conversation.

Before explaining, know the thing: read the code, the logs, the diff, the ticket. An
explanation assembled from guesswork reads exactly as confident as a correct one, which is
what makes it dangerous.

**If the honest answer is one or two facts, state them and stop.** Not every question hides a
mechanism. Everything below applies only once the reader would otherwise be left with a wrong
or missing model.

## What an explanation must answer

Not an order — the shape below owns order and emphasis. This list only says what may not be
silently dropped. Leave an item out when the reader does not need it to hold a correct model,
not merely when the subject has no such element.

- **The actors, by their real names.** Every service, table, column, method, file, person, every time.
- **What each actor knows and does not know.** Most non-obvious problems come from a source being partial, stale, or authoritative over only part of the picture. Make that boundary explicit before describing any behaviour.
- **The conflict.** Where the actors overlap, disagree, or where one silently substitutes for another.
- **ONE example, carried the whole way through.** With a real system in scope, real identifiers and real values from it, its logs, or its measurements — never invented round numbers. With a real artifact holding no data (prose, config, a rule, a doc), one concrete case of it being read or applied. With a general concept and nothing to read, an invented example, marked as illustrative. It must not change mid-explanation.
- **The essence, in one sentence.** "We replaced adding the two numbers with taking the larger one." If it cannot be compressed, the explanation is not finished — keep working, do not paper over it with detail. State it as soon as the reader can see why it is true, never at the end.
- **Why the obvious simpler thing fails.** The reader is silently asking "why not just X". Name their X and kill it in one line each. Where nothing has been chosen yet (Shapes C and E), name the alternatives without picking one.
- **The evidence and the remainder.** Measured numbers if they exist, then what this does NOT cover or solve, and whose problem that is.

Where the subject is arithmetic or state, use a table, with the wrong result and the right one
both in it.

### Also, when the subject is a fix or a change

- **The same example on both sides**, before and after — otherwise the difference is asserted rather than shown.
- **What the old behaviour got wrong**, not only what the new one does.
- **A second case that pulls the other way**, where one exists. One example proves the fix; a case at the opposite extreme proves it does not break the other direction.
- **The root-cause fix separated from the mechanism**, when both exist. "This is what makes the input correct" versus "this is what keeps it correct as data changes."

## Shapes

Pick exactly one. First match wins:

- Live failure, no fix yet → **E**
- Nothing of the subject exists in this repo → **F**
- Nothing built yet, and the question is what to build → **C**
- Something was built or changed → **A**, even when a trade-off was involved; fold the rejected option into "why the obvious simpler thing fails"
- A choice was made but nothing built on it yet → **D**
- Otherwise → **B**

**A — a change that was made.** The checklist above in the order it is written, ending on measured result and remainder.

**B — how an existing thing works.** The actors and their boundaries → the path one real request or record takes through them → where it surprises people → the limits.

**C — what the problem or task is.** What is wanted → what blocks it → the tension that makes it non-trivial → what has to be decided before anything can be built. Do not invent a solution here.

**D — why this decision.** What was being chosen between → what each option costs, priced on the same concrete case → which was taken and the one fact that settled it → what is accepted as a downside.

**E — why it is failing.** What was observed, verbatim → which actor produced it → what it means in ordinary words → what is established versus still suspected → the next thing that would settle it.

**F — a concept or third-party thing.** What problem it exists to solve → how it works on one worked example → why the naive approach it replaces fails → where it applies here and where it does not.

## Hard rules

1. **Match the conversation's language.** Russian conversation → Russian explanation. Never hardcode.
2. **No metaphors, no placeholder nouns.** Not "the system", "the service", "the layer", "the pipeline", "the source". Use the proper name, or say the name is unknown.
3. **Translate jargon on first use, or drop it.** "Идемпотентно" becomes "повторный запуск не меняет результат". Keep only the terms the reader needs to work on the thing, and only after defining them once in ordinary words.
4. **Label anything not verified.** Measured facts, reasoning, and assumptions must read differently. Never present a derived expectation as a measurement, and never hedge in place of saying "unknown".
5. **Chat-only.** Never write the explanation to a file, never update memory. Reading is expected; writing is not part of this skill.
6. **No code blocks unless the code IS the subject.** At most the one line that carries the meaning.
7. **No process narrative.** Not "first I tried X, then Y" — only the final model, plus the dead ends the reader must know about to avoid repeating them.

## Anti-patterns

- Restating the diff in words. A list of changed files is not an explanation.
- Padding with everything known about the subject. Depth belongs where the reader would otherwise be confused, nowhere else.
