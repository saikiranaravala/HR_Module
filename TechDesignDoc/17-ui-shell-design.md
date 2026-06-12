# UI Shell Design — Meridian Web App (cross-module)

**Goal:** best-in-class web UI with a PeopleSoft-familiar interaction grammar (so 50K PS-trained users feel at home) under Meridian's own branding — minimum clicks, maximum usage.
**Stack:** React 19 + TypeScript + Vite (pinned toolchain), `react-router-dom`. No component library — the design system is owned (`UI/src/styles.css`), per the shared-design-system requirement.
**Status:** v1 shell + 16 screens, demo data layer. `npm run dev` (http://localhost:5199) · `npm run build` green.

## 1. PeopleSoft-familiar, Meridian-branded

| PS pattern kept | Meridian treatment |
|---|---|
| Dark global header band + ☰ NavBar | Navy `#15324E` gradient band; left work-center nav (PS NavBar moved left for ergonomics) |
| Fluid homepage selector ("Employee Self Service ▾") | Header dropdown switches persona homepages (Employee / Manager / Workforce Admin) |
| Fluid tile homepages with live KPIs | `tilegrid`/`tile` — KPI, icon, status flag, one click to the work area |
| Classic breadcrumb bar ("Main Menu >") | `crumbs` bar under the header: Homepage › Group › Page |
| Classic grids (light-blue headers, "Personalize \| Find \| View All") | `psgrid` + `GridBar` reproduce the furniture; zebra rows, dense 13.5px type |
| Gold action buttons | Amber `#F2A33C` CTAs; teal `#0E8074` primaries/links |
| EFFDT/EFFSEQ pages | Profile job history grid with an **as-of date picker** highlighting the row in force |

## 2. Minimum clicks, maximum usage

- **Ctrl+K command palette**: every page + quick actions (request PTO, latest payslip, approve-all-routine, find person) — anything in ≤2 keystrokes + Enter.
- **"Needs your attention" strip** on every homepage: deep links straight into the acting screen.
- One-click approve/reject per row; bulk approve with the no-bulk-on-comp guardrail surfaced in-UI.
- 2-click PTO request (tile → submit) with live balance projection ("balance on Dec 31 will be…").
- Inline merit entry with live budget bar; out-of-guideline justification demanded in-flow.
- Header notification bell = pending-approval count; persona switch is two clicks.

## 3. Structure

```
UI/src/
  styles.css        design system (tokens + shell + tiles + psgrid + forms…)
  data.ts           demo data layer — shapes mirror backend models 1:1 (swap for REST client)
  store.tsx         reducer store: persona, approvals, PTO, worksheet, pipeline, toasts
  components.tsx    GlobalHeader, NavBar, Crumbs, CommandPalette, Toasts, Tile, Modal, GridBar…
  pages/            16 screens: Home, Approvals, Team, Payslips, TimeAbsence, Benefits,
                    Profile, Directory, Performance, Learning, Help, CompCycle, Recruiting,
                    PayrollHub, Succession, Analytics
```

Every module Done in Progress.md has a screen, and each screen surfaces its module's governance behaviors (guardrails are UI-visible, not hidden): comp never bulk-approves; AI ranks but cannot reject; AI drafts require edit-before-submit; T3 views announce read-logging; suppressed analytics cells explain complementary suppression; payroll approval is blocked while anomalies are open.

## 4. Accessibility & i18n posture

Skip-nav link, ARIA labels on shell controls/dialogs, keyboard path for palette and modals (Esc/arrows/Enter), focus-visible outlines, WCAG-AA-checked contrast on tokens. Strings are not yet externalized — the i18n catalog is the first follow-up before any non-EN population (CLAUDE.md day-one rule; flagged, not dropped).

## 5. Open items

- Replace `data.ts` with the REST client once the FastAPI per-module routers land (store actions are dispatch-shaped for that swap).
- String externalization (i18n catalog), WCAG audit in CI, mobile/native surfaces, design-token doc page.

## Change Log

- **2026-06-11** — v1: scaffold, design system, shell (header/nav/crumbs/palette/toasts), 3 persona homepages, 16 screens, demo data layer. `tsc -b && vite build` green; dev-server smoke-tested.
