# Module 12 Design — Recruiting & Onboarding (Specs/06)

**Spec:** [Specs/06-recruiting.md](../Specs/06-recruiting.md) · **Package:** `src/recruiting/` · Tests: `src/test/recruiting/`
**Depends on:** ai_layer (`resume-rank-explain` use case, already registered), platform_core (policy, audit), rules_workflow (approval matrix), ess_mss (ER-tier case escalation), comp (offer range validation), core_hr (hire handoff)
**⚠ Gate:** ATS build-vs-buy is OPEN (master §13.7; this PRD assumes build). Isolation: everything here is the **canonical core** (requisitions, applications, offers, the POST /hires contract, compliance data) that survives either outcome — if "buy" wins, the pipeline/candidate-experience surface becomes an adapter writing into these same contracts (Invariant #4 pattern).

## 1. Scope & Requirement Trace

| Req | Design element | Local scope |
|---|---|---|
| REC-1 (P1) | `requisitions.py`: create-from-position (inherits grade/range/budget), backfill-lighter approval, salary-range disclosure auto-injection per jurisdiction (`config/pay_transparency.yaml`), cancel flow with offers-out handling | **Yes** (job-board feeds/agency portal deferred — adapter layer) |
| REC-2 (P1) | `CandidateProfile` shared across reqs; GDPR: per-country retention clocks (`config/retention.yaml`), erasure-mid-pipeline (anonymize, keep lawful flow stats) | **Yes** (career-site UI = UI phase) |
| REC-3 (P1) | `pipeline.py`: configurable stage flows (`config/stage_flows.yaml`), deterministic knockout rules (objective only), mandatory OFCCP disposition taxonomy at rejection, **AI rank-and-explain via gateway — output is advisory ordering; no code path from rank to disposition** | **Yes** (interview kits/scheduling/assessment vendors deferred) |
| REC-4 (P1) | `offers.py`: comp validation against `comp.GradeRange` (out-of-range ⇒ comp-team approval), negotiation versioning, accept ⇒ **pre-hire payload (the POST /hires contract: zero re-keying)**, rescind + failure-to-start flows | **Yes** (e-sign = vendor adapter, deferred) |
| REC-5 (P2) | Recruiting analytics | Deferred (semantic-layer metrics exist in 11 when needed) |

## 2. Data Model (schema `recruiting`)

| Table | Notes | Tier |
|---|---|---|
| `candidate_profile` | shared identity across reqs; `do_not_rehire` flag (policy-gated visibility); erasure ⇒ anonymized in place | T1 (PII), `do_not_rehire` **T2** |
| `requisition` | position inheritance (grade/country/range), status open\|hold\|filled\|cancelled, headcount_type | T1 |
| `application` | per-req: stage, disposition_code (OFCCP), `internal` + data-wall fields, ai_rank/ai_explanation (advisory) | T1 |
| `offer` | version chain (negotiation history), components incl. clawback terms, status draft\|extended\|accepted\|rescinded\|declined | **T2** (comp content) |

Catalog tags: category `recruiting`, purpose `talent-acquisition`, lawful basis `consent` (candidate data) / `legitimate-interest` (req data), retention `recruiting-per-country` (clock-driven).

## 3. Rules & Configuration Surface

- `config/stage_flows.yaml` — stage sequences per req template.
- `config/knockout.yaml` — objective deterministic knockouts (work authorization, license). Never AI.
- `config/pay_transparency.yaml` — jurisdictions requiring salary disclosure in postings (CO/CA/NY/WA + EU directive).
- `config/retention.yaml` — per-country candidate retention clocks (EU 6-month default).

## 4. AI Touchpoints

- `resume-rank-explain` (already in the 14-AI governance registry, `risk_class: high-risk`, `ll144_audit: required`): rank-and-explain ONLY. The rank function returns ordering + cited evidence; **rejection is a separate human call requiring a disposition code** — there is no code path from AI output to a stage change (Invariant #6: never auto-reject). Bias-audit hook: stage pass-through capture per pipeline.

## 5. Edge-Case Test Plan (register §9)

| Register row | Test |
|---|---|
| Rehire with do-not-rehire flag (policy-gated visibility) | `test_REC_do_not_rehire_policy_gated` |
| Internal candidate rejected (sensitive handling + manager data wall) | `test_REC_internal_candidate_manager_data_wall` |
| Offer accepted then rescinded (counter-offer) | `test_REC_accepted_offer_rescind_flow` |
| Multi-req single candidate (shared profile, per-req dispositions) | `test_REC_multi_req_shared_profile` |
| Requisition cancelled with offers out | `test_REC_req_cancelled_with_offers_out` |
| Background adverse finding post-start (escalation runbook) | `test_REC_adverse_finding_post_start_escalation` |
| GDPR erasure mid-pipeline | `test_REC_gdpr_erasure_mid_pipeline` |

## 6. Key Decisions / Invariant Notes

- **Zero re-keying (REC-4):** `accept_offer` emits the complete pre-hire payload assembled from profile + req + offer; the Core HR hire flow consumes it as-is. Tested field-for-field.
- AI ranking writes `ai_rank`/`ai_explanation` columns only; `reject()` demands a human actor + OFCCP code, and refuses `actor="ai"` defensively.
- Adverse finding post-start escalates via `ess_mss.cases.open_case(topic="investigation")` → ER-segregated queue (T3) — reusing the one case system, no recruiting-local ER store.
- Erasure anonymizes the profile in place and nulls PII, keeping dispositions/stage history identity-free for OFCCP applicant-flow statistics (documented lawful-retention basis); accepted-offer candidates are refused erasure (contract basis) with the legal ground in the error.
- Do-not-rehire visibility uses central policy capability `candidate.read-dnr` (new roles `recruiter`, `recruiter-lead`) — no local access logic.

## 7. Open Items

- ATS build-vs-buy gate (above). CRM/talent-marketing P2. Background/assessment vendor adapters land in the 13-Integration adapter layer.

## Change Log

- **2026-06-11** — Initial design. Trigger: Module 06 kickoff (auto-approved cadence).
- **2026-06-11** — Review fix: candidate retention clocks use calendar months (`platform_core.dates.add_months`).
