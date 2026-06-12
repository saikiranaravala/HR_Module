-- SQL/DDL/15_succession.sql - key_position, slate_entry, talent_profile, ninebox_placement (immutable), discovery_hold (Specs/09)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: succession; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS succession;

--
-- Name: discovery_hold; Type: TABLE; Schema: succession; Owner: -
--

CREATE TABLE succession.discovery_hold (
    hold_id uuid NOT NULL,
    scope text NOT NULL,
    requested_by text NOT NULL,
    counsel text NOT NULL,
    privileged boolean NOT NULL,
    counsel_approved boolean NOT NULL,
    released boolean NOT NULL,
    artifact_refs jsonb
);

--
-- Name: key_position; Type: TABLE; Schema: succession; Owner: -
--

CREATE TABLE succession.key_position (
    position_id uuid NOT NULL,
    title text NOT NULL,
    incumbent_id text,
    division_path text NOT NULL,
    criticality jsonb NOT NULL,
    retirement_band text
);

--
-- Name: ninebox_placement; Type: TABLE; Schema: succession; Owner: -
--

CREATE TABLE succession.ninebox_placement (
    placement_id uuid NOT NULL,
    worker_id text NOT NULL,
    session_id text NOT NULL,
    performance text NOT NULL,
    potential text NOT NULL,
    rationale text NOT NULL,
    actor text NOT NULL,
    placed_at timestamp with time zone NOT NULL
);

--
-- Name: slate_entry; Type: TABLE; Schema: succession; Owner: -
--

CREATE TABLE succession.slate_entry (
    entry_id uuid NOT NULL,
    position_id uuid NOT NULL,
    successor_id text NOT NULL,
    readiness text NOT NULL,
    rationale text NOT NULL,
    emergency boolean NOT NULL,
    development_plan_ref text,
    last_validated date NOT NULL,
    status text NOT NULL
);

--
-- Name: talent_profile; Type: TABLE; Schema: succession; Owner: -
--

CREATE TABLE succession.talent_profile (
    profile_id uuid NOT NULL,
    worker_id text NOT NULL,
    aspirations text,
    aspirations_consent boolean NOT NULL,
    mobility_prefs jsonb,
    experiences jsonb,
    interim boolean NOT NULL,
    history_note text
);

--
-- Name: discovery_hold discovery_hold_pkey; Type: CONSTRAINT; Schema: succession; Owner: -
--

ALTER TABLE ONLY succession.discovery_hold
    ADD CONSTRAINT discovery_hold_pkey PRIMARY KEY (hold_id);

--
-- Name: key_position key_position_pkey; Type: CONSTRAINT; Schema: succession; Owner: -
--

ALTER TABLE ONLY succession.key_position
    ADD CONSTRAINT key_position_pkey PRIMARY KEY (position_id);

--
-- Name: ninebox_placement ninebox_placement_pkey; Type: CONSTRAINT; Schema: succession; Owner: -
--

ALTER TABLE ONLY succession.ninebox_placement
    ADD CONSTRAINT ninebox_placement_pkey PRIMARY KEY (placement_id);

--
-- Name: slate_entry slate_entry_pkey; Type: CONSTRAINT; Schema: succession; Owner: -
--

ALTER TABLE ONLY succession.slate_entry
    ADD CONSTRAINT slate_entry_pkey PRIMARY KEY (entry_id);

--
-- Name: talent_profile talent_profile_pkey; Type: CONSTRAINT; Schema: succession; Owner: -
--

ALTER TABLE ONLY succession.talent_profile
    ADD CONSTRAINT talent_profile_pkey PRIMARY KEY (profile_id);

--
-- Name: ninebox_placement immutable_succession_ninebox_placement; Type: TRIGGER; Schema: succession; Owner: -
--

CREATE TRIGGER immutable_succession_ninebox_placement BEFORE DELETE OR UPDATE ON succession.ninebox_placement FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();

--
--
