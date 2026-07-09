# pm-report Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a global Claude Code skill that auto-discovers natural-language triggers ("report for PM", etc.) and produces a chat-only adaptive PM report covering what shipped, how to find it, how to verify, and outstanding items.

**Architecture:** A single `SKILL.md` file under `~/.claude/skills/lodestar/skills/pm-report/`. The file is YAML-frontmatter + Markdown guidance — no scripts, no bundled resources, no tooling. The Claude Code skill loader scans the `description` and auto-invokes when the user's message matches semantically.

**Tech Stack:** Markdown. YAML frontmatter. That's the whole stack.

**Spec:** `~/.claude/skills/lodestar/skills/pm-report/DESIGN.md` is the source of truth for what the skill should contain. This plan lifts that content into `SKILL.md` with minor rewording for the "agent reading instructions" register.

---

## File Structure

| File | Purpose | Status |
|---|---|---|
| `~/.claude/skills/lodestar/skills/pm-report/DESIGN.md` | Historical design doc (the spec) | Already exists |
| `~/.claude/skills/lodestar/skills/pm-report/SKILL.md` | The skill itself — what the Claude Code skill loader reads | **To create** |
| `~/.claude/skills/lodestar/skills/pm-report/PLAN.md` | This file | Already exists |

No other files. No scripts. No bundled references. The skill is pure guidance.

---

### Task 1: Write the SKILL.md file

**Files:**
- Create: `/Users/dmitryantonenko/.claude/skills/lodestar/skills/pm-report/SKILL.md`

- [ ] **Step 1: Write the complete file**

Write this exact content to `/Users/dmitryantonenko/.claude/skills/lodestar/skills/pm-report/SKILL.md`:

````markdown
---
name: pm-report
description: Use when the user says "report for PM", "PM report", "report for the PM", "summary for PM", "summarize for PM", "give me a PM summary", "plain English session report", "Bericht für PM", "PM-Bericht", or any near-equivalent — wants a non-technical session summary for the project manager. Produces a chat-only adaptive report covering what shipped, how to find it, how to verify, and outstanding items. Always reviews the whole session, not just the latest task. Never writes to a file.
---

# PM Report

Produce a non-technical, PM-ready summary of everything done in the current session. The PM copies it from chat into Slack / email / ClickUp / a status comment.

This is a **stakeholder-facing artifact**, not a context handoff. Audience is a non-engineer who cares about outcomes, costs, deploy-readiness, and what they can verify themselves — not file paths, class names, or process narratives.

## When to invoke

User says: "report for PM", "PM report", "report for the PM", "summary for PM", "summarize for PM", "give me a PM summary", "plain English session report", "Bericht für PM", "PM-Bericht", or any near-equivalent intent. Description matching is semantic — equivalent intent in any language triggers the skill, not just the listed phrases.

## How to produce the report

1. **Review the FULL conversation**, not just the last few turns. Whole-session scope is mandatory — if the user wanted only the latest task, they'd say so.
2. **Apply the include / exclude rules below to every paragraph** before writing it. This is the length control — there is no word cap.
3. **Pick one adaptive shape** based on what was done. Use the selection rules.
4. **Match the conversation's language.** German session → German report. English → English. Don't hardcode.
5. **Produce the output in chat.** Do not write a file. Do not update memory. Chat-only by design.

## What goes IN — PM cares

- **The problem in business framing** — 1–2 sentences. "Our X was wrong" / "Users couldn't Y" / "We were spending $N on Z." Never "the assembler returned 0" — always the user-visible consequence.
- **What's different now from the PM / user's POV** — new capability, fixed behavior, removed risk. Concrete outcomes, not implementation. "Admin can now toggle X" — not "Added ConfigKeyEnum::X".
- **Cost / time / risk implications** — anything affecting budget, deploy timing, or downstream decisions.
- **Outstanding items the PM needs to act on or wait for** — confirmations needed, deploys to schedule, follow-ups created.
- **Trust signals — selectively.** "All 824 tests pass including the 5 new ones we added" is a signal (number + context). "Lint clean" is not (assumed). Cite test counts only when they bolster credibility.
- **Before/after scenarios** when behavior or output changed in a way that matters. *Old: every Gemini run logged the same generic label, you couldn't tell Max from Preview. Now: each cost record carries the real agent name.* Skip when contrast is trivial or implied.
- **How to find new surfaces.** For any new page, modal, admin setting, or config — give the exact navigation path. *Admin → Conversations → click conversation → Researches → ⋮ → Spendings.* If the PM can't find it, they can't try it.
- **How to verify / reproduce.** A short repro path the PM can follow. *Start a new research with variant = Preview, open the Spendings modal — four sub-rows should appear.* Skip when the change is invisible to the PM (pure refactor, internal hygiene).

## What stays OUT — PM doesn't care

- File paths, class names, function signatures, migration filenames, table column names.
- Internal refactors and code-style fixes (Pint passes, PHPStan clean — internal hygiene).
- Audit-and-fix loops. Present the **final state**. Never "we found bugs in our own code then fixed them" — exception below in "The save rule".
- Tool calls, internal back-and-forth, design alternatives that were considered and dropped.
- Process narration ("first I did X, then Y, then Z").
- Trade-offs the PM has no decision power over.

## Conditional rules (judge case-by-case)

- **Before/after, navigation, repro** — apply only when they materially help the PM verify or use the change. A pure bugfix to an internal queue retry doesn't get nav paths or before/after — there's nothing the PM would see.
- **Multi-task synthesis** — if the session covers unrelated tasks, group per task (Shape D). If they're related (impl + bugfix + docs for one feature), synthesize into a single shape.

## Adaptive section shapes — pick one

Section names are starting points. Rename if it helps clarity. Plain English only — no "Implementation Notes", "Acceptance Criteria", etc.

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
<one of Shapes A/B/C, compressed>

### Item 2 — <one-line title>
<one of Shapes A/B/C, compressed>
```

### Selection rules

- Everything ties to one "what we shipped" outcome → **Shape A**.
- Everything is a single defect → **Shape B**.
- No code was changed (we just researched / decided / planned) → **Shape C**.
- 2+ unrelated chunks → **Shape D**, with each chunk in its own sub-shape.

## Hard rules

1. **Chat-only output.** Never write the report to a file. Never update memory.
2. **Match the conversation's language.** German session → German report. English → English. Don't hardcode.
3. **Whole session, not "the last task".** Review the full conversation from the start.
4. **No emojis, no hype, no "great job".** Plain professional tone — same discipline as `session-handoff`.
5. **Never invent state.** If a section has no real content, **omit the section entirely**. Don't pad. Don't write "Outstanding items: None" — just skip the section.
6. **Always do the include / exclude pass before writing.** Mentally check every paragraph against the rules above before emitting it.
7. **Heading format.** Top heading is `# <One-line outcome title>` — no fixed prefix like "PM Report:". Title describes the outcome (*"Gemini Deep Research cost tracking now matches Google's bill"*), not the task number. PM thinks in outcomes.

## Anti-patterns — do not do these

- Summarizing the last 3 turns and calling it a session report.
- Including audit-and-fix loops as "transparency". PM doesn't want to read about bugs introduced and removed in the same session — show the final state.
- Mentioning specific file paths, class names, function signatures unless the PM needs to navigate them.
- Listing every test that passed. "All tests pass" is enough. Cite numbers only when they add credibility ("all 824 tests including the 5 we added").
- Writing a process narrative.
- Adding section names that don't apply ("Outstanding items: None" — just omit the section).
- Hedging ("hopefully this addresses...", "should now work"). Either there's evidence or there isn't. State it.

## The "save" rule (when internal process IS worth surfacing)

If a self-audit caught a production-blocking defect before ship, surface it in **one sentence** — it's a positive signal (we have safeguards), not an admission of sloppiness.

Example: *"The original spend-cap code would have silently failed in production — caught in review before deploy."*

Limit to 1 sentence. Don't elaborate. Don't itemize audit findings. Don't apply for trivial / cosmetic catches.
````

- [ ] **Step 2: Verify the file was written to the correct location**

Run: `ls -la /Users/dmitryantonenko/.claude/skills/lodestar/skills/pm-report/`

Expected output includes:
```
DESIGN.md
PLAN.md
SKILL.md
```

If `SKILL.md` is missing or in the wrong path, the skill loader won't find it. Fix the path before continuing.

- [ ] **Step 3: Verify the YAML frontmatter parses**

Run:
```bash
python3 -c "
import sys
with open('/Users/dmitryantonenko/.claude/skills/lodestar/skills/pm-report/SKILL.md') as f:
    content = f.read()
if not content.startswith('---\n'):
    print('FAIL: missing opening frontmatter delimiter'); sys.exit(1)
end_idx = content.find('\n---\n', 4)
if end_idx == -1:
    print('FAIL: missing closing frontmatter delimiter'); sys.exit(1)
frontmatter = content[4:end_idx]
import yaml
try:
    parsed = yaml.safe_load(frontmatter)
except Exception as e:
    print(f'FAIL: YAML parse error: {e}'); sys.exit(1)
required = {'name', 'description'}
missing = required - set(parsed.keys())
if missing:
    print(f'FAIL: missing required keys: {missing}'); sys.exit(1)
if parsed['name'] != 'pm-report':
    print(f'FAIL: expected name=pm-report, got {parsed[\"name\"]!r}'); sys.exit(1)
if len(parsed['description']) < 100:
    print(f'FAIL: description suspiciously short ({len(parsed[\"description\"])} chars)'); sys.exit(1)
print('OK: frontmatter valid')
print(f'  name: {parsed[\"name\"]}')
print(f'  description length: {len(parsed[\"description\"])} chars')
"
```

Expected output:
```
OK: frontmatter valid
  name: pm-report
  description length: <some-number-around-450>
```

If FAIL: re-read the SKILL.md, fix the frontmatter, repeat.

- [ ] **Step 4: Verify no broken cross-references**

The skill mentions `session-handoff` as a tone reference. Confirm that skill exists:

Run: `ls /Users/dmitryantonenko/.claude/skills/session-handoff/SKILL.md`

Expected: file exists. If it doesn't, the analogy in the SKILL.md is dangling but not fatal — the skill still works on its own. Note in handoff if absent, otherwise continue.

- [ ] **Step 5: Decide whether to commit**

`~/.claude/` may or may not be a git repository on this machine.

Run: `cd /Users/dmitryantonenko/.claude && git rev-parse --is-inside-work-tree 2>/dev/null`

- If output is `true` → run `git status` and check if the user wants the skill committed alongside other `.claude` changes. Ask before committing.
- If output is empty / errors → `~/.claude/` is not tracked. Skip commit. The skill works without it.

Do NOT initialize a new git repo in `~/.claude/` — that's a user-level decision, not implementation scope.

---

### Task 2: Smoke-test the skill triggers in a fresh session

**Files:** none (procedural test the user runs)

The skill loader auto-discovers skills at the start of each Claude Code session. The skill cannot be tested in the current session because the loader's snapshot is already taken — it has to be a fresh session.

- [ ] **Step 1: Document the verification procedure for the user**

The user should:

1. Open a new Claude Code session in any project.
2. Do any small task (e.g. answer a question, read a file, fix a typo).
3. Type one of the trigger phrases — recommended: "give me a PM report" or "Bericht für PM".
4. Verify Claude invokes the `pm-report` skill (it'll announce: "Launching skill: pm-report" or similar) and produces a chat-only report.

**Acceptance criteria for the smoke test:**

- ✅ The skill triggers without the user having to type the literal name `pm-report`.
- ✅ The output appears in chat — no file is written under `docs/`, `~/.claude/`, or anywhere else.
- ✅ The report uses one of the four adaptive shapes (A / B / C / D) — not a generic "what I did" essay.
- ✅ Section names are plain English (or German), no project jargon.
- ✅ No file paths or class names in the output unless the PM needs them to navigate.

**If the skill doesn't trigger:**
- Check the description in `SKILL.md` for typos.
- Check the file path is exactly `~/.claude/skills/lodestar/skills/pm-report/SKILL.md` (singular `pm-report` folder, not plural).
- Try a different trigger phrase from the list.

This smoke test is the only meaningful end-to-end test — there's no automated test framework for skill auto-discovery in Claude Code.

- [ ] **Step 2: Report results back**

Once the user has run the smoke test in a fresh session, the skill is live. No further work.

---

## Self-Review

Spec coverage check — every line item in `DESIGN.md`:

| DESIGN.md section | Covered by |
|---|---|
| Goal | Task 1 Step 1 (skill body's "When to invoke" + "How to produce") |
| Decisions locked | Task 1 Step 1 (entire SKILL.md content) |
| Inclusion rules | Task 1 Step 1 ("What goes IN" + "What stays OUT" sections) |
| Adaptive section templates | Task 1 Step 1 ("Adaptive section shapes" section) |
| Trigger phrases | Task 1 Step 1 (YAML `description`) |
| Hard rules | Task 1 Step 1 ("Hard rules" section) |
| Anti-patterns | Task 1 Step 1 ("Anti-patterns" section) |
| The "save" rule | Task 1 Step 1 ("The save rule" section) |
| File structure | Task 1 Step 2 (`ls` verification) |
| Out-of-scope items | Naturally excluded by not appearing in SKILL.md |

No spec gaps.

Placeholder scan: no TBDs, no TODOs, no "implement appropriate handling" hedges. Every step has concrete content.

Type consistency: there are no types or signatures — this is a pure-Markdown skill.

Plan is complete and ready to execute.

---

## Execution Handoff

Plan complete and saved to `/Users/dmitryantonenko/.claude/skills/lodestar/skills/pm-report/PLAN.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints.

For a 2-task plan where Task 2 is procedural (the user runs the smoke test), **inline execution** is overkill of an overkill — the actual machine work is just Task 1 (write SKILL.md, verify it parses). I can do that inline directly.

Which approach?
