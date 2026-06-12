from datetime import date

import pytest
from sqlalchemy import text

from platform_core.base import Base
from platform_core.db import make_engine, make_session_factory
from platform_core.temporal import install_immutability_guard

import performance.models  # noqa: F401 — register models
import platform_core.audit  # noqa: F401
import platform_core.policy.engine  # noqa: F401

from performance import cycles
from performance.models import ReviewDoc


@pytest.fixture(scope="session")
def engine():
    eng = make_engine(test=True)
    with eng.begin() as conn:
        for schema in ("platform", "performance"):
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            conn.execute(text(f"CREATE SCHEMA {schema}"))
        for schema in ("core", "integration", "ai", "workflow", "time_labor",
                       "payroll", "benefits", "service_delivery", "analytics",
                       "comp", "recruiting"):
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        install_immutability_guard(conn, "platform.audit_event")
        install_immutability_guard(conn, "performance.calibration_adjustment")
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE performance.goal, performance.review_cycle, "
            "performance.review_doc, performance.calibration_adjustment, "
            "performance.checkin, performance.feedback, platform.audit_event"
        ))
    s = make_session_factory(engine)()
    yield s
    s.rollback()
    s.close()


@pytest.fixture
def doc(session):
    """A manager-done review doc inside a launched cycle."""
    cycle, docs = cycles.launch_cycle(
        session, name="FY26 Annual", template_key="annual-standard",
        launched_on=date(2026, 1, 15), window_end=date(2026, 3, 31),
        population=[{"worker_id": "w-1", "manager_id": "mgr-1",
                     "hire_date": date(2024, 1, 1)}],
    )
    d = docs[0]
    d.narrative = "Solid delivery on platform goals."
    d.rating = "meets"
    d.state = "manager-done"
    session.flush()
    return d
