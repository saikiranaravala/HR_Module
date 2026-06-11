---
name: update-progress
description: Record completed work in Progress.md — update the module status table and append a dated log entry. Use after finishing any unit of work (design doc, schema, slice, tests), or when asked "where are we?" / "update progress".
---

# Update Progress

`Progress.md` (repo root) is the single source of truth for build status. Keep it honest: it records what *is*, verified, not what's intended.

## Steps

1. **Read `Progress.md`** — the status table and the most recent log entries.
2. **Update the module's row** in the status table if its stage changed. Allowed transitions: `Not Started → Design → In Progress → Testing → Done`. Rules:
   - `Design` requires the design doc to exist in `TechDesignDoc/`.
   - `Testing` requires all P0 slices implemented.
   - `Done` requires the PRD Edge Cases Register fully covered by passing named tests (see `edge-case-tests` skill) — state the final count.
   - Never move a status forward on intention ("about to finish") — only on verified artifacts.
3. **Append a log entry** at the top of the Progress Log (reverse-chronological):

   ```markdown
   ### YYYY-MM-DD — <Module NN name>: <one-line summary>
   - **Status:** <old> → <new> (or unchanged)
   - **Requirement IDs:** CORE-3, CORE-7 …
   - **Done:** what was actually built/verified, with test results if tests ran.
   - **Next:** the single next step for this module.
   - **Blockers:** open gates or issues (omit if none).
   ```

4. **If something non-obvious was learned** (PRD ambiguity, reversed decision, constraint discovered), also append it to `.claude/memory.md` — Progress.md says *what happened*, memory.md says *what we know now*.
5. **Report failures plainly.** Failing tests, skipped scenarios, or partial slices go in the log as-is. A log entry that hides a failure is worse than no entry.
