-- SQL/DDL/02_workflow.sql - workflow_instance, step_execution (Specs/12)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: workflow; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS workflow;

--
-- Name: step_execution; Type: TABLE; Schema: workflow; Owner: -
--

CREATE TABLE workflow.step_execution (
    execution_id uuid NOT NULL,
    instance_id uuid NOT NULL,
    step_id text NOT NULL,
    step_type text NOT NULL,
    resolved_assignee text,
    resolution_reason text,
    status text NOT NULL,
    acted_by text,
    acted_at timestamp with time zone
);

--
-- Name: workflow_instance; Type: TABLE; Schema: workflow; Owner: -
--

CREATE TABLE workflow.workflow_instance (
    instance_id uuid NOT NULL,
    definition_key text NOT NULL,
    definition_version integer NOT NULL,
    subject_ref text NOT NULL,
    initiator text NOT NULL,
    status text NOT NULL,
    current_step_index integer NOT NULL,
    payload jsonb,
    created_at timestamp with time zone NOT NULL,
    correlation_id uuid NOT NULL
);

--
-- Name: step_execution step_execution_pkey; Type: CONSTRAINT; Schema: workflow; Owner: -
--

ALTER TABLE ONLY workflow.step_execution
    ADD CONSTRAINT step_execution_pkey PRIMARY KEY (execution_id);

--
-- Name: workflow_instance workflow_instance_pkey; Type: CONSTRAINT; Schema: workflow; Owner: -
--

ALTER TABLE ONLY workflow.workflow_instance
    ADD CONSTRAINT workflow_instance_pkey PRIMARY KEY (instance_id);

--
-- Name: ix_step_execution_instance; Type: INDEX; Schema: workflow; Owner: -
--

CREATE INDEX ix_step_execution_instance ON workflow.step_execution USING btree (instance_id);

--
--
