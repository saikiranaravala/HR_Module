# Module 1 Design — Platform Foundation (Specs/15)

**Spec:** [Specs/15-technical-architecture.md](../Specs/15-technical-architecture.md) · **Status:** Design → In Progress
**Stack:** Python 3.11.9, FastAPI, SQLAlchemy 2.x, Alembic, pytest · PostgreSQL 17 (local, database `meridian`)
**Package:** `src/platform_core/` · Tests: `src/test/platform_core/`

## 1. Scope & Requirement Trace

| Req ID | Priority | Requirement (summary) | Design element | In local scope? |
|---|---|---|---|---|
| TECH-4 | P0 | Temporal data as first-class platform service | `platform_core.temporal` — declarative mixin, as-of helpers, correction/retro semantics, conformance suite | **Yes** |
| TECH-5 | P0 | Hybrid RBAC+ABAC, one policy decision point, sensitivity tiers | `platform_core.policy` — capability×scope evaluator, T0–T3 field filtering, YAML policy config, decision log | **Yes** |
| TECH-6 | P0 | Append-only hash-chained audit, T2/T3 read logging | `platform_core.audit` — audit table + chain verify + read-event API | **Yes** (WORM storage emulated by append-only constraints; real object-lock is cloud-deferred) |
| TECH-9 | P0 | Lawful-basis register, purpose limitation, DSAR groundwork | `platform_core.catalog` — field tags at model declaration; generated records-of-processing report | **Yes** (DSAR tooling itself deferred to a later module) |
| TECH-10 | P0 | Residency planes, routing-minimal global directory | Documented N/A-local; catalog carries `residency_class` tag so models are plane-ready | Partial |
| TECH-3 | P0 | PostgreSQL per service, Kafka, Redis, OpenSearch, lakehouse | PostgreSQL only; **events deferred** (memory.md), Redis/OpenSearch/lakehouse N/A-local | Partial |
| TECH-7 | P0 | Encryption, field-level envelope for IDs/banking | Interface stub `platform_core.crypto` (envelope-encrypt API with local key provider); KMS deferred | Partial |
| TECH-1/2/8/11 | — | EKS/GitOps, deployment topology, SOC2/pen-tests, retention engine | N/A-local / later module | No |

Out-of-scope items are *deferred*, not dropped — each appears in §7 below.

## 2. Bounded Context & Data Model

`platform_core` is infrastructure shared by every future context. It owns schema `platform` containing:

- **`platform.audit_event`** — append-only, hash-chained.
  Columns: `audit_id` (uuid pk), `seq` (bigint, monotonic per chain), `occurred_at`, `actor`, `on_behalf_of`, `actor_type` (`user|system|agent`), `action` (`insert|update-correction|insert-retro|read`), `entity_ref` (schema.table:id), `before` (jsonb), `after` (jsonb), `sensitivity_tier`, `source_channel`, `correlation_id`, `prev_hash`, `row_hash`.
  `row_hash = sha256(prev_hash || canonical_json(payload))`. UPDATE/DELETE revoked + trigger-blocked.
- **`platform.policy_decision_log`** — sampled decision records (subject, capability, resource scope, decision, policy version, correlation id).
- No business entities live here; temporal pattern ships as a **library** that other contexts' tables use.

### Temporal pattern (library contract)
Every effective-dated table gets, via `TemporalMixin`:
`effective_date date`, `effective_sequence smallint default 0`, `action_code text`, `action_reason text`, plus audit columns `created_by`, `created_at`, `source_channel`, `correlation_id`. PK = `(entity_id, effective_date, effective_sequence)`. Rows immutable (no ORM updates; DB trigger blocks UPDATE on domain columns). Semantics:
- **Correction** = new row, same `effective_date`, `effective_sequence + 1`.
- **Retro change** = new row with past `effective_date`; emits a retro record (locally: audit event with `action='insert-retro'`; later: CloudEvents retro event).
- **As-of read** = helper `as_of(session, Model, entity_id, date)` → row with max `(effective_date, effective_sequence)` where `effective_date <= date`.

### Catalog tags
Each mapped column declares `info={"catalog": FieldTag(category, purpose, lawful_basis, retention_class, tier, residency_class)}`. A startup check fails if any column on a registered model lacks tags — privacy by construction (Invariant #8).

## 3. APIs

FastAPI app `platform_core.api` (internal platform endpoints, `/v1`):
- `POST /v1/policy/decide` — {subject attrs, capability, resource attrs} → {decision, obligations (e.g., redact-tiers), policy_version}. RFC7807 errors, `X-Correlation-Id` propagation.
- `GET /v1/audit/verify` — walks a chain segment, returns first broken link if tampered.
- `GET /v1/catalog/records-of-processing` — generated from registered models (TECH-9 register derived from schemas).
Other modules call the policy engine **in-process** through `platform_core.policy.decide()` — same implementation the endpoint uses (one decision point, two transports).

## 4. Policy model (TECH-5)

- **Capabilities**: verbs per domain (`person.read`, `comp.read`, `audit.verify`, …) granted by **roles** (YAML: `config/policy/roles.yaml`).
- **Scopes (ABAC)**: org subtree, country, population; evaluated against resource attributes.
- **Sensitivity tiers**: T0–T3 per field from catalog tags. Decision returns `redact_tiers`; the serialization layer (`platform_core.policy.serialize_filtered()`) strips fields above the subject's clearance — the *same* filter used for API responses and report-style dict output (cross-surface consistency, testable).
- T2/T3 **read** decisions also write an audit read-event.
- Policy files carry a `version`; every decision logs it.

## 5. Edge-Case Test Plan (Specs/15 §9 register → named tests)

| Register row | Test | Status plan |
|---|---|---|
| Clock skew vs effective-timestamp ordering | `test_TECH_clock_skew_effective_ordering` (single time authority; monotonic seq under same-day inserts) | **passing** |
| Audit store capacity surge under read-logging | `test_TECH_audit_surge_bulk_read_logging` (bulk writes keep chain valid) | **passing** |
| Partial-service brownout: payroll never silently degrades | `test_TECH_policy_unavailable_fails_closed` (policy engine error ⇒ deny, never allow) | **passing** (local analogue) |
| Region failover during OE | N/A-local (cloud game day) | deferred |
| Kafka consumer-lag cascade | N/A-local (events deferred) | deferred |
| KMS key compromise rotation drill | N/A-local (crypto stub only) | deferred |

Cross-cutting (mandatory per `edge-case-tests` skill): as-of straddle, same-day double change ordering, retro insert emits retro record, audit columns populated, policy denial identical via API and serialization paths, hash-chain tamper detection, append-only enforcement.

## 6. Invariant Check

1 Temporal ✔ (the library *is* this invariant) · 2 Schema ownership ✔ (`platform` schema; others get their own) · 3 One policy point ✔ (§4) · 4 Adapters n/a here · 5 Config-only ✔ (policy as versioned YAML) · 6 AI governed n/a (no AI in this module) · 7 Events **deviation — deferred** (memory.md 2026-06-10) · 8 Privacy by construction ✔ (mandatory catalog tags).

## 7. Deferrals & Open Items

- Event emission (retro events as CloudEvents) — deferred with Invariant #7; local stand-in is the audit record.
- KMS-backed envelope encryption — `crypto` stub with local key provider; swap to KMS later (TECH-7).
- WORM object-lock, SIEM detections, DR drills, load model (25K concurrent) — cloud-phase.
- DSAR assembler/erasure orchestration — later privacy module slice (TECH-9 remainder).
- Open question from spec (Aurora vs self-managed PG at 250K scale) — irrelevant locally; benchmark deferred.

## Change Log

- **2026-06-10** — Implemented as designed; one addition: audit hash payload canonicalizes `occurred_at` to UTC (Postgres returns `timestamptz` in session timezone, which must not change the hash). Conformance suite ships as `platform_core.conformance.TemporalConformanceSuite` (pytest class, subclass-with-fixtures pattern). Alembic migration `0001_platform_foundation` (up/down/up verified). Test results: 25 passed, 0 failed. Trigger: Module 1 implementation. Requirement IDs: TECH-4/5/6/7/9.
- **2026-06-10** — Initial design. Trigger: Module 1 kickoff. Requirement IDs: TECH-3/4/5/6/7/9/10.
