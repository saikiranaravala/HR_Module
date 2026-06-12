-- SQL/DDL/05_core.sql - person, person_name*, national_id, work_eligibility, worker, assignment*, department, position (*temporal+immutable)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: core; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS core;

--
-- Name: assignment; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.assignment (
    worker_id uuid NOT NULL,
    effective_date date NOT NULL,
    effective_sequence smallint NOT NULL,
    action_code text NOT NULL,
    action_reason text,
    created_by text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    source_channel text NOT NULL,
    correlation_id uuid NOT NULL,
    worker_status text NOT NULL,
    job_code text NOT NULL,
    department_id uuid,
    position_id uuid,
    manager_worker_id uuid,
    location_country text NOT NULL,
    fte numeric(4,2) NOT NULL,
    pay_group text
);

--
-- Name: department; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.department (
    department_id uuid NOT NULL,
    name text NOT NULL,
    parent_id uuid,
    status text NOT NULL
);

--
-- Name: national_id; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.national_id (
    national_id_pk uuid NOT NULL,
    person_id uuid NOT NULL,
    id_type text NOT NULL,
    value_encrypted text NOT NULL,
    last_four text NOT NULL
);

--
-- Name: person; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.person (
    person_id uuid NOT NULL,
    date_of_birth date NOT NULL,
    primary_nationality text
);

--
-- Name: person_name; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.person_name (
    person_id uuid NOT NULL,
    effective_date date NOT NULL,
    effective_sequence smallint NOT NULL,
    action_code text NOT NULL,
    action_reason text,
    created_by text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    source_channel text NOT NULL,
    correlation_id uuid NOT NULL,
    given_name text NOT NULL,
    family_name text NOT NULL,
    formatted_name text NOT NULL,
    legal_doc_verified boolean NOT NULL
);

--
-- Name: position; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core."position" (
    position_id uuid NOT NULL,
    job_code text NOT NULL,
    department_id uuid NOT NULL,
    headcount_budget integer NOT NULL,
    status text NOT NULL
);

--
-- Name: work_eligibility; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.work_eligibility (
    eligibility_id uuid NOT NULL,
    person_id uuid NOT NULL,
    country text NOT NULL,
    document_type text NOT NULL,
    expiry_date date
);

--
-- Name: worker; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.worker (
    worker_id uuid NOT NULL,
    person_id uuid NOT NULL,
    legal_entity text NOT NULL,
    entity_country text NOT NULL,
    worker_type text NOT NULL,
    hire_date date NOT NULL,
    original_hire_date date NOT NULL,
    carried_flags text
);

--
-- Name: assignment assignment_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.assignment
    ADD CONSTRAINT assignment_pkey PRIMARY KEY (worker_id, effective_date, effective_sequence);

--
-- Name: department department_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.department
    ADD CONSTRAINT department_pkey PRIMARY KEY (department_id);

--
-- Name: national_id national_id_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.national_id
    ADD CONSTRAINT national_id_pkey PRIMARY KEY (national_id_pk);

--
-- Name: person_name person_name_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.person_name
    ADD CONSTRAINT person_name_pkey PRIMARY KEY (person_id, effective_date, effective_sequence);

--
-- Name: person person_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.person
    ADD CONSTRAINT person_pkey PRIMARY KEY (person_id);

--
-- Name: position position_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core."position"
    ADD CONSTRAINT position_pkey PRIMARY KEY (position_id);

--
-- Name: work_eligibility work_eligibility_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.work_eligibility
    ADD CONSTRAINT work_eligibility_pkey PRIMARY KEY (eligibility_id);

--
-- Name: worker worker_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.worker
    ADD CONSTRAINT worker_pkey PRIMARY KEY (worker_id);

--
-- Name: assignment immutable_core_assignment; Type: TRIGGER; Schema: core; Owner: -
--

CREATE TRIGGER immutable_core_assignment BEFORE DELETE OR UPDATE ON core.assignment FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();

--
-- Name: person_name immutable_core_person_name; Type: TRIGGER; Schema: core; Owner: -
--

CREATE TRIGGER immutable_core_person_name BEFORE DELETE OR UPDATE ON core.person_name FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();

--
--
