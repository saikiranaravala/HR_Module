import pytest
from sqlalchemy import text

from platform_core.base import Base
from platform_core.db import make_engine, make_session_factory
from platform_core.temporal import install_immutability_guard

import ai_layer.gateway  # noqa: F401 — register models
import platform_core.audit  # noqa: F401
import platform_core.policy.engine  # noqa: F401


@pytest.fixture(scope="session")
def engine():
    eng = make_engine(test=True)
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS platform CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS ai CASCADE"))
        conn.execute(text("CREATE SCHEMA platform"))
        conn.execute(text("CREATE SCHEMA ai"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS workflow"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS integration"))
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        install_immutability_guard(conn, "platform.audit_event")
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE platform.audit_event, ai.ai_ledger"))
    s = make_session_factory(engine)()
    yield s
    s.rollback()
    s.close()
