-- SQL/DDL/16_migration.sql - staged_record (idempotency unique), dq_exception, gate_artifact (immutable), sync_conflict (Specs/16)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: migration; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS migration;

--
-- Name: dq_exception; Type: TABLE; Schema: migration; Owner: -
--

CREATE TABLE migration.dq_exception (
    exception_id uuid NOT NULL,
    batch_id text NOT NULL,
    domain text NOT NULL,
    rule text NOT NULL,
    source_ref text NOT NULL,
    guidance text NOT NULL,
    status text NOT NULL
);

--
-- Name: gate_artifact; Type: TABLE; Schema: migration; Owner: -
--

CREATE TABLE migration.gate_artifact (
    artifact_id uuid NOT NULL,
    wave text NOT NULL,
    gate text NOT NULL,
    passed boolean NOT NULL,
    report jsonb NOT NULL,
    content_hash text NOT NULL,
    signed_by text NOT NULL,
    signed_at timestamp with time zone NOT NULL
);

--
-- Name: staged_record; Type: TABLE; Schema: migration; Owner: -
--

CREATE TABLE migration.staged_record (
    staged_id uuid NOT NULL,
    batch_id text NOT NULL,
    source_key text NOT NULL,
    domain text NOT NULL,
    payload jsonb NOT NULL,
    loaded boolean NOT NULL
);

--
-- Name: sync_conflict; Type: TABLE; Schema: migration; Owner: -
--

CREATE TABLE migration.sync_conflict (
    conflict_id uuid NOT NULL,
    worker_ref text NOT NULL,
    field text NOT NULL,
    ps_value text,
    meridian_value text,
    detected_at timestamp with time zone NOT NULL,
    sla_due_at timestamp with time zone NOT NULL,
    status text NOT NULL,
    resolution text
);

--
-- Name: dq_exception dq_exception_pkey; Type: CONSTRAINT; Schema: migration; Owner: -
--

ALTER TABLE ONLY migration.dq_exception
    ADD CONSTRAINT dq_exception_pkey PRIMARY KEY (exception_id);

--
-- Name: gate_artifact gate_artifact_pkey; Type: CONSTRAINT; Schema: migration; Owner: -
--

ALTER TABLE ONLY migration.gate_artifact
    ADD CONSTRAINT gate_artifact_pkey PRIMARY KEY (artifact_id);

--
-- Name: staged_record staged_record_pkey; Type: CONSTRAINT; Schema: migration; Owner: -
--

ALTER TABLE ONLY migration.staged_record
    ADD CONSTRAINT staged_record_pkey PRIMARY KEY (staged_id);

--
-- Name: sync_conflict sync_conflict_pkey; Type: CONSTRAINT; Schema: migration; Owner: -
--

ALTER TABLE ONLY migration.sync_conflict
    ADD CONSTRAINT sync_conflict_pkey PRIMARY KEY (conflict_id);

--
-- Name: staged_record uq_staged_idempotency; Type: CONSTRAINT; Schema: migration; Owner: -
--

ALTER TABLE ONLY migration.staged_record
    ADD CONSTRAINT uq_staged_idempotency UNIQUE (batch_id, domain, source_key);

--
-- Name: gate_artifact immutable_migration_gate_artifact; Type: TRIGGER; Schema: migration; Owner: -
--

CREATE TRIGGER immutable_migration_gate_artifact BEFORE DELETE OR UPDATE ON migration.gate_artifact FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();

--
--
