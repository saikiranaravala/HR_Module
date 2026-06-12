import pytest
from sqlalchemy import text

from platform_core.base import Base
from platform_core.db import make_engine, make_session_factory
from platform_core.temporal import install_immutability_guard

import compensation.models  # noqa: F401 — register models
import platform_core.audit  # noqa: F401
import platform_core.policy.engine  # noqa: F401



@pytest.fixture(scope="session")
def engine():
    eng = make_engine(test=True)
    with eng.begin() as conn:
        for schema in ("platform", "comp"):
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            conn.execute(text(f"CREATE SCHEMA {schema}"))
        for schema in ("core", "integration", "ai", "workflow", "time_labor",
                       "payroll", "benefits", "service_delivery", "analytics"):
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        install_immutability_guard(conn, "platform.audit_event")
        install_immutability_guard(conn, "comp.grade_range")
        install_immutability_guard(conn, "comp.comp_record")
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE comp.grade_range, comp.comp_record, comp.comp_cycle, "
            "comp.cycle_line, platform.audit_event"
        ))
    s = make_session_factory(engine)()
    yield s
    s.rollback()
    s.close()
