import pytest
from sqlalchemy import text

from platform_core.base import Base
from platform_core.db import make_engine, make_session_factory
from platform_core.temporal import install_immutability_guard

import integration_hub.chassis  # noqa: F401 — register models with metadata
import integration_hub.jml  # noqa: F401
import platform_core.audit  # noqa: F401
import platform_core.policy.engine  # noqa: F401


@pytest.fixture(scope="session")
def engine():
    eng = make_engine(test=True)
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS platform CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS integration CASCADE"))
        conn.execute(text("CREATE SCHEMA platform"))
        conn.execute(text("CREATE SCHEMA integration"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS workflow"))
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        install_immutability_guard(conn, "platform.audit_event")
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE integration.connector_run, integration.connector_credential, "
            "integration.provisioning_action, platform.audit_event"
        ))
    s = make_session_factory(engine)()
    yield s
    s.rollback()
    s.close()


class FakeScim:
    """SCIM client double; can be switched to outage mode."""

    def __init__(self):
        self.calls: list[tuple] = []
        self.outage = False

    def _check(self):
        if self.outage:
            raise ConnectionError("IdP unreachable")

    def create_account(self, worker_id, attributes):
        self._check()
        self.calls.append(("create", worker_id))

    def update_attributes(self, worker_id, attributes):
        self._check()
        self.calls.append(("update", worker_id))

    def disable_account(self, worker_id):
        self._check()
        self.calls.append(("disable", worker_id))


@pytest.fixture
def scim():
    return FakeScim()
