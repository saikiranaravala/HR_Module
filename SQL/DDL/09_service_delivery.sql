-- SQL/DDL/09_service_delivery.sql - case, case_note, kb_article, delegation, notification_pref, access_grant (Specs/10)
-- Generated from the live alembic-managed database (rev 0016) via pg_dump.
-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);
-- use these files only to build a standalone copy, then: alembic stamp head.

--
--

--
-- Name: service_delivery; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS service_delivery;

--
-- Name: access_grant; Type: TABLE; Schema: service_delivery; Owner: -
--

CREATE TABLE service_delivery.access_grant (
    grant_id uuid NOT NULL,
    worker_id text NOT NULL,
    kind text NOT NULL,
    scope jsonb,
    reason text,
    starts_on date NOT NULL,
    expires_on date,
    released boolean NOT NULL
);

--
-- Name: case; Type: TABLE; Schema: service_delivery; Owner: -
--

CREATE TABLE service_delivery."case" (
    case_id uuid NOT NULL,
    worker_id text NOT NULL,
    topic text NOT NULL,
    queue text NOT NULL,
    priority text NOT NULL,
    status text NOT NULL,
    description text NOT NULL,
    transcript jsonb,
    opened_at timestamp with time zone NOT NULL,
    sla_due_at timestamp with time zone NOT NULL,
    closed_at timestamp with time zone,
    satisfaction integer
);

--
-- Name: case_note; Type: TABLE; Schema: service_delivery; Owner: -
--

CREATE TABLE service_delivery.case_note (
    note_id uuid NOT NULL,
    case_id uuid NOT NULL,
    author text NOT NULL,
    visibility text NOT NULL,
    body text NOT NULL,
    created_at timestamp with time zone NOT NULL
);

--
-- Name: delegation; Type: TABLE; Schema: service_delivery; Owner: -
--

CREATE TABLE service_delivery.delegation (
    delegation_id uuid NOT NULL,
    delegator text NOT NULL,
    delegate text NOT NULL,
    scope_types jsonb NOT NULL,
    starts_on date NOT NULL,
    ends_on date NOT NULL,
    revoked boolean NOT NULL
);

--
-- Name: kb_article; Type: TABLE; Schema: service_delivery; Owner: -
--

CREATE TABLE service_delivery.kb_article (
    article_id uuid NOT NULL,
    title text NOT NULL,
    body text NOT NULL,
    country text NOT NULL,
    population text NOT NULL,
    version integer NOT NULL,
    status text NOT NULL,
    is_policy boolean NOT NULL,
    published_on date,
    review_due date
);

--
-- Name: notification_pref; Type: TABLE; Schema: service_delivery; Owner: -
--

CREATE TABLE service_delivery.notification_pref (
    pref_id uuid NOT NULL,
    worker_id text NOT NULL,
    notif_type text,
    channels jsonb,
    quiet_start integer,
    quiet_end integer,
    personal_channel_consent boolean NOT NULL
);

--
-- Name: access_grant access_grant_pkey; Type: CONSTRAINT; Schema: service_delivery; Owner: -
--

ALTER TABLE ONLY service_delivery.access_grant
    ADD CONSTRAINT access_grant_pkey PRIMARY KEY (grant_id);

--
-- Name: case_note case_note_pkey; Type: CONSTRAINT; Schema: service_delivery; Owner: -
--

ALTER TABLE ONLY service_delivery.case_note
    ADD CONSTRAINT case_note_pkey PRIMARY KEY (note_id);

--
-- Name: case case_pkey; Type: CONSTRAINT; Schema: service_delivery; Owner: -
--

ALTER TABLE ONLY service_delivery."case"
    ADD CONSTRAINT case_pkey PRIMARY KEY (case_id);

--
-- Name: delegation delegation_pkey; Type: CONSTRAINT; Schema: service_delivery; Owner: -
--

ALTER TABLE ONLY service_delivery.delegation
    ADD CONSTRAINT delegation_pkey PRIMARY KEY (delegation_id);

--
-- Name: kb_article kb_article_pkey; Type: CONSTRAINT; Schema: service_delivery; Owner: -
--

ALTER TABLE ONLY service_delivery.kb_article
    ADD CONSTRAINT kb_article_pkey PRIMARY KEY (article_id);

--
-- Name: notification_pref notification_pref_pkey; Type: CONSTRAINT; Schema: service_delivery; Owner: -
--

ALTER TABLE ONLY service_delivery.notification_pref
    ADD CONSTRAINT notification_pref_pkey PRIMARY KEY (pref_id);

--
--
