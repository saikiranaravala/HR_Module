"""Synthetic temporal entity used by the conformance and policy tests.

WorkerProfile is NOT a product table — Core HR (Module Specs/01) will define
the real person model. This exists so platform_core's pattern is proven against
a realistic shape, including a T2 field for read-logging tests. All data
written to it is synthetic.
"""
import uuid

from sqlalchemy import Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag
from platform_core.temporal import TemporalMixin


@register_model
class WorkerProfile(TemporalMixin, Base):
    __tablename__ = "worker_profile"
    __temporal_identity__ = "worker_id"

    worker_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, info=dict(RECORD_KEEPING_TAG)
    )
    display_name: Mapped[str] = mapped_column(
        Text,
        info=tag(category="personal", purpose="employment-admin",
                 lawful_basis="contract", retention_class="emp+7y", tier=Tier.T1),
    )
    email: Mapped[str] = mapped_column(
        Text,
        info=tag(category="contact", purpose="employment-admin",
                 lawful_basis="contract", retention_class="emp+7y", tier=Tier.T1),
    )
    base_salary = mapped_column(
        Numeric(12, 2),
        info=tag(category="compensation", purpose="payroll",
                 lawful_basis="contract", retention_class="payroll-statutory", tier=Tier.T2),
    )
