# Module 15 Design — Succession & Career Planning (Specs/09)

**Spec:** [Specs/09-succession.md](../Specs/09-succession.md) · **Package:** `src/succession/` · Tests: `src/test/succession/`
**Depends on:** platform_core (policy + read-audit — the defining feature here), performance (ratings/trend input), learning (skills), core_hr
**⚠ Gates:** ratings philosophy (9-box performance axis consumes PERF ratings as opaque strings — isolated); works-council inventory (DE/FR/NL talent-assessment consultation artifacts noted, not blocking local build); flight-risk model = aggregate-only pending 14-AI ethics review (deferred entirely).

## 1. Scope & Requirement Trace

| Req | Design element | Local scope |
|---|---|---|
| SUCC-1 (P1) | `slates.py`: key-position designation with criticality rubric (impact × scarcity × ramp), slates with readiness (now/1-2y/3y+) + mandatory rationale + last-validated staleness, emergency designee distinct from development successors, concentration-risk flag (1 person on ≥3 slates), retirement band (band, never date) | **Yes** (flight risk deferred — ethics gate) |
| SUCC-2 (P1) | `ninebox.py`: performance (PERF input, opaque) × potential (rubric input), **mandatory rationale, append-only immutable placement lineage** (same pattern as calibration); review session decision log | **Yes** (facilitator console = UI phase) |
| SUCC-3 (P2) | Career pathing/lattice | Deferred; aspiration **consent toggle** built now (privacy can't be retrofitted) |
| SUCC-4 (P1) | `access.py`: tiered access via central policy (`succession.read`, division-scoped roles), **incumbent self-block regardless of role**, T3 read-audit on every view, no-export default | **Yes** |

## 2. Data Model (schema `succession`)

| Table | Notes | Tier |
|---|---|---|
| `key_position` | criticality scores + rubric total, incumbent, division org_path, retirement band (band only) | **T3** |
| `slate_entry` | position, successor, readiness + rationale, `emergency` flag, last_validated, status (active\|gap) | **T3** (read-audited) |
| `talent_profile` | aspirations + `aspirations_consent` (manager visibility opt-in, default OFF), `interim` flag (acquisition cohort, limited history), mobility prefs | T2; aspirations consent-walled |
| `ninebox_placement` | performance×potential, mandatory rationale, session id — **DB-immutable append-only** | **T3** |
| `discovery_hold` | legal-discovery privilege workflow: scope, counsel, released flag | T3 |

Catalog tags: category `succession`, purpose `talent-management`, lawful basis `legitimate-interest` (potential ratings = personal data per GDPR — retention schedule + DSAR protocol noted), retention `succession-active+2y`.

## 3. Rules & Configuration Surface

- Criticality rubric weights in `config/criticality.yaml`.
- Readiness values and staleness threshold (12 months) are module constants; concentration threshold (3 slates) config-adjacent constant.
- Retirement eligibility: age/service rule evaluated to a **band** ("<3y", "3-5y", ">5y") — the date never leaves the function.

## 4. AI Touchpoints

None locally. Flight-risk display is deferred until the 14-AI governance/ethics review and would be aggregate-first (spec §8). AI never assigns potential or readiness (Invariant #6 extension — same posture as ratings).

## 5. Edge-Case Test Plan (register §7)

| Register row | Test |
|---|---|
| Successor terminates (slate-gap alert + review task) | `test_SUCC_successor_termination_gap_alert` |
| Incumbent sees own slate via inherited role (tier recompute) | `test_SUCC_incumbent_never_sees_own_slate` |
| Divisional reorg splitting slates | `test_SUCC_reorg_rehomes_slates_with_review` |
| Acquisition executive cohort (interim profiles) | `test_SUCC_acquisition_interim_profiles` |
| Legal discovery on talent decisions (privilege workflow) | `test_SUCC_legal_discovery_privilege_workflow` |

## 6. Key Decisions / Invariant Notes

- **Incumbent self-block is absolute:** `read_slate` denies the incumbent their own slate before the policy call and after it (role inheritance can never leak it — the register row's "tier recompute on every assignment event" collapses to: the check uses *current* incumbent identity at read time, so a role change can't stale it). Denial is audit-logged.
- 9-box placements and slate views ride the central policy engine + `read_with_audit` (Invariants #3, T3 read-logging). Employees never see slate placements about themselves — slates are simply not a reachable resource below the talent tiers.
- Placement lineage immutable at the DB (same trigger pattern as calibration/audit).
- Discovery requests: artifacts collected under a privilege hold; **counsel approval required before any release**; the hold and release are audited.

## 7. Open Items

- Potential rubric semantics (HR workshop, with ratings gate). Flight-risk ethics review. Works-council consultation artifacts for DE/FR/NL before processing talent assessments there.

## Change Log

- **2026-06-11** — Initial design. Trigger: Module 09 kickoff (auto-approved cadence).
- **2026-06-11** — Review fix: reorg re-homing matches division paths on '/' boundaries via `platform_core.orgpath`.
