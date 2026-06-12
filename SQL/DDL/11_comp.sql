-- SQL/DDL/11_comp.sql - grade_range*, comp_record* (temporal+immutable), comp_cycle, cycle_line (Specs/05)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: comp; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS comp;

--
-- Name: comp_cycle; Type: TABLE; Schema: comp; Owner: -
--

CREATE TABLE comp.comp_cycle (
    cycle_id uuid NOT NULL,
    name text NOT NULL,
    status text NOT NULL,
    corporate_currency text NOT NULL,
    fx_rates jsonb NOT NULL,
    budget_pool numeric(14,2) NOT NULL,
    opened_at timestamp with time zone NOT NULL
);

--
-- Name: comp_record; Type: TABLE; Schema: comp; Owner: -
--

CREATE TABLE comp.comp_record (
    comp_key uuid NOT NULL,
    effective_date date NOT NULL,
    effective_sequence smallint NOT NULL,
    action_code text NOT NULL,
    action_reason text,
    created_by text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    source_channel text NOT NULL,
    correlation_id uuid NOT NULL,
    worker_id text NOT NULL,
    record_role text NOT NULL,
    base_annual numeric(12,2) NOT NULL,
    currency text NOT NULL,
    grade text NOT NULL,
    country text NOT NULL,
    fte numeric(4,2) NOT NULL
);

--
-- Name: cycle_line; Type: TABLE; Schema: comp; Owner: -
--

CREATE TABLE comp.cycle_line (
    line_id uuid NOT NULL,
    cycle_id uuid NOT NULL,
    worker_id text NOT NULL,
    manager_id text NOT NULL,
    snapshot jsonb NOT NULL,
    merit_pct numeric(5,2),
    justification text,
    out_of_guideline boolean NOT NULL,
    status text NOT NULL
);

--
-- Name: grade_range; Type: TABLE; Schema: comp; Owner: -
--

CREATE TABLE comp.grade_range (
    range_key text NOT NULL,
    effective_date date NOT NULL,
    effective_sequence smallint NOT NULL,
    action_code text NOT NULL,
    action_reason text,
    created_by text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    source_channel text NOT NULL,
    correlation_id uuid NOT NULL,
    grade text NOT NULL,
    country text NOT NULL,
    currency text NOT NULL,
    range_min numeric(12,2) NOT NULL,
    range_mid numeric(12,2) NOT NULL,
    range_max numeric(12,2) NOT NULL
);

--
-- Name: comp_cycle comp_cycle_pkey; Type: CONSTRAINT; Schema: comp; Owner: -
--

ALTER TABLE ONLY comp.comp_cycle
    ADD CONSTRAINT comp_cycle_pkey PRIMARY KEY (cycle_id);

--
-- Name: comp_record comp_record_pkey; Type: CONSTRAINT; Schema: comp; Owner: -
--

ALTER TABLE ONLY comp.comp_record
    ADD CONSTRAINT comp_record_pkey PRIMARY KEY (comp_key, effective_date, effective_sequence);

--
-- Name: cycle_line cycle_line_pkey; Type: CONSTRAINT; Schema: comp; Owner: -
--

ALTER TABLE ONLY comp.cycle_line
    ADD CONSTRAINT cycle_line_pkey PRIMARY KEY (line_id);

--
-- Name: grade_range grade_range_pkey; Type: CONSTRAINT; Schema: comp; Owner: -
--

ALTER TABLE ONLY comp.grade_range
    ADD CONSTRAINT grade_range_pkey PRIMARY KEY (range_key, effective_date, effective_sequence);

--
-- Name: comp_record immutable_comp_comp_record; Type: TRIGGER; Schema: comp; Owner: -
--

CREATE TRIGGER immutable_comp_comp_record BEFORE DELETE OR UPDATE ON comp.comp_record FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();

--
-- Name: grade_range immutable_comp_grade_range; Type: TRIGGER; Schema: comp; Owner: -
--

CREATE TRIGGER immutable_comp_grade_range BEFORE DELETE OR UPDATE ON comp.grade_range FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();

--
--
