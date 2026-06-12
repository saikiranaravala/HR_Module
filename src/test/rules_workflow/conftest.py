import pytest
from sqlalchemy import text

from platform_core.base import Base
from platform_core.db import make_engine, make_session_factory
from platform_core.temporal import install_immutability_guard

# Import models so create_all sees them.
import rules_workflow.workflow  # noqa: F401


@pytest.fixture(scope="session")
def engine():
    eng = make_engine(test=True)
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS platform CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS workflow CASCADE"))
        conn.execute(text("CREATE SCHEMA platform"))
        conn.execute(text("CREATE SCHEMA workflow"))
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        install_immutability_guard(conn, "platform.audit_event")
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE platform.audit_event, workflow.workflow_instance, workflow.step_execution"
        ))
    s = make_session_factory(engine)()
    yield s
    s.rollback()
    s.close()


class FakeOrg:
    """worker -> manager chain for routing tests."""

    def __init__(self, chain: dict[str, str]):
        self._chain = chain

    def manager_of(self, worker_id):
        return self._chain.get(worker_id)


@pytest.fixture
def org():
    # w1 -> mgr1 -> dir1 -> ceo (top of tree)
    return FakeOrg({"w1": "mgr1", "mgr1": "dir1", "dir1": "ceo"})
