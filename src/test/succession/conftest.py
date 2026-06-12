import pytest
from sqlalchemy import text

from platform_core.base import Base
from platform_core.db import make_engine, make_session_factory
from platform_core.temporal import install_immutability_guard

import platform_core.audit  # noqa: F401
import platform_core.policy.engine  # noqa: F401
import succession.models  # noqa: F401 — register models


@pytest.fixture(scope="session")
def engine():
    eng = make_engine(test=True)
    with eng.begin() as conn:
        for schema in ("platform", "succession"):
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            conn.execute(text(f"CREATE SCHEMA {schema}"))
        for schema in ("core", "integration", "ai", "workflow", "time_labor",
                       "payroll", "benefits", "service_delivery", "analytics",
                       "comp", "recruiting", "performance", "learning"):
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        install_immutability_guard(conn, "platform.audit_event")
        install_immutability_guard(conn, "succession.ninebox_placement")
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE succession.key_position, succession.slate_entry, "
            "succession.talent_profile, succession.ninebox_placement, "
            "succession.discovery_hold, platform.audit_event, "
            "platform.policy_decision_log"
        ))
    s = make_session_factory(engine)()
    yield s
    s.rollback()
    s.close()
