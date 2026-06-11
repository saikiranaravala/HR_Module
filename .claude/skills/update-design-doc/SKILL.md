---
name: update-design-doc
description: Keep TechDesignDoc/ in sync with reality — create a module's design doc when design starts, and update it (with a change log) whenever implementation deviates from or extends the design. Use after any slice that changed schema, API, or behavior vs. the doc, or when asked to "update the design doc".
---

# Update Tech Design Doc

`TechDesignDoc/NN-<module>-design.md` must describe the system **as built**, not as first imagined. A design doc that drifts from the code is worse than none — reviewers trust it.

## When this skill fires

- A module enters design (`design-module` skill creates the doc here).
- An implementation slice changed anything the doc specifies: schema columns, API shape, sensitivity tiers, event/contract decisions, scope of a requirement ID.
- A gated decision resolved (e.g., payroll RFP) and the design's isolation interface can be made concrete.
- The user asks for a design-doc refresh or drift check.

## Steps

1. **Read** the module's doc in `TechDesignDoc/` and diff it mentally against the code in `src/<context>/` (models, routers, config). List every mismatch.
2. **Update the affected sections in place** — requirement-trace table, data model, APIs, edge-case test plan. The doc body always reflects the current state.
3. **Append to the doc's `## Change Log`** (create the section at the bottom if missing), newest first:

   ```markdown
   - **YYYY-MM-DD** — <what changed and why>. Trigger: <slice/decision>. Requirement IDs: <…>.
   ```

   Never rewrite old change-log entries; the log is the doc's history.
4. **Classify each change:**
   - *Deviation* (code does something the design didn't say) → also check whether it violates an Architecture Invariant in `CLAUDE.md`; if so, stop and raise it instead of documenting it as normal.
   - *Extension* (new scope) → must trace to a requirement ID, or be flagged as unscoped.
   - *Deferral* (designed but not built) → record in the doc **and** in `.claude/memory.md` with what re-enables it.
5. **Cross-update:** if the change affects build status, run the `update-progress` skill in the same pass.

## Drift check (when asked "is the doc current?")

Compare doc sections against code for: table/column lists, endpoint lists, tier assignments, config file names, test names in the edge-case coverage table. Report mismatches as a table (doc says / code says / which is right) — don't fix silently; deviations may be undocumented decisions.
