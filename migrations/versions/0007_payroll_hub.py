"""Payroll hub schema (Specs/03): cycles, input snapshots, results.

Revision ID: 0007
Revises: 0006
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS payroll")
    op.create_table(
        "pay_cycle",
        sa.Column("cycle_id", sa.Uuid(), primary_key=True),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("pay_group", sa.Text(), nullable=False),
        sa.Column("period_key", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("off_cycle", sa.Boolean(), nullable=False),
        sa.Column("snapshot_hash", sa.Text(), nullable=True),
        sa.Column("compiled_by", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.Text(), nullable=True),
        sa.Column("gross_total", sa.Numeric(16, 2), nullable=True),
        sa.Column("state_changed_at", sa.DateTime(timezone=True), nullable=True),
        schema="payroll",
    )
    op.create_table(
        "pay_input_record",
        sa.Column("input_id", sa.Uuid(), primary_key=True),
        sa.Column("cycle_id", sa.Uuid(), nullable=False),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("held", sa.Boolean(), nullable=False),
        sa.Column("hold_reason", sa.Text(), nullable=True),
        schema="payroll",
    )
    op.create_table(
        "pay_result_record",
        sa.Column("result_id", sa.Uuid(), primary_key=True),
        sa.Column("cycle_id", sa.Uuid(), nullable=False),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("gross", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_deductions", sa.Numeric(14, 2), nullable=False),
        sa.Column("net", sa.Numeric(14, 2), nullable=False),
        sa.Column("elements", JSONB(), nullable=True),
        schema="payroll",
    )


def downgrade() -> None:
    for table in ("pay_result_record", "pay_input_record", "pay_cycle"):
        op.execute(f"DROP TABLE IF EXISTS payroll.{table}")
    op.execute("DROP SCHEMA IF EXISTS payroll")
