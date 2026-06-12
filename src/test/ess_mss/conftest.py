import pytest
from sqlalchemy import text

from platform_core.base import Base
from platform_core.db import make_engine, make_session_factory
from platform_core.temporal import install_immutability_guard

import ess_mss.models  # noqa: F401 — register models
import platform_core.audit  # noqa: F401
import platform_core.policy.engine  # noqa: F401
import rules_workflow.workflow  # noqa: F401


@pytest.fixture(scope="session")
def engine():
    eng = make_engine(test=True)
    with eng.begin() as conn:
        for schema in ("platform", "service_delivery", "workflow"):
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            conn.execute(text(f"CREATE SCHEMA {schema}"))
        for schema in ("core", "integration", "ai", "time_labor", "payroll", "benefits"):
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
            'TRUNCATE service_delivery."case", service_delivery.case_note, '
            "service_delivery.kb_article, service_delivery.delegation, "
            "service_delivery.notification_pref, service_delivery.access_grant, "
            "workflow.workflow_instance, workflow.step_execution, "
            "platform.audit_event, platform.policy_decision_log"
        ))
    s = make_session_factory(engine)()
    yield s
    s.rollback()
    s.close()


class Org:
    """manager_of resolver over a static chain."""

    def __init__(self, chain: dict[str, str]):
        self.chain = chain

    def manager_of(self, worker_id: str) -> str | None:
        return self.chain.get(worker_id)


@pytest.fixture
def org():
    # emp-1 -> mgr-1 -> dir-1 -> vp-1
    return Org({"emp-1": "mgr-1", "mgr-1": "dir-1", "dir-1": "vp-1"})
