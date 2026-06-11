---
name: temporal-schema
description: Generate effective-dated PostgreSQL DDL following Meridian's temporal data pattern (EFFDT/EFFSEQ, audit columns, catalog tags, sensitivity tiers). Use whenever creating or altering tables for person/job/comp/org or any history-bearing entity.
---

# Temporal Schema Generator

Meridian's most important consistency layer is the shared temporal pattern (Architecture Invariant #1). Every history-bearing entity follows it exactly — never a "current state only" table for person/job/comp/org domains.

## Required shape for an effective-dated table

```sql
CREATE TABLE <ctx>.<entity> (
    <entity>_id        UUID        NOT NULL,           -- stable identity, never changes
    effective_date     DATE        NOT NULL,
    effective_sequence SMALLINT    NOT NULL DEFAULT 0, -- multiple same-day changes
    action_code        TEXT        NOT NULL,           -- e.g., HIR, XFR, PAY
    action_reason      TEXT,
    -- domain columns ...
    -- audit (mandatory on every table)
    created_by         TEXT        NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_channel     TEXT        NOT NULL,           -- ui | api | integration | migration | agent
    correlation_id     UUID        NOT NULL,
    PRIMARY KEY (<entity>_id, effective_date, effective_sequence)
);
```

## Rules

1. **Rows are immutable.** A correction is a new row with a higher `effective_sequence`; a retroactive change is a new row with a past `effective_date` **plus a retro event** — never an UPDATE that silently rewrites history.
2. **Catalog tags as comments** on every column: category, purpose, lawful basis, retention class. Example:
   `COMMENT ON COLUMN core.person.birth_date IS 'category=personal; purpose=employment-admin; lawful_basis=contract; retention=emp+7y; tier=T1';`
3. **Sensitivity tiers** drive storage: T2 (comp, national ID, banking) and T3 (health-adjacent, ER cases, succession) fields use field-level envelope encryption — store ciphertext + key reference, never plaintext.
4. **As-of querying** must be possible with a standard predicate; provide a view or function per entity:
   `effective_date <= :as_of` → take max `(effective_date, effective_sequence)` per id.
5. **Schema ownership:** the table lives in its bounded context's schema only. No foreign keys across context schemas — cross-context references are by ID + event-built read models.
6. **Every DDL change ships with temporal conformance tests:** as-of query correctness, same-day sequence ordering, retro-row insertion emits retro event, audit columns populated on every path.

## Anti-patterns (reject on sight)

- `UPDATE ... SET <domain column>` on a temporal table (history mutation).
- `valid_to` / `end_date` maintained by trigger as the only history mechanism.
- Nullable `created_by`/`correlation_id` ("we'll backfill audit later").
- A `country` column used by code branches instead of country-pack config.
