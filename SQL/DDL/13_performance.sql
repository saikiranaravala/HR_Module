-- SQL/DDL/13_performance.sql - goal, review_cycle, review_doc, calibration_adjustment (immutable), checkin, feedback (Specs/07)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: performance; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS performance;

--
-- Name: calibration_adjustment; Type: TABLE; Schema: performance; Owner: -
--

CREATE TABLE performance.calibration_adjustment (
    adjustment_id uuid NOT NULL,
    doc_id uuid NOT NULL,
    session_id text NOT NULL,
    before_rating text,
    after_rating text,
    rationale text NOT NULL,
    actor text NOT NULL,
    adjusted_at timestamp with time zone NOT NULL
);

--
-- Name: checkin; Type: TABLE; Schema: performance; Owner: -
--

CREATE TABLE performance.checkin (
    checkin_id uuid NOT NULL,
    worker_id text NOT NULL,
    manager_id text NOT NULL,
    occurred_on date NOT NULL,
    shared_notes text,
    private_notes text,
    private_notes_author text
);

--
-- Name: feedback; Type: TABLE; Schema: performance; Owner: -
--

CREATE TABLE performance.feedback (
    feedback_id uuid NOT NULL,
    author_id text NOT NULL,
    subject_id text NOT NULL,
    visibility text NOT NULL,
    body text NOT NULL,
    competency text,
    campaign_id text,
    given_on date NOT NULL
);

--
-- Name: goal; Type: TABLE; Schema: performance; Owner: -
--

CREATE TABLE performance.goal (
    goal_id uuid NOT NULL,
    worker_id text NOT NULL,
    title text NOT NULL,
    goal_type text NOT NULL,
    weight integer NOT NULL,
    parent_goal_id uuid,
    visibility text NOT NULL,
    status text NOT NULL,
    version integer NOT NULL,
    supersedes uuid
);

--
-- Name: review_cycle; Type: TABLE; Schema: performance; Owner: -
--

CREATE TABLE performance.review_cycle (
    cycle_id uuid NOT NULL,
    name text NOT NULL,
    template_key text NOT NULL,
    status text NOT NULL,
    launched_on date NOT NULL,
    window_end date NOT NULL
);

--
-- Name: review_doc; Type: TABLE; Schema: performance; Owner: -
--

CREATE TABLE performance.review_doc (
    doc_id uuid NOT NULL,
    cycle_id uuid NOT NULL,
    worker_id text NOT NULL,
    manager_id text NOT NULL,
    state text NOT NULL,
    rating text,
    narrative text,
    self_assessment text,
    ai_drafted boolean NOT NULL,
    ai_draft_edited boolean NOT NULL,
    prorated boolean NOT NULL,
    extension_until date,
    restricted boolean NOT NULL,
    amends uuid,
    amendment_reason text,
    skip_level_disagreement text,
    acknowledged_comment text,
    closeout_reason text,
    handoff_log jsonb
);

--
-- Name: calibration_adjustment calibration_adjustment_pkey; Type: CONSTRAINT; Schema: performance; Owner: -
--

ALTER TABLE ONLY performance.calibration_adjustment
    ADD CONSTRAINT calibration_adjustment_pkey PRIMARY KEY (adjustment_id);

--
-- Name: checkin checkin_pkey; Type: CONSTRAINT; Schema: performance; Owner: -
--

ALTER TABLE ONLY performance.checkin
    ADD CONSTRAINT checkin_pkey PRIMARY KEY (checkin_id);

--
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: performance; Owner: -
--

ALTER TABLE ONLY performance.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (feedback_id);

--
-- Name: goal goal_pkey; Type: CONSTRAINT; Schema: performance; Owner: -
--

ALTER TABLE ONLY performance.goal
    ADD CONSTRAINT goal_pkey PRIMARY KEY (goal_id);

--
-- Name: review_cycle review_cycle_pkey; Type: CONSTRAINT; Schema: performance; Owner: -
--

ALTER TABLE ONLY performance.review_cycle
    ADD CONSTRAINT review_cycle_pkey PRIMARY KEY (cycle_id);

--
-- Name: review_doc review_doc_pkey; Type: CONSTRAINT; Schema: performance; Owner: -
--

ALTER TABLE ONLY performance.review_doc
    ADD CONSTRAINT review_doc_pkey PRIMARY KEY (doc_id);

--
-- Name: calibration_adjustment immutable_performance_calibration_adjustment; Type: TRIGGER; Schema: performance; Owner: -
--

CREATE TRIGGER immutable_performance_calibration_adjustment BEFORE DELETE OR UPDATE ON performance.calibration_adjustment FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();

--
--
