-- SQL/DDL/14_learning.sql - content_item, assignment, completion_record (immutable), certification (Specs/08)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: learning; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS learning;

--
-- Name: assignment; Type: TABLE; Schema: learning; Owner: -
--

CREATE TABLE learning.assignment (
    assignment_id uuid NOT NULL,
    worker_id text NOT NULL,
    requirement_key text NOT NULL,
    content_key text NOT NULL,
    content_version integer NOT NULL,
    status text NOT NULL,
    due_on date NOT NULL,
    paused_on date,
    pause_log jsonb,
    extension_note text,
    attempts integer NOT NULL,
    suspend_data text,
    suspend_checksum text,
    lightweight boolean NOT NULL
);

--
-- Name: certification; Type: TABLE; Schema: learning; Owner: -
--

CREATE TABLE learning.certification (
    certification_id uuid NOT NULL,
    worker_id text NOT NULL,
    cert_type text NOT NULL,
    issuer text NOT NULL,
    issued_on date NOT NULL,
    expires_on date,
    evidence_ref text,
    job_required boolean NOT NULL
);

--
-- Name: completion_record; Type: TABLE; Schema: learning; Owner: -
--

CREATE TABLE learning.completion_record (
    completion_id uuid NOT NULL,
    worker_id text NOT NULL,
    requirement_key text,
    content_key text NOT NULL,
    content_version integer NOT NULL,
    score integer,
    completed_at timestamp with time zone NOT NULL,
    source text NOT NULL,
    evidence_ref text,
    approved_by text
);

--
-- Name: content_item; Type: TABLE; Schema: learning; Owner: -
--

CREATE TABLE learning.content_item (
    content_id uuid NOT NULL,
    content_key text NOT NULL,
    title text NOT NULL,
    version integer NOT NULL,
    supersede_policy text NOT NULL,
    active boolean NOT NULL
);

--
-- Name: assignment assignment_pkey; Type: CONSTRAINT; Schema: learning; Owner: -
--

ALTER TABLE ONLY learning.assignment
    ADD CONSTRAINT assignment_pkey PRIMARY KEY (assignment_id);

--
-- Name: certification certification_pkey; Type: CONSTRAINT; Schema: learning; Owner: -
--

ALTER TABLE ONLY learning.certification
    ADD CONSTRAINT certification_pkey PRIMARY KEY (certification_id);

--
-- Name: completion_record completion_record_pkey; Type: CONSTRAINT; Schema: learning; Owner: -
--

ALTER TABLE ONLY learning.completion_record
    ADD CONSTRAINT completion_record_pkey PRIMARY KEY (completion_id);

--
-- Name: content_item content_item_pkey; Type: CONSTRAINT; Schema: learning; Owner: -
--

ALTER TABLE ONLY learning.content_item
    ADD CONSTRAINT content_item_pkey PRIMARY KEY (content_id);

--
-- Name: completion_record immutable_learning_completion_record; Type: TRIGGER; Schema: learning; Owner: -
--

CREATE TRIGGER immutable_learning_completion_record BEFORE DELETE OR UPDATE ON learning.completion_record FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();

--
--
