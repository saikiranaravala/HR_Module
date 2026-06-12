-- SQL/DDL/01_platform.sql - audit_event (hash-chained, immutable), policy_decision_log, forbid_mutation()
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: platform; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS platform;

--
-- Name: forbid_mutation(); Type: FUNCTION; Schema: platform; Owner: -
--

CREATE FUNCTION platform.forbid_mutation() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            RAISE EXCEPTION 'rows in %.% are immutable (temporal/audit pattern): % denied',
                TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP;
        END;
        $$;

--
-- Name: audit_event; Type: TABLE; Schema: platform; Owner: -
--

CREATE TABLE platform.audit_event (
    audit_id uuid NOT NULL,
    seq bigint NOT NULL,
    occurred_at timestamp with time zone NOT NULL,
    actor text NOT NULL,
    on_behalf_of text,
    actor_type text NOT NULL,
    action text NOT NULL,
    entity_ref text NOT NULL,
    before jsonb,
    after jsonb,
    sensitivity_tier text NOT NULL,
    source_channel text NOT NULL,
    correlation_id uuid NOT NULL,
    prev_hash text NOT NULL,
    row_hash text NOT NULL
);

--
-- Name: policy_decision_log; Type: TABLE; Schema: platform; Owner: -
--

CREATE TABLE platform.policy_decision_log (
    decision_id uuid NOT NULL,
    decided_at timestamp with time zone NOT NULL,
    subject_id text NOT NULL,
    capability text NOT NULL,
    resource_ref text,
    allow boolean NOT NULL,
    reasons text NOT NULL,
    policy_version text NOT NULL,
    correlation_id uuid NOT NULL
);

--
-- Name: audit_event audit_event_pkey; Type: CONSTRAINT; Schema: platform; Owner: -
--

ALTER TABLE ONLY platform.audit_event
    ADD CONSTRAINT audit_event_pkey PRIMARY KEY (audit_id);

--
-- Name: audit_event audit_event_seq_key; Type: CONSTRAINT; Schema: platform; Owner: -
--

ALTER TABLE ONLY platform.audit_event
    ADD CONSTRAINT audit_event_seq_key UNIQUE (seq);

--
-- Name: policy_decision_log policy_decision_log_pkey; Type: CONSTRAINT; Schema: platform; Owner: -
--

ALTER TABLE ONLY platform.policy_decision_log
    ADD CONSTRAINT policy_decision_log_pkey PRIMARY KEY (decision_id);

--
-- Name: ix_audit_event_entity_ref; Type: INDEX; Schema: platform; Owner: -
--

CREATE INDEX ix_audit_event_entity_ref ON platform.audit_event USING btree (entity_ref);

--
-- Name: audit_event immutable_platform_audit_event; Type: TRIGGER; Schema: platform; Owner: -
--

CREATE TRIGGER immutable_platform_audit_event BEFORE DELETE OR UPDATE ON platform.audit_event FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();

--
--
