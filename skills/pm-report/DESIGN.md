# `pm-report` skill — design

**Date:** 2026-05-14
**Status:** approved (this doc), ready for implementation plan
**Skill location (after build):** `~/.claude/skills/lodestar/skills/pm-report/SKILL.md`

## Goal

Replace the long natural-language phrase the user types at end-of-session ("use plain English to explain what was done and how it works now, I need a report for PM. Do not make it too long.") with an auto-discovered skill that produces a PM-ready report directly in chat.

The user copies the report from chat into Slack / email / ClickUp.

## Decisions locked in brainstorming

| Decision | Value |
|---|---|
| Audience | PM only — single plain-English voice |
| Scope | Whole session, not "latest task" — user reviews entire conversation |
| Structure | Adaptive — shape follows the work, not a fixed template |
| Length control | Inclusion rules ("PM cares / PM doesn't care") — no word cap |
| Output | Chat only — never write to a file, never update memory |
| Trigger | Natural-language phrases — no slash command |
| Skill scope | Global (`~/.claude/skills/lodestar/skills/pm-report/`) — works across all projects |
| Language | Match the conversation's language — don't hardcode English |

## Inclusion rules (the brain of the skill)

### Include (PM cares)

- **The problem in business framing** — 1–2 sentences. *"Our X was wrong"* / *"Users couldn't Y"* / *"We were spending $N on Z."* Never *"the assembler returned 0"* — always the consequence.
- **What's different now from the user / PM's POV** — new capability, fixed behavior, removed risk. Concrete outcomes, not implementation. (*"Admin can now toggle X"* not *"Added ConfigKeyEnum::X"*.)
- **Cost / time / risk implications** — anything that affects budget, deploy timing, or downstream decisions.
- **Outstanding items the PM needs to act on or wait for** — confirmations needed, deploys to schedule, follow-ups created.
- **Trust signals — selectively** — *"All 824 tests pass including the 5 new ones we added"* is a signal (number + context). *"Lint clean"* is not (assumed). Test counts mentioned only when they bolster credibility.
- **Where the PM can verify** — only if there's a place to look (admin URL, screen, file). Skip if irrelevant.
- **Before/after scenarios** — when a behavior or output changed in a way that matters, show a concrete contrast. *Old: every Gemini run logged the same generic label; you couldn't tell Max from Preview. Now: each cost record carries the real agent name.* Skip when the contrast is trivial or implied.
- **How to find new surfaces** — for any new page, modal, admin setting, or config: the exact navigation path. *Admin → Conversations → click conversation → Researches → ⋮ → Spendings.* If the PM can't find it, they can't try it.
- **How to verify / reproduce** — a short repro path the PM can follow themselves. *Start a new research with variant = Preview, open the Spendings modal — four sub-rows should appear.* Skip when the change is invisible to the PM.

### Exclude (PM doesn't care)

- File paths, class names, function signatures, migration filenames, table column names.
- Internal refactors and code-style fixes (Pint passes, PHPStan clean — internal hygiene).
- Audit-and-fix loops — present the FINAL state. Never *"we found bugs in our own code then fixed them"* unless the audit caught a real production-blocking defect (see "save" rule below).
- Tool calls, my back-and-forth questions, design alternatives that were considered and dropped.
- Process narration (*"first I did X, then Y, then Z"*).
- Trade-offs the PM has no decision power over.

### Conditional rules (the skill judges case-by-case)

- **Before/after, navigation, repro** — apply only when they materially help the PM verify or use the change. A pure bugfix to an internal queue retry doesn't get nav paths or before/after — there's nothing the PM would see.
- **Audit saves** — if a self-review caught something user-impacting before ship, it's worth one sentence (boosts confidence in the work). Limit to 1 sentence; don't elaborate.
- **Multi-task synthesis** — if the session covers unrelated tasks, group per task. If they're related (impl + bugfix + docs for one feature), synthesize.

## Adaptive section templates

The skill picks one shape based on what was done. Section names are starting points — the skill can rename if it helps clarity.

### Shape A — New feature / capability shipped (default for most work)

```
The problem        — 1-2 sentences, business framing
What works now     — outcome bullets, grouped by area if needed
                     (use sub-headings only if 3+ distinct features)
How to see / try   — navigation path + repro steps (if applicable)
Quality bar        — trust signals only (selectively)
Outstanding items  — what's not done yet, what PM needs to act on
```

### Shape B — Bug fix

```
The bug            — what was wrong, what user saw / what we billed wrong / etc.
The fix            — one sentence on what changed
How to confirm     — verify steps the PM can run
Risk               — what we did to make sure we didn't break anything else
                     (only if there's a real risk worth flagging)
```

### Shape C — Investigation / no code shipped

```
The question       — what we set out to find
What we found      — concrete findings, with evidence
Recommendation     — what to do next
```

### Shape D — Multi-task session (multiple unrelated chunks)

```
This session covered N items. Each below stands alone.

### Item 1 — <one-line title>
<one of Shapes A/B/C compressed>

### Item 2 — <one-line title>
<one of Shapes A/B/C compressed>
```

### Selection rules

- Everything ties to one "what we shipped" outcome → **Shape A**.
- Everything is a single defect → **Shape B**.
- No code was changed (we just researched / decided / planned) → **Shape C**.
- 2+ unrelated chunks → **Shape D**, with each chunk in its own sub-shape.

Section names use plain English. No *"Implementation Notes,"* *"Acceptance Criteria,"* etc. — that's our jargon, not the PM's.

## Trigger phrases

The SKILL.md `description` will list natural phrases so the skill loader picks it up automatically:

> *Use when the user says "report for PM", "PM report", "report for the PM", "summary for PM", "summarize for PM", "give me a PM summary", "plain English session report", or any near-equivalent — wants a non-technical session summary for the project manager. Produces a chat-only adaptive report covering what shipped, how to find it, how to verify, and outstanding items.*

The description is in English but the matching is semantic — the model recognizes equivalent intent in other languages. *"Bericht für PM"* or *"PM-Bericht"* should still trigger.

## Hard rules

1. **Chat-only output.** Never write the report to a file. Never update memory.
2. **Match the conversation's language.** German session → German report. English → English. Don't hardcode.
3. **Whole session, not "the last task".** Review the full conversation from the start. If the user wanted only the latest task, they'd say so.
4. **No emojis, no hype, no "great job".** Plain professional tone — same discipline as `session-handoff`.
5. **Never invent state.** If a section has no real content, omit it entirely. Don't pad.
6. **Always do the include/exclude pass before writing.** Mentally check every paragraph against the rules above before emitting it.
7. **Heading format.** Top heading is `# <One-line outcome title>` — no fixed prefix like *"PM Report:"*. Title describes the outcome (*"Gemini Deep Research cost tracking now matches Google's bill"*), not the task number. PM thinks in outcomes.

## Anti-patterns (call out explicitly)

- Summarizing the last 3 turns and calling it a session report.
- Including audit-and-fix loops as "transparency." PM doesn't want to read about bugs introduced and removed in the same session — show the final state.
- Mentioning specific file paths, class names, function signatures unless the PM needs to navigate them.
- Listing every test that passed. *"All tests pass"* is enough. Cite numbers only when they add credibility.
- Writing a process narrative.
- Adding section names that don't apply (*"Outstanding items: None"* — just omit the section).
- Hedging (*"hopefully this addresses..."*, *"should now work"*). The skill either has evidence or it doesn't. State it.

## The "save" rule (when internal process IS worth surfacing)

If a self-audit caught a production-blocking defect before ship, surface it in one sentence — it's a positive signal (we have safeguards), not an admission of sloppiness.

Example from the session that motivated this skill: *"The original spend-cap code would have silently failed in production — caught in review before deploy."*

Limit to 1 sentence. Don't elaborate. Don't itemize audit findings.

## File structure

```
~/.claude/skills/lodestar/skills/pm-report/
├── SKILL.md      (required — YAML frontmatter + the rules above, formatted as guidance the model follows)
└── DESIGN.md     (this document — historical reference)
```

No bundled scripts, no references folder, no assets. The skill is pure guidance — no tooling needed.

## What this skill explicitly does NOT do

- Generate weekly status reports across multiple sessions (out of scope — different audience need).
- Produce client-facing reports (different tone — out of scope per audience decision).
- Multi-language variant selection (matches conversation language only).
- Cross-project synthesis (one session = one report).
- File output of any kind (chat-only by design).

## Reference: closest existing skill

`~/.claude/skills/session-handoff/SKILL.md` — same mechanism (analyzes session, produces structured output, chat-only, deterministic discipline) with a different audience (next Claude instance vs PM). Borrow its hard-rules pattern and anti-patterns format.
