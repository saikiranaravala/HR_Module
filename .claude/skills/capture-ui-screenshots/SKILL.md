---
name: capture-ui-screenshots
description: Regenerate the Training/screenshots/ images from the live demo UI with Playwright. Use after any UI change that alters a captured screen, when adding a new training scenario, or when asked to "update/refresh screenshots".
---

# Capture UI Screenshots

`Training/screenshots/` holds ~45 PNGs referenced by the scenario guides (Training docs 12–14). They are **generated, not hand-made** — the single source is `Training/screenshots/_capture.mjs`, which drives the Vite dev UI through every scenario across all three personas.

## Steps

1. **Start the stack** (from `UI/`):
   ```powershell
   npm install --no-save playwright      # first time only; --no-save keeps package.json clean
   npx playwright install chromium       # first time only
   npm run dev                           # keep running (port 5173)
   ```
2. **Run the capture:** `node ..\Training\screenshots\_capture.mjs` (from `UI/`). It prints each filename as it writes; a full run produces every screenshot in one pass.
3. **Spot-check the output** — Read 2–3 of the changed PNGs and verify: correct persona in the header/breadcrumb, the intended UI state (modal open, toast visible, pill rendered), no half-faded animations.
4. **Sync the guides:** if a screen's content changed (labels, numbers, layout), update the captions/prose in `Training/12–14-*.md` — captions cite exact on-screen values, so a data or copy change makes them lie.
5. **Scenario changes:** new scenario → add steps to `_capture.mjs` following the naming scheme `<persona>-<scenario>-<step>-<slug>.png` (e.g., `mgr-02-3-bulk-refused`), then reference the file from the guide. Delete orphaned PNGs when a scenario is removed.

## Gotchas (each cost real time — don't rediscover them)

- **`page.goto()` resets the persona.** A full navigation reloads React and the store resets to `employee`. After `selectOption('.gh-home-sel', ...)`, navigate **only** by clicking left-nav items (`.nav a.nav-item`). Employee scenarios may use `goto` because employee is the default.
- **Toasts auto-dismiss after ~4.2 s** — screenshot promptly after the triggering click (the script's built-in 350 ms settle is enough; don't add long waits before the shot).
- **The bulk-approve button clears the selection even when the action is refused** — re-check the checkboxes before the second attempt.
- **Playwright module resolution is script-location based** — the script imports `playwright` from `UI/node_modules`, so run `node` from `UI/`.
- Toast state persists across client-side navigation — order scenarios so a lingering toast can't photobomb the next screen (or navigate once to let it expire).
