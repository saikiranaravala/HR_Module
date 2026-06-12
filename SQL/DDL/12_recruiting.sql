-- SQL/DDL/12_recruiting.sql - candidate_profile, requisition, application, offer (Specs/06)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: recruiting; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS recruiting;

--
-- Name: application; Type: TABLE; Schema: recruiting; Owner: -
--

CREATE TABLE recruiting.application (
    application_id uuid NOT NULL,
    candidate_id uuid NOT NULL,
    requisition_id uuid NOT NULL,
    stage text NOT NULL,
    status text NOT NULL,
    disposition_code text,
    internal boolean NOT NULL,
    confidential boolean NOT NULL,
    ai_rank integer,
    ai_explanation text,
    applied_on date NOT NULL
);

--
-- Name: candidate_profile; Type: TABLE; Schema: recruiting; Owner: -
--

CREATE TABLE recruiting.candidate_profile (
    candidate_id uuid NOT NULL,
    full_name text,
    email text,
    country text NOT NULL,
    internal_worker_id text,
    do_not_rehire boolean NOT NULL,
    consent_captured_on date,
    erased boolean NOT NULL
);

--
-- Name: offer; Type: TABLE; Schema: recruiting; Owner: -
--

CREATE TABLE recruiting.offer (
    offer_id uuid NOT NULL,
    application_id uuid NOT NULL,
    version integer NOT NULL,
    supersedes uuid,
    base_annual numeric(12,2) NOT NULL,
    currency text NOT NULL,
    components jsonb,
    status text NOT NULL,
    start_date date,
    requires_comp_approval boolean NOT NULL,
    rescind_reason text,
    decided_at timestamp with time zone
);

--
-- Name: requisition; Type: TABLE; Schema: recruiting; Owner: -
--

CREATE TABLE recruiting.requisition (
    requisition_id uuid NOT NULL,
    position_id text NOT NULL,
    title text NOT NULL,
    grade text NOT NULL,
    country text NOT NULL,
    jurisdiction text,
    headcount_type text NOT NULL,
    status text NOT NULL,
    range_min numeric(12,2),
    range_max numeric(12,2),
    posting_text text
);

--
-- Name: application application_pkey; Type: CONSTRAINT; Schema: recruiting; Owner: -
--

ALTER TABLE ONLY recruiting.application
    ADD CONSTRAINT application_pkey PRIMARY KEY (application_id);

--
-- Name: candidate_profile candidate_profile_pkey; Type: CONSTRAINT; Schema: recruiting; Owner: -
--

ALTER TABLE ONLY recruiting.candidate_profile
    ADD CONSTRAINT candidate_profile_pkey PRIMARY KEY (candidate_id);

--
-- Name: offer offer_pkey; Type: CONSTRAINT; Schema: recruiting; Owner: -
--

ALTER TABLE ONLY recruiting.offer
    ADD CONSTRAINT offer_pkey PRIMARY KEY (offer_id);

--
-- Name: requisition requisition_pkey; Type: CONSTRAINT; Schema: recruiting; Owner: -
--

ALTER TABLE ONLY recruiting.requisition
    ADD CONSTRAINT requisition_pkey PRIMARY KEY (requisition_id);

--
--
