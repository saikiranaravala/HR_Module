-- SQL/DDL/04_ai.sql - ai_ledger - every gateway call (Specs/14)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: ai; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS ai;

--
-- Name: ai_ledger; Type: TABLE; Schema: ai; Owner: -
--

CREATE TABLE ai.ai_ledger (
    entry_id uuid NOT NULL,
    occurred_at timestamp with time zone NOT NULL,
    use_case text NOT NULL,
    subject_id text NOT NULL,
    purpose text NOT NULL,
    model text,
    prompt_version text,
    status text NOT NULL,
    refusal_reason text,
    request_chars integer NOT NULL,
    correlation_id uuid NOT NULL
);

--
-- Name: ai_ledger ai_ledger_pkey; Type: CONSTRAINT; Schema: ai; Owner: -
--

ALTER TABLE ONLY ai.ai_ledger
    ADD CONSTRAINT ai_ledger_pkey PRIMARY KEY (entry_id);

--
--
