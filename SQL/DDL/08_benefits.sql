-- SQL/DDL/08_benefits.sql - benefit_plan, benefit_rate, enrollment (Specs/04)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: benefits; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS benefits;

--
-- Name: benefit_plan; Type: TABLE; Schema: benefits; Owner: -
--

CREATE TABLE benefits.benefit_plan (
    plan_id uuid NOT NULL,
    plan_type text NOT NULL,
    name text NOT NULL,
    country text NOT NULL,
    requires_eoi_above_multiple integer,
    default_option text
);

--
-- Name: benefit_rate; Type: TABLE; Schema: benefits; Owner: -
--

CREATE TABLE benefits.benefit_rate (
    rate_id uuid NOT NULL,
    plan_id uuid NOT NULL,
    option text NOT NULL,
    age_min integer NOT NULL,
    age_max integer NOT NULL,
    effective_date date NOT NULL,
    annual_premium numeric(12,2) NOT NULL,
    employer_pct numeric(5,2) NOT NULL
);

--
-- Name: enrollment; Type: TABLE; Schema: benefits; Owner: -
--

CREATE TABLE benefits.enrollment (
    enrollment_id uuid NOT NULL,
    worker_id text NOT NULL,
    plan_id uuid NOT NULL,
    option text NOT NULL,
    status text NOT NULL,
    coverage_start date NOT NULL,
    coverage_end date,
    dependents jsonb,
    source text NOT NULL
);

--
-- Name: benefit_plan benefit_plan_pkey; Type: CONSTRAINT; Schema: benefits; Owner: -
--

ALTER TABLE ONLY benefits.benefit_plan
    ADD CONSTRAINT benefit_plan_pkey PRIMARY KEY (plan_id);

--
-- Name: benefit_rate benefit_rate_pkey; Type: CONSTRAINT; Schema: benefits; Owner: -
--

ALTER TABLE ONLY benefits.benefit_rate
    ADD CONSTRAINT benefit_rate_pkey PRIMARY KEY (rate_id);

--
-- Name: enrollment enrollment_pkey; Type: CONSTRAINT; Schema: benefits; Owner: -
--

ALTER TABLE ONLY benefits.enrollment
    ADD CONSTRAINT enrollment_pkey PRIMARY KEY (enrollment_id);

--
--
