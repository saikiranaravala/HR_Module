# Module 13 Design — Performance Management (Specs/07)

**Spec:** [Specs/07-performance.md](../Specs/07-performance.md) · **Package:** `src/performance/` · Tests: `src/test/performance/`
**Depends on:** platform_core (audit, policy), ai_layer (draft assist via gateway), rules_workflow (config patterns), core_hr (population), feeds 05-Comp / 09-Succession
**⚠ Gate:** ratings philosophy (master §13.4) is OPEN. Isolation: rating scales live in `config/templates.yaml` per template; `rating` is nullable everywhere and **ratingless mode** (narrative + calibration grid only) is a template flag. Comp already consumes ratings as opaque strings (05 design), so either philosophy lands as config.

## 1. Scope & Requirement Trace

| Req | Design element | Local scope |
|---|---|---|
| PERF-1 (P1) | `goals.py`: Goal with alignment parent (cascade), weights, visibility; **mid-cycle revision = version chain, original preserved**; orphan-goal report; transfer policy (travel-with-worker vs re-baseline) | **Yes** (alignment-map viz = UI; Jira/CRM connectors = P2 adapters) |
| PERF-2 (P1) | `cycles.py` + `reviews.py`: template config (sections, anchored scales, **ratingless flag**, participant matrix incl. matrix-manager weights), launch with population snapshot + eligibility (<90-day tenure auto-excluded, pro-rated flag), self/manager assessment, **calibration with mandatory rationale + immutable pre/post adjustment records**, release/acknowledge with dispute link, amendment workflow (dual record) | **Yes** (probationary/PIP auto-instantiation = Core-action slice later; PIP tier-restriction noted) |
| PERF-3 (P1) | `feedback.py`: check-ins (shared agenda vs private notes), feedback with **explicit per-item visibility** (no silent manager-visible), 360 aggregation with **anonymity threshold (no theme < 3 raters)** | **Yes** (campaign UX, external-rater email = UI/adapter) |
| PERF-4 (P2) | `reviews.ai_draft`: labeled draft via gateway use case `review-draft-assist` (added to 14's governance registry), **edit-required-before-submit enforced**; deterministic bias-language lint (`config/bias_lint.yaml`) | **Yes** |
| §5 hard rule | **AI never assigns or recommends a rating**: drafts populate narrative only (no rating parameter exists); rating fields are human-set; tested | **Yes** |

## 2. Data Model (schema `performance`)

| Table | Notes | Tier |
|---|---|---|
| `goal` | version chain (`supersedes`), parent alignment, visibility | T1 |
| `review_cycle` | template key, status, windows | T1 |
| `review_doc` | state machine: draft → self-done → manager-done → calibrated → released → acknowledged (+ `amended`, `closed-out`); nullable `rating`; `ai_drafted`/`ai_draft_edited`; `extension_until`; `amends` link (dual record); skip-level disagreement fields | T1; PIP docs **T3** (read-audited) — flag `restricted` |
| `calibration_adjustment` | before/after, **mandatory rationale**, actor — append-only audit lineage | T1 |
| `checkin` | shared notes vs `private_notes` (author-only) | T1 |
| `feedback` | explicit `visibility` to-subject\|to-manager; 360 `campaign_id`, `competency` | T1 |

Catalog tags: category `performance`, purpose `performance-management`, lawful basis `legitimate-interest`, retention `perf-per-country` (released docs excluded from GDPR erasure during retention — legal basis recorded; litigation-hold freeze honored via ess_mss access grants).

## 3. Rules & Configuration Surface

- `config/templates.yaml` — review templates: sections, scale (n-point with anchors) **or `ratingless: true`**, participant matrix with matrix-manager weights (must sum to 100 — conflict register row), eligibility (min tenure days), leave auto-extension days per leave type.
- `config/bias_lint.yaml` — gendered/age-coded/personality-vs-behavior term lists (deterministic lint, not AI).
- Forced distribution: guideline-only (spec recommendation) — calibration shows distribution, never hard-enforces.

## 4. AI Touchpoints

- `review-draft-assist` (new registry entry, risk `limited`, human role `author-must-edit`): drafts self/manager narratives from goals + check-in history; output labeled, `ai_draft_edited` must flip true before submit (policy option ON locally). **No rating input or output path exists.** Check-in summarizer reuses the same use case with citations.
- Rating-pattern analytics (leniency drift) = aggregate HR views only — deferred with analytics P2; never auto-adjusts.

## 5. Edge-Case Test Plan (register §8)

| Register row | Test |
|---|---|
| Manager change mid-cycle (outgoing drafts → incoming finalizes, both logged) | `test_PERF_manager_change_midcycle_handoff` |
| Worker on leave during window (auto-extension per leave type) | `test_PERF_leave_auto_extension` |
| Rating released, factual error found (amendment, dual record) | `test_PERF_released_amendment_dual_record` |
| Skip-level disagreement protocol | `test_PERF_skip_level_disagreement_recorded` |
| Matrix-manager weighting conflicts | `test_PERF_matrix_weight_conflict_rejected` |
| Terminated before release (close-out policy) | `test_PERF_terminated_before_release_closeout` |

## 6. Key Decisions / Invariant Notes

- **Amendment = dual record:** released docs are never edited; an amendment creates a new doc with `amends` → original; both remain readable, release history intact.
- Calibration adjustments are separate append-only rows (pre/post + rationale + actor) — the 100%-audited rating-lineage metric falls out of the schema.
- Goal revision preserves the original via version chain (no in-place edits of history).
- AI governance (Invariant #6): draft path has no rating surface; tests pin it. Bias lint is deterministic config.
- Check-in `private_notes` never serialize to the other party (explicit accessor).

## 7. Open Items

- Ratings philosophy gate (isolated, above); forced-distribution stance (guideline-only implemented); probationary/PIP auto-instantiation arrives with the Core-action integration slice.

## Change Log

- **2026-06-11** — Initial design. Trigger: Module 07 kickoff (auto-approved cadence).
