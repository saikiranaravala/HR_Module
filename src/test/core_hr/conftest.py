import pytest
from sqlalchemy import text

from platform_core.base import Base
from platform_core.db import make_engine, make_session_factory
from platform_core.temporal import install_immutability_guard

import core_hr.models  # noqa: F401 — register models
import integration_hub.jml  # noqa: F401 (terminate() JML path)
import platform_core.audit  # noqa: F401
import platform_core.policy.engine  # noqa: F401


@pytest.fixture(scope="session")
def engine():
    eng = make_engine(test=True)
    with eng.begin() as conn:
        for schema in ("platform", "core", "integration"):
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            conn.execute(text(f"CREATE SCHEMA {schema}"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS workflow"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS ai"))
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        install_immutability_guard(conn, "platform.audit_event")
        install_immutability_guard(conn, "core.assignment")
        install_immutability_guard(conn, "core.person_name")
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE platform.audit_event, core.person, core.person_name, "
            "core.national_id, core.work_eligibility, core.worker, core.assignment, "
            "core.department, core.position, integration.provisioning_action"
        ))
    s = make_session_factory(engine)()
    yield s
    s.rollback()
    s.close()


class FakeScim:
    def __init__(self):
        self.calls = []

    def create_account(self, worker_id, attributes):
        self.calls.append(("create", worker_id))

    def update_attributes(self, worker_id, attributes):
        self.calls.append(("update", worker_id))

    def disable_account(self, worker_id):
        self.calls.append(("disable", worker_id))


@pytest.fixture
def scim():
    return FakeScim()
