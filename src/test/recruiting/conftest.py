from datetime import date

import pytest
from sqlalchemy import text

from platform_core.base import Base
from platform_core.db import make_engine, make_session_factory
from platform_core.temporal import install_immutability_guard

import ess_mss.models  # noqa: F401 — adverse-finding escalation target
import platform_core.audit  # noqa: F401
import platform_core.policy.engine  # noqa: F401
import recruiting.models  # noqa: F401 — register models

from recruiting.models import CandidateProfile, Requisition
from recruiting import pipeline


@pytest.fixture(scope="session")
def engine():
    eng = make_engine(test=True)
    with eng.begin() as conn:
        for schema in ("platform", "recruiting", "service_delivery"):
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            conn.execute(text(f"CREATE SCHEMA {schema}"))
        for schema in ("core", "integration", "ai", "workflow", "time_labor",
                       "payroll", "benefits", "analytics", "comp"):
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        install_immutability_guard(conn, "platform.audit_event")
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE recruiting.candidate_profile, recruiting.requisition, "
            "recruiting.application, recruiting.offer, "
            'service_delivery."case", service_delivery.case_note, '
            "platform.audit_event, platform.policy_decision_log"
        ))
    s = make_session_factory(engine)()
    yield s
    s.rollback()
    s.close()


@pytest.fixture
def req(session):
    return Requisition(position_id="pos-1", title="Platform Engineer", grade="G7",
                       country="US", jurisdiction="US-CO", headcount_type="backfill",
                       range_min=80000, range_max=120000, status="open")


@pytest.fixture
def candidate(session):
    c = CandidateProfile(full_name="Avery Quinn", email="avery@example.test",
                         country="US", consent_captured_on=date(2026, 5, 1))
    session.add(c)
    session.flush()
    return c
