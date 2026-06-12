-- SQL/DDL/10_analytics.sql - dim_worker (SCD2), certified_snapshot (immutable), org_bridge (Specs/11)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: analytics; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS analytics;

--
-- Name: certified_snapshot; Type: TABLE; Schema: analytics; Owner: -
--

CREATE TABLE analytics.certified_snapshot (
    snapshot_id uuid NOT NULL,
    as_of date NOT NULL,
    metric text NOT NULL,
    value numeric(18,4) NOT NULL,
    version integer NOT NULL,
    restatement_of uuid,
    annotation text
);

--
-- Name: dim_worker; Type: TABLE; Schema: analytics; Owner: -
--

CREATE TABLE analytics.dim_worker (
    row_id uuid NOT NULL,
    worker_key text NOT NULL,
    valid_from date NOT NULL,
    valid_to date NOT NULL,
    org_path text NOT NULL,
    country text NOT NULL,
    worker_type text NOT NULL,
    fte numeric(4,2) NOT NULL,
    exited boolean NOT NULL,
    regrettable_exit boolean NOT NULL
);

--
-- Name: org_bridge; Type: TABLE; Schema: analytics; Owner: -
--

CREATE TABLE analytics.org_bridge (
    bridge_id uuid NOT NULL,
    old_org_path text NOT NULL,
    new_org_path text NOT NULL,
    effective_date date NOT NULL
);

--
-- Name: certified_snapshot certified_snapshot_pkey; Type: CONSTRAINT; Schema: analytics; Owner: -
--

ALTER TABLE ONLY analytics.certified_snapshot
    ADD CONSTRAINT certified_snapshot_pkey PRIMARY KEY (snapshot_id);

--
-- Name: dim_worker dim_worker_pkey; Type: CONSTRAINT; Schema: analytics; Owner: -
--

ALTER TABLE ONLY analytics.dim_worker
    ADD CONSTRAINT dim_worker_pkey PRIMARY KEY (row_id);

--
-- Name: org_bridge org_bridge_pkey; Type: CONSTRAINT; Schema: analytics; Owner: -
--

ALTER TABLE ONLY analytics.org_bridge
    ADD CONSTRAINT org_bridge_pkey PRIMARY KEY (bridge_id);

--
-- Name: certified_snapshot immutable_analytics_certified_snapshot; Type: TRIGGER; Schema: analytics; Owner: -
--

CREATE TRIGGER immutable_analytics_certified_snapshot BEFORE DELETE OR UPDATE ON analytics.certified_snapshot FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();

--
--
