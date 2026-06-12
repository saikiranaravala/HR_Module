from decimal import Decimal

import pytest
from sqlalchemy import text

from platform_core.base import Base
from platform_core.db import make_engine, make_session_factory
from platform_core.temporal import install_immutability_guard

import payroll_hub.cycle  # noqa: F401 — register models
import platform_core.audit  # noqa: F401
import platform_core.policy.engine  # noqa: F401

from payroll_hub.cpdc import CpdcRecord, PayElement


@pytest.fixture(scope="session")
def engine():
    eng = make_engine(test=True)
    with eng.begin() as conn:
        for schema in ("platform", "payroll", "integration"):
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            conn.execute(text(f"CREATE SCHEMA {schema}"))
        for schema in ("workflow", "ai", "core", "time_labor"):
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
            "TRUNCATE payroll.pay_cycle, payroll.pay_input_record, "
            "payroll.pay_result_record, integration.connector_run, platform.audit_event"
        ))
    s = make_session_factory(engine)()
    yield s
    s.rollback()
    s.close()


def make_record(worker="w-1", country="US", gross=Decimal("5000"),
                deductions=Decimal("750"), **kwargs) -> CpdcRecord:
    return CpdcRecord(
        worker_id=worker, legal_entity="meridian-us", country=country,
        pay_group="us-biweekly", period_key="2026-P12",
        elements=[
            PayElement("REG", "earning", gross),
            PayElement("401K" if country == "US" else "HEALTH", "deduction", deductions),
        ],
        **kwargs,
    )


@pytest.fixture
def record_factory():
    return make_record
