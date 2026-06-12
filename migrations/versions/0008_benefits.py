"""Benefits schema (Specs/04): plans, effective-dated rates, enrollments.

Revision ID: 0008
Revises: 0007
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS benefits")
    op.create_table(
        "benefit_plan",
        sa.Column("plan_id", sa.Uuid(), primary_key=True),
        sa.Column("plan_type", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("requires_eoi_above_multiple", sa.Integer(), nullable=True),
        sa.Column("default_option", sa.Text(), nullable=True),
        schema="benefits",
    )
    op.create_table(
        "benefit_rate",
        sa.Column("rate_id", sa.Uuid(), primary_key=True),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("option", sa.Text(), nullable=False),
        sa.Column("age_min", sa.Integer(), nullable=False),
        sa.Column("age_max", sa.Integer(), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("annual_premium", sa.Numeric(12, 2), nullable=False),
        sa.Column("employer_pct", sa.Numeric(5, 2), nullable=False),
        schema="benefits",
    )
    op.create_table(
        "enrollment",
        sa.Column("enrollment_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("option", sa.Text(), nullable=False),  # T3 health-adjacent
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("coverage_start", sa.Date(), nullable=False),
        sa.Column("coverage_end", sa.Date(), nullable=True),
        sa.Column("dependents", JSONB(), nullable=True),  # T3 health-adjacent
        sa.Column("source", sa.Text(), nullable=False),
        schema="benefits",
    )


def downgrade() -> None:
    for table in ("enrollment", "benefit_rate", "benefit_plan"):
        op.execute(f"DROP TABLE IF EXISTS benefits.{table}")
    op.execute("DROP SCHEMA IF EXISTS benefits")
