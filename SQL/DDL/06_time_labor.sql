-- SQL/DDL/06_time_labor.sql - time_entry, time_result, accrual_lot (Specs/02)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: time_labor; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS time_labor;

--
-- Name: accrual_lot; Type: TABLE; Schema: time_labor; Owner: -
--

CREATE TABLE time_labor.accrual_lot (
    lot_id uuid NOT NULL,
    worker_id uuid NOT NULL,
    absence_type text NOT NULL,
    granted_on date NOT NULL,
    hours_granted numeric(7,2) NOT NULL,
    hours_consumed numeric(7,2) NOT NULL,
    expires_on date
);

--
-- Name: time_entry; Type: TABLE; Schema: time_labor; Owner: -
--

CREATE TABLE time_labor.time_entry (
    entry_id uuid NOT NULL,
    worker_id uuid NOT NULL,
    person_id uuid NOT NULL,
    in_utc timestamp with time zone NOT NULL,
    out_utc timestamp with time zone NOT NULL,
    timezone_name text NOT NULL,
    work_date date NOT NULL,
    pay_group text NOT NULL,
    country text NOT NULL,
    state text
);

--
-- Name: time_result; Type: TABLE; Schema: time_labor; Owner: -
--

CREATE TABLE time_labor.time_result (
    result_id uuid NOT NULL,
    worker_id uuid NOT NULL,
    period_key text NOT NULL,
    pay_group text NOT NULL,
    earnings_code text NOT NULL,
    hours numeric(7,2) NOT NULL,
    rate numeric(12,4) NOT NULL,
    is_retro_delta boolean NOT NULL,
    origin_result_id uuid,
    explanation text NOT NULL,
    locked boolean NOT NULL
);

--
-- Name: accrual_lot accrual_lot_pkey; Type: CONSTRAINT; Schema: time_labor; Owner: -
--

ALTER TABLE ONLY time_labor.accrual_lot
    ADD CONSTRAINT accrual_lot_pkey PRIMARY KEY (lot_id);

--
-- Name: time_entry time_entry_pkey; Type: CONSTRAINT; Schema: time_labor; Owner: -
--

ALTER TABLE ONLY time_labor.time_entry
    ADD CONSTRAINT time_entry_pkey PRIMARY KEY (entry_id);

--
-- Name: time_result time_result_pkey; Type: CONSTRAINT; Schema: time_labor; Owner: -
--

ALTER TABLE ONLY time_labor.time_result
    ADD CONSTRAINT time_result_pkey PRIMARY KEY (result_id);

--
--
