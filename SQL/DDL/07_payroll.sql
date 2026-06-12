-- SQL/DDL/07_payroll.sql - pay_cycle, pay_input_record, pay_result_record (Specs/03)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: payroll; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS payroll;

--
-- Name: pay_cycle; Type: TABLE; Schema: payroll; Owner: -
--

CREATE TABLE payroll.pay_cycle (
    cycle_id uuid NOT NULL,
    country text NOT NULL,
    pay_group text NOT NULL,
    period_key text NOT NULL,
    state text NOT NULL,
    off_cycle boolean NOT NULL,
    snapshot_hash text,
    compiled_by text,
    approved_by text,
    gross_total numeric(16,2),
    state_changed_at timestamp with time zone
);

--
-- Name: pay_input_record; Type: TABLE; Schema: payroll; Owner: -
--

CREATE TABLE payroll.pay_input_record (
    input_id uuid NOT NULL,
    cycle_id uuid NOT NULL,
    worker_id text NOT NULL,
    payload jsonb NOT NULL,
    held boolean NOT NULL,
    hold_reason text
);

--
-- Name: pay_result_record; Type: TABLE; Schema: payroll; Owner: -
--

CREATE TABLE payroll.pay_result_record (
    result_id uuid NOT NULL,
    cycle_id uuid NOT NULL,
    worker_id text NOT NULL,
    gross numeric(14,2) NOT NULL,
    total_deductions numeric(14,2) NOT NULL,
    net numeric(14,2) NOT NULL,
    elements jsonb
);

--
-- Name: pay_cycle pay_cycle_pkey; Type: CONSTRAINT; Schema: payroll; Owner: -
--

ALTER TABLE ONLY payroll.pay_cycle
    ADD CONSTRAINT pay_cycle_pkey PRIMARY KEY (cycle_id);

--
-- Name: pay_input_record pay_input_record_pkey; Type: CONSTRAINT; Schema: payroll; Owner: -
--

ALTER TABLE ONLY payroll.pay_input_record
    ADD CONSTRAINT pay_input_record_pkey PRIMARY KEY (input_id);

--
-- Name: pay_result_record pay_result_record_pkey; Type: CONSTRAINT; Schema: payroll; Owner: -
--

ALTER TABLE ONLY payroll.pay_result_record
    ADD CONSTRAINT pay_result_record_pkey PRIMARY KEY (result_id);

--
--
