---
name: update-training
description: Keep the Training/ curriculum in sync with the product — update persona docs and scenario walkthroughs when features, UI, config, or governance behavior change. Use after any user-visible change, or when asked to "update training" or add a persona/scenario.
---

# Update Training Documentation

`Training/` is a persona-based curriculum (see `Training/00-INDEX.md` for the full map): docs 01–11 are concept courses per persona; docs 12–14 are screenshot-per-step scenario walkthroughs; `screenshots/` holds the generated images. Training is a **program deliverable tracked in Progress.md** — treat drift the same way as design-doc drift.

## Conventions (match them exactly)

- **Grounded, never generic:** every claim cites as-built behavior — real screen text, real config file paths (`src/<module>/config/*.yaml`), real commands, real named tests, the demo cast (Avery Quinn / Morgan Lee / Sam Rivera + the 9-person SQL seed). If you can't point at the artifact, don't write the sentence.
- **Structure per concept doc:** audience/duration/prereqs header → learning objectives → timed modules with hands-on exercises against the demo environment → **competency checklist** (the sign-off gate) → FAQ/hard-lines where relevant.
- **Structure per scenario doc:** situation → numbered steps, one screenshot per state → "what to notice" callouts tying the UI moment to the governing invariant → recap table.
- **Synthetic data only** in every example and screenshot (Invariant #8 — applies to training materials too).
- **Governance beats are the point:** prefer scenarios where the system *pushes back* (bulk refusal, anomaly gate, T3 read receipt, mandatory rationale) over happy paths.

## Steps

1. **Identify blast radius:** which personas see the change? A payroll-gate change touches 03, 07, 14; a UI navigation change touches 01, 12–14; a policy/tier change touches 02, 03, 09, 10.
2. **Update the affected docs in place** — including competency checklists if the observable behavior changed (checklists are what certification observes).
3. **Screenshots:** if any captured screen changed, run the `capture-ui-screenshots` skill and re-verify captions against the new images.
4. **Index:** new doc or duration change → update the map and learning paths in `Training/00-INDEX.md`.
5. **Cross-references:** training cites Deploy-local.md / Deploy-Render.md and specific config files — verify the paths still exist before publishing (memory and docs go stale; the repo is the truth).
6. **Log it:** `update-progress` skill, program-level entry.

## Adding a new persona

Copy the structure of the closest existing doc (03 for operational roles, 04/05 for consultant roles), number it sequentially, wire it into 00-INDEX (map + learning path + go-live minimums), and give it a competency checklist that a super user could observe unaided.
