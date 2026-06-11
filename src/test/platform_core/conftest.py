import uuid
from datetime import date

import pytest
from sqlalchemy import text

from platform_core.base import Base
from platform_core.db import make_engine, make_session_factory
from platform_core.temporal import install_immutability_guard
from sample_entity import WorkerProfile


@pytest.fixture(scope="session")
def engine():
    eng = make_engine(test=True)
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS platform CASCADE"))
        conn.execute(text("CREATE SCHEMA platform"))
        conn.execute(text("DROP TABLE IF EXISTS worker_profile"))
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        install_immutability_guard(conn, "platform.audit_event")
        install_immutability_guard(conn, "worker_profile")
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    # Clean slate per test. TRUNCATE bypasses row-level triggers by design,
    # so the immutability guard does not block it (test-db only).
    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE platform.audit_event, platform.policy_decision_log, worker_profile")
        )
    s = make_session_factory(engine)()
    yield s
    s.rollback()
    s.close()


@pytest.fixture
def temporal_model():
    return WorkerProfile


@pytest.fixture
def make_row():
    def _make(entity_id, effective_date: date, **overrides):
        defaults = dict(
            worker_id=entity_id,
            effective_date=effective_date,
            action_code="DTA",
            display_name="Synthetic Worker",
            email="synthetic.worker@example.invalid",
            base_salary=50000,
        )
        defaults.update(overrides)
        return WorkerProfile(**defaults)

    return _make


@pytest.fixture
def correlation_id():
    return uuid.uuid4()
