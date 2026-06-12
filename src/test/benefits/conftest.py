from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from platform_core.base import Base
from platform_core.db import make_engine, make_session_factory
from platform_core.temporal import install_immutability_guard

import benefits.models  # noqa: F401
import platform_core.audit  # noqa: F401
import platform_core.policy.engine  # noqa: F401

from benefits.models import BenefitPlan, BenefitRate


@pytest.fixture(scope="session")
def engine():
    eng = make_engine(test=True)
    with eng.begin() as conn:
        for schema in ("platform", "benefits"):
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            conn.execute(text(f"CREATE SCHEMA {schema}"))
        for schema in ("workflow", "integration", "ai", "core", "time_labor", "payroll"):
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
            "TRUNCATE benefits.benefit_plan, benefits.benefit_rate, "
            "benefits.enrollment, platform.audit_event"
        ))
    s = make_session_factory(engine)()
    yield s
    s.rollback()
    s.close()


@pytest.fixture
def medical_plan(session):
    plan = BenefitPlan(plan_type="medical", name="PPO Standard", country="US",
                       default_option="EE")
    session.add(plan)
    session.flush()
    session.add(BenefitRate(plan_id=plan.plan_id, option="EE",
                            effective_date=date(2026, 1, 1),
                            annual_premium=Decimal("6000"), employer_pct=Decimal("75")))
    session.add(BenefitRate(plan_id=plan.plan_id, option="EE+FAM",
                            effective_date=date(2026, 1, 1),
                            annual_premium=Decimal("18000"), employer_pct=Decimal("70")))
    session.flush()
    return plan


@pytest.fixture
def life_plan(session):
    plan = BenefitPlan(plan_type="life", name="GTL", country="US",
                       requires_eoi_above_multiple=3, default_option="1x")
    session.add(plan)
    session.flush()
    return plan
