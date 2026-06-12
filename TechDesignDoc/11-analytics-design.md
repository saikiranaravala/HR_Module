# Module 10 Design — Workforce Analytics & Reporting (Specs/11)

**Spec:** [Specs/11-analytics.md](../Specs/11-analytics.md) · **Package:** `src/analytics/` · Tests: `src/test/analytics/`
**Depends on:** platform_core (policy passthrough, immutability guard), core_hr / payroll_hub / time_labor (source data via service calls — events/CDC deferred per memory)

## 1. Scope & Requirement Trace

| Req | Design element | Local scope |
|---|---|---|
| ANLT-1 (P0) | `reports.py`: report runner with **inherited row/field security** — every report row passes through the central policy engine (`person.read` scope + tier filtering via `serialize_filtered`); a report can never show what the UI denies (cross-surface suite) | **Yes** (report builder UI, schedule/burst, watermark/DLP = cloud/UI phase; PeopleSoft disposition = migration workstream, Module 16) |
| ANLT-2 (P1) | `semantic.py` metrics: point-in-time headcount (FTE-weighted variant), annualized turnover w/ regrettable split, span of control; `suppression.py`: n<5 with **complementary suppression** (no residual disclosure by subtraction) | **Yes** (dashboards/Sankey = UI phase) |
| ANLT-3 (P1) | `scd2.py`: `DimWorker` SCD2 dimension mirroring effective dating, built by direct service calls (CDC/Kafka deferred); `config/metrics.yaml`: governed metric registry (definition, formula, grain, owner, change log) — **one definition per metric**; `snapshots.py`: certified daily snapshots, immutable, restatement-by-new-version | **Yes** (Iceberg/dbt/BI connectors = N/A-local, documented not dropped) |
| ANLT-4 (P2) | Deferred entirely (ethics-gated; aggregate-first attrition policy noted for the future AI-governance review) | No |

## 2. Data Model (schema `analytics`)

| Table | Notes | Tier |
|---|---|---|
| `dim_worker` | SCD2: worker_id, valid_from/valid_to, org_path, country, worker_type, fte, regrettable-exit flag. Tokenized identifier (`worker_key`), no names/PII — PII-vault pattern | T1 |
| `certified_snapshot` | (as_of, metric, value, version, restatement_of, annotation) — **immutability-guarded**; restatement = new version row pointing at the original, never an UPDATE | T1 |
| `org_bridge` | old_org_path → new_org_path @ effective_date — like-for-like trending across reorgs | T0 |

Catalog tags: category `analytics`, purpose `workforce-analytics`, lawful basis `legitimate-interest`, retention `analytics-3y`.

## 3. Rules & Configuration Surface

- `config/metrics.yaml` — the semantic layer locally: each metric carries definition, formula id, grain, owner, `include_contingent` toggle (register row), change log. Code evaluates only formulas the registry names; ad-hoc metric definitions are impossible.
- Suppression threshold (n=5) and complementary-suppression behavior are constants of `suppression.py` — deliberately NOT configurable (privacy floor, not a preference).

## 4. AI Touchpoints

None locally (ANLT-4 deferred). When attrition scoring arrives it must enter via the 14-AI governance registry, aggregate-first, never a bare individual score to a direct manager (spec §6) — recorded here so the deferral is visible.

## 5. Edge-Case Test Plan (register §8)

| Register row | Test |
|---|---|
| Retro transactions rewriting history (facts restate; certified snapshots immutable + annotated) | `test_ANLT_retro_restates_facts_snapshots_immutable` |
| Org reorg breaking trend continuity (bridge tables) | `test_ANLT_reorg_bridge_like_for_like_trend` |
| n<5 suppression vs drill-down (complementary suppression) | `test_ANLT_complementary_suppression_no_subtraction` |
| Contractor inclusion toggles per metric | `test_ANLT_contractor_inclusion_toggle` |

## 6. Key Decisions / Invariant Notes

- **No competing definitions:** metric math lives only in `semantic.py`, keyed by the registry. Headcount is defined once (point-in-time on SCD2 validity), FTE-weighted is a declared variant, not a re-implementation.
- **Snapshots restate by versioning** — `restate_snapshot` writes a new row with `restatement_of` + annotation; the DB-level immutability guard makes UPDATE/DELETE on certified rows impossible (payroll-grade pattern reused).
- Report security is the central policy engine (Invariant #3); the BI "passthrough auth" requirement becomes: the same `decide` + `serialize_filtered` filter the report path, proven by the cross-surface test.
- Dimension build reads source modules through their service functions (Invariant #2); CDC replaces this when the event layer lands (Invariant #7 deferral, recorded in memory).

## 7. Open Items

- BI standard (Tableau vs Power BI), Finance plan integration depth, eNPS integrate-vs-native (spec §9) — product decisions, none gating the local backend.

## Change Log

- **2026-06-11** — Initial design. Trigger: Module 11 kickoff (auto-approved cadence).
- **2026-06-11** — Review fix: `orgmap.map_path` and the semantic-layer org filter match org-path prefixes on '/' boundaries via `platform_core.orgpath` ('/corp/eng' no longer matches '/corp/engineering').
