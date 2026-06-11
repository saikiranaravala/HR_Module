# Deep-Dive PRD 09 — Succession & Career Planning
*Project Meridian | Depends on: 01-Core, 07-Performance, 08-Learning (skills) | Feeds: executive talent reviews, 06-REC internal mobility*

## 1. Mission & Success Metrics
Know who can step into critical roles tomorrow, develop them deliberately, and give every employee a visible path — under the strictest confidentiality model in the suite.
- Key-position slate coverage: ≥ 95% of designated roles have ≥ 1 ready-now-or-1-2yr successor.
- Internal fill rate for key roles ≥ 60% within 24 months.
- Confidentiality: zero unauthorized-access events (read-audited domain).

## 2. Key Positions & Slates
Key-position designation: criticality scoring rubric (business impact, scarcity, ramp time) with approval; incumbent-risk panel (retirement-eligibility from age/service rules — displayed as band not date, flight-risk flag P2 from 11-Analytics model with strict aggregate-first access, performance trend). Slate: ordered successors with readiness (now / 1–2y / 3y+), readiness rationale, development-plan link, last-validated date with staleness alerts; emergency/interim designee distinct from development successors; cross-slate analytics (one person on 5 slates = concentration risk flag; diverse-slate composition metrics with suppression rules).

## 3. Talent Profiles & Reviews
Talent profile: career history (auto from Core), self-maintained aspirations + mobility preferences (geographic, timeline), skills (08-LEARN graph), experiences tags (P&L size, turnaround, international), performance trend (07), assessments on file. 9-box: performance (from PERF) × potential (talent-review input with defined rubric); **talent review meeting mode:** facilitator console — population grid, drag placement with mandatory rationale, side-by-side dossiers, decision log auto-minuted, pre/post snapshots immutable, action items (development moves, slate changes) committed as transactions from the session. Cadence support: annual divisional reviews rolling up to executive/board package (board-ready export: key-role coverage, top-talent retention risks — heavily redacted template).

## 4. Development & Career Pathing
Development plans: actions (experience assignments, mentoring pairings with matching support, coursework links to 08, stretch projects) with owners/dates/status; plan progress visible in next review cycle. Career lattice (employee-visible, P2): adjacency map from job catalog (common transition mining + curated paths), role profiles with skill requirements, gap view ("you have 7/10 skills for X; suggested learning…"), internal-opportunity matching: open requisitions (06), gigs/projects marketplace (P2), with recruiter-blind aspiration privacy (aspirations never visible to current manager without consent — explicit toggle).

## 5. Confidentiality Model (defining feature)
Access tiers: (T1) Executive talent team — full; (T2) Division HR leaders — own-division slates; (T3) Senior leaders — slates they own, never their own succession record; (T4) Managers — no slate access by default; employees — own talent profile only (never slate placements about them — emotional-harm + legal exposure). Read-access logging on every slate/9-box view (TECH-6 extension); screenshots-discouraged UI (no-export default, watermarked PDFs for board pack only); search index excludes succession objects for non-tier users; works-council consultation artifacts where talent assessment processing requires it (DE/FR/NL); GDPR: potential ratings = personal data — retention schedule + access-request handling protocol with legal review.

## 6. Events & APIs
Events: slate.changed, keyposition.designated, talentreview.completed (metadata only — payloads pull-gated by tier). APIs: tier-enforced slate/profile endpoints; PERF summary ingestion; LEARN skills ingestion; analytics aggregates with k-anonymity ≥ 5.

## 7. Edge Cases Register
Successor terminates (auto slate-gap alert + review task); incumbent sees own slate via inherited role change (tier recompute on every assignment event — tested); divisional reorg splitting slates; acquisition executive cohort (interim profiles with limited history); legal discovery request on talent decisions (privilege workflow with counsel).

## 8. Open Questions
Potential rubric and 9-box semantics: HR leadership workshop (with 07-PERF philosophy, month 4). Flight-risk model deployment ethics review (14-AI governance) before any individual-level display — recommend aggregate-only for ≥ first year.
