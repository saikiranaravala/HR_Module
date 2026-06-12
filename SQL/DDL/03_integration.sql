-- SQL/DDL/03_integration.sql - connector_run/credential, provisioning_action (Specs/13)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: integration; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS integration;

--
-- Name: connector_credential; Type: TABLE; Schema: integration; Owner: -
--

CREATE TABLE integration.connector_credential (
    credential_id uuid NOT NULL,
    connector_key text NOT NULL,
    credential_kind text NOT NULL,
    reference text NOT NULL,
    expires_on date NOT NULL
);

--
-- Name: connector_run; Type: TABLE; Schema: integration; Owner: -
--

CREATE TABLE integration.connector_run (
    run_id uuid NOT NULL,
    connector_key text NOT NULL,
    started_at timestamp with time zone NOT NULL,
    finished_at timestamp with time zone,
    status text NOT NULL,
    record_count integer NOT NULL,
    error_normalized text,
    correlation_id uuid NOT NULL
);

--
-- Name: provisioning_action; Type: TABLE; Schema: integration; Owner: -
--

CREATE TABLE integration.provisioning_action (
    action_id uuid NOT NULL,
    worker_id text NOT NULL,
    action_type text NOT NULL,
    effective_ts timestamp with time zone NOT NULL,
    attributes jsonb,
    status text NOT NULL,
    alert_raised boolean NOT NULL,
    applied_at timestamp with time zone
);

--
-- Name: connector_credential connector_credential_pkey; Type: CONSTRAINT; Schema: integration; Owner: -
--

ALTER TABLE ONLY integration.connector_credential
    ADD CONSTRAINT connector_credential_pkey PRIMARY KEY (credential_id);

--
-- Name: connector_run connector_run_pkey; Type: CONSTRAINT; Schema: integration; Owner: -
--

ALTER TABLE ONLY integration.connector_run
    ADD CONSTRAINT connector_run_pkey PRIMARY KEY (run_id);

--
-- Name: provisioning_action provisioning_action_pkey; Type: CONSTRAINT; Schema: integration; Owner: -
--

ALTER TABLE ONLY integration.provisioning_action
    ADD CONSTRAINT provisioning_action_pkey PRIMARY KEY (action_id);

--
--
