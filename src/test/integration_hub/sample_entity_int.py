"""Synthetic model for consumer-contract tests (not a product table)."""
from sqlalchemy import Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import Tier, tag


class IntWorkerRow(Base):
    __tablename__ = "int_worker_row_sample"

    display_name: Mapped[str] = mapped_column(
        Text, primary_key=True,
        info=tag(category="personal", purpose="employment-admin",
                 lawful_basis="contract", retention_class="emp+7y", tier=Tier.T1),
    )
    email: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        info=tag(category="contact", purpose="employment-admin",
                 lawful_basis="contract", retention_class="emp+7y", tier=Tier.T1),
    )
    base_salary = mapped_column(
        Numeric(12, 2), nullable=True,
        info=tag(category="compensation", purpose="payroll",
                 lawful_basis="contract", retention_class="payroll-statutory", tier=Tier.T2),
    )
