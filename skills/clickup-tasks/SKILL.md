---
name: clickup-tasks
description: Use when creating a task/ticket in ClickUp — a new feature, bug, change request, or dev to-do. Ensures the task follows the board's title convention, is assigned to Dmitry, carries the board's standard custom fields, and gets a realistic vibe-coding estimate. Always shown as a draft first, created only after Dmitry's explicit OK.
---

# ClickUp Tasks

How to create a ClickUp task. This skill is project-agnostic — it holds the
process; project-specific values (list, custom fields, project name) are
discovered at runtime, never hardcoded here.

## Resolve the project context first

Before drafting, establish the target board's specifics:

- **List:** if the current project's `CLAUDE.md` documents ClickUp list IDs,
  use them. Otherwise resolve with `mcp__clickup__clickup_get_list` /
  `mcp__clickup__clickup_get_workspace_hierarchy`, or ask Dmitry which list.
- **Title convention:** scan a few recent task titles in that list
  (`mcp__clickup__clickup_filter_tasks`) and match their format — don't assume.
- **Custom fields:** fetch them with
  `mcp__clickup__clickup_get_custom_fields` for the target list. Set the ones
  the board uses (see Custom fields below). Never hardcode field IDs — they
  differ per board and can change.

## Title format

`[Area] Verb-first short description` — in **English**, matching the board.

- **Follow the board's existing tag convention.** A common dev pattern is an
  area tag plus an optional type tag: `[BE]`, `[FE]`, `[BE][FE]`, with
  `[BUG]` / `[CR]` (change request) / `[Design]` when they apply — e.g.
  `[BE] Add soft delete`, `[FE][BUG] Issue with citation`. If the board uses
  a different convention, match that instead.
- **Verb first:** Add / Fix / Implement / Setup / Prepare / Make / Harden /
  Verify / Migrate.
- **Short.** Details go in the description, not the title.

## Description

- Written for a developer (Dmitry), so technical detail is fine — unlike
  ticket *comments*, which are for the PM.
- Cover: what needs doing, why, and acceptance criteria / done-condition.
- Markdown is supported (`markdown_description`).

## Estimate (vibe coding)

`time_estimate` is **Dmitry's real hands-on time** working with Claude Code
— prompting, reviewing, testing, iterating — NOT traditional manual-coding
man-hours. It is usually far lower than a hand-coded estimate.

Rough anchors (Claude-Code-assisted wall-clock; always adjust to the task):

| Size | Examples | Estimate |
|---|---|---|
| Trivial | copy/config tweak, one-liner | 15–30 min |
| Small | single-area bugfix or small feature | 30–90 min |
| Medium | multi-file feature, some iteration | 2–4 h |
| Large | cross-cutting change, multiple areas | 4–8 h |

`time_estimate` is passed **in minutes as a string** (e.g. `"150"` = 2h 30m).
Always propose a number and let Dmitry confirm or adjust it — estimates are
guesses, not facts.

## Assignee

Always Dmitry — `assignees: ["me"]` (resolves to Dmitry's user ID).

## Custom fields

Set the board's standard fields, using the IDs and dropdown option UUIDs
returned by `clickup_get_custom_fields` for the target list. Dropdown values
are passed as the **option UUID** string in the `custom_fields` array.

- **Project name field:** set it to the option matching the **current
  project**, not a fixed value. If the current project isn't obvious or has
  no matching option, ask Dmitry.
- **Category / area field:** map from the task's area. Single-select boards:
  for a multi-area task pick the dominant area.
- **Tracker / type field:** map from the title's type tag — bug → Bug,
  change request → Change Request, investigation-only → Research, otherwise
  Feature.
- Skip fields the board doesn't define. If a value is rejected, re-fetch the
  field definitions and use the fresh IDs — don't guess.

## Procedure (never skip a step)

1. **Resolve project context** (list, title convention, custom fields) as
   above.
2. **Draft the task** — title, description, and pick the area/type values
   from the content.
3. **Propose the estimate** per the vibe-coding rules.
4. **Show the full draft to Dmitry** — title, description, list, assignee,
   custom fields, and the estimate. Do NOT create it yet.
5. **Wait for explicit confirmation.** Any reply that isn't a clear "create
   it" / "ок" is treated as edits — revise and re-show.
6. **Create only after OK** via `mcp__clickup__clickup_create_task` with
   `list_id`, `name`, `markdown_description`, `assignees: ["me"]`,
   `time_estimate` (minutes as string), and the `custom_fields` array. Report
   back the new task's custom id and URL.
