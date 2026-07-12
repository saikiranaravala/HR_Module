# Training 05 — Technical Consultant / Developer

**Audience:** engineers building or extending Meridian modules. **Duration:** 5 days. **Prerequisites:** Python 3.11+, SQLAlchemy or equivalent ORM, SQL, REST. Read `CLAUDE.md` and `TechDesignDoc/15-foundation-design.md` before day 1.

## Learning Objectives

Set up the dev environment; internalize the eight architecture invariants; build against the shared kernel (temporal, policy, audit, catalog); create a schema slice with matching model + migration; pass the temporal conformance suite; implement a module's edge-case register as named tests; follow the module workflow (design doc → slice → tests → progress log).

---

## Day 1 — Environment & Architecture Orientation

### 1.1 Setup (follow [Deploy-local.md](../Deploy-local.md) §1–8)

Checkpoint: `.\.venv\Scripts\python.exe -m pytest` → **237 passed**; `npm run build` in `UI/` green; API serving at `/docs`.

### 1.2 Repository mental model

- `Specs/` — immutable PRDs; requirement IDs (CORE-3, PAY-5…) are defined in the master, expanded in domain PRDs. **Every unit of work cites one.**
- `TechDesignDoc/` — one design doc per module, kept in sync with code (change log inside each doc).
- `src/platform_core/` — the shared kernel (below). `src/<module>/` — thin domain packages: `models.py` + service modules + `config/`.
- `src/test/<module>/` — mirrors the package; `conftest.py` per module rebuilds its schemas from `Base.metadata` in `meridian_test` (tests do **not** run Alembic).
- `migrations/versions/` — single Alembic chain (`0001`…), roughly one revision per module.
- `Progress.md` — authoritative status; update after every unit of work.

### 1.3 The shared kernel — read these files today

| File | Provides | Trap it prevents |
|---|---|---|
| `temporal.py` | `TemporalMixin` (EFFDT/EFFSEQ PK, action/reason, audit cols), temporal writer, `install_immutability_guard` | "Current-state-only" tables; silent history edits |
| `policy/engine.py` | `PolicyEngine.decide(subject, capability, resource)`, tiers T0–T3, `serialize_filtered`, fail-closed | Local access checks; permissive error paths |
| `audit.py` | Hash-chained audit events; `verify_chain` | Tamper-evident logging done ad hoc (canonicalize timestamps to UTC before hashing) |
| `catalog.py` | Privacy tags (category/purpose/lawful-basis/retention/tier) attached at column `info=` | Untagged PII columns |
| `crypto.py` | Envelope encryption for national IDs / bank details | Plaintext T2 identifiers |
| `conformance.py` | `TemporalConformanceSuite` — inherited test class for any temporal entity | Re-inventing temporal tests |
| `orgpath.py` | `within(path, subtree)` | `startswith` bug: `/corp/eng` matching `/corp/engineering` |
| `dates.py` | `add_months` (calendar-true) | `months * 30` drift on statutory windows |
| `db.py`, `base.py` | Engine/session factories, `.env` loading, shared declarative `Base` | Parallel metadata/config schemes |

## Day 2 — The Eight Invariants, as Engineering Practice

1. **Temporal data is sacred** — person/job/comp/org entities use `TemporalMixin`; reads accept `as_of`; retro changes emit retro events. Corrections are new rows (same date, seq+1).
2. **Bounded contexts own their schemas** — one PostgreSQL schema per context; **cross-context access only via the other module's service functions**, never SQL joins across schemas (locally a discipline; in prod, a hard boundary).
3. **One policy decision point** — every read/write authorization calls `PolicyEngine.decide`. T2/T3 reads are audit-logged by the engine. Never re-implement, never special-case.
4. **No vendor codes upstream of adapters** — provider formats live only in adapter modules (see `migration/extraction.py`: PS codes never leave it).
5. **Configuration-only extensibility** — variation goes in `config/` decision tables/workflows. No scripting hooks. No `if country == 'DE'` — that's a country pack.
6. **AI is governed** — model calls only via `ai_layer.gateway`; use cases registered in `use_cases.yaml`; agents inherit the calling user's scope; AI never rates/never rejects.
7. **Events are contracts** — *currently deferred locally* (direct service calls); when the event layer lands: CloudEvents, schema-registry, PII-minimized payloads, idempotent consumers.
8. **Privacy by construction** — every new column gets catalog tags at schema time; T2 identifiers use envelope encryption; synthetic data only below prod.

**Exercise 2.1** — Code-review drill: six seeded diffs (a cross-schema join, a local role check, a `startswith` org test, a `months*30` window, an inline prompt, an untagged PII column). Find and name the violated invariant for each.

## Day 3 — Build a Slice (guided lab)

Lab: add a `sabbatical_request` entity to a scratch module, end to end.

1. **Model** — `TemporalMixin` + tagged columns on the shared `Base`, `__table_args__ = {"schema": ...}`.
2. **Migration** — next revision on the chain; **verify up/down/up**: `alembic upgrade head`, `downgrade -1`, `upgrade head`. Model and migration must agree exactly — tests build from metadata, dev DB from migrations; drift bites later.
3. **Immutability** — `install_immutability_guard` in the migration and in the test conftest.
4. **Service functions** — temporal writer for mutations; `as_of` on reads; policy check at every entry point; audit events for sensitive ops.
5. **Tests** — inherit `TemporalConformanceSuite` (as-of, sequence conflict, retro, immutability for free), then add domain tests. Run `pytest src/test/<module>`.
6. **API (if exposed)** — FastAPI per conventions: `/v1`, RFC7807 `problem()`, `X-Correlation-Id` middleware (see `platform_core/api.py` as the template), cursor pagination, idempotency keys on mutations.

## Day 4 — Testing Requirements & Quality Gates

A PR is incomplete without:

- **Temporal conformance** for any effective-dated entity (the suite, not hand-rolled).
- **Edge-case register as named tests** — each PRD's penultimate section is mandatory; names follow `test_<DOMAIN>_<scenario>` (e.g., `test_PAY_negative_net_arrears`, `test_SUCC_incumbent_never_sees_own_slate`). A module is Done only when its register passes.
- **Decision-table tests + golden regression** for any rules/workflow change.
- **Cross-surface security consistency** — anything denied in the UI must be denied identically via API/report/AI (see `test_policy.py` for the pattern).
- **Payroll-path extras** — reconciliation identity (original + retro delta = recalculated) and snapshot immutability tests.

Also: PR descriptions and commit messages cite requirement IDs; design-doc change log updated when implementation deviates (`update-design-doc` skill); `Progress.md` entry appended (`update-progress` skill).

**War stories to learn from (all real, all fixed):** the org-path `startswith` boundary bug; `months*30` drift on biennial anniversaries; role-queue items missing from inboxes; Windows timer resolution making same-timestamp ordering non-deterministic (fixed with a DB `Identity` sequence — order by a monotonic column, never by wall-clock alone).

## Day 5 — Module Workflow & Local Deviations

- **One module at a time**, in build order; check `Progress.md` first. Flow: `design-module` skill → design doc → implement in slices → edge-case tests green → `update-progress`.
- **Local deviations (deliberate, documented):** no Kafka/Redis/OpenSearch locally — events deferred, direct service calls; one PostgreSQL instance stands in for DB-per-service; cloud concerns (EKS, DR, SIEM) are N/A-local in design docs, never silently dropped. Do not "helpfully" add infrastructure.
- **Migrations that touch history** need retro events and reconciliation evidence — never a data-fix script that mutates temporal rows.
- **SQL/DDL** is a pg_dump artifact of the migration chain; regenerate (`SQL/DDL/_generate.py`) after adding a migration.

---

## Competency Checklist (sign-off)

- [ ] Local stack green: 237 tests, UI build, API up
- [ ] Recites all eight invariants with one engineering consequence each
- [ ] Completes the Day-3 slice: model + migration (up/down/up) + guard + service + conformance suite green
- [ ] Names the four mandatory test categories and the payroll extras
- [ ] Correctly identifies all six violations in the code-review drill
- [ ] Ships one real change end-to-end: requirement ID cited, tests named per register, design doc + Progress.md updated
