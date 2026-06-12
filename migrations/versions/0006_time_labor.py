"""Time & Labor schema (Specs/02).

Revision ID: 0006
Revises: 0005
"""
import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS time_labor")
    op.create_table(
        "time_entry",
        sa.Column("entry_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("in_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("out_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone_name", sa.Text(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("pay_group", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=True),
        schema="time_labor",
    )
    op.create_table(
        "time_result",
        sa.Column("result_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Uuid(), nullable=False),
        sa.Column("period_key", sa.Text(), nullable=False),
        sa.Column("pay_group", sa.Text(), nullable=False),
        sa.Column("earnings_code", sa.Text(), nullable=False),
        sa.Column("hours", sa.Numeric(7, 2), nullable=False),
        sa.Column("rate", sa.Numeric(12, 4), nullable=False),
        sa.Column("is_retro_delta", sa.Boolean(), nullable=False),
        sa.Column("origin_result_id", sa.Uuid(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("locked", sa.Boolean(), nullable=False),
        schema="time_labor",
    )
    op.create_table(
        "accrual_lot",
        sa.Column("lot_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Uuid(), nullable=False),
        sa.Column("absence_type", sa.Text(), nullable=False),
        sa.Column("granted_on", sa.Date(), nullable=False),
        sa.Column("hours_granted", sa.Numeric(7, 2), nullable=False),
        sa.Column("hours_consumed", sa.Numeric(7, 2), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=True),
        schema="time_labor",
    )


def downgrade() -> None:
    for table in ("accrual_lot", "time_result", "time_entry"):
        op.execute(f"DROP TABLE IF EXISTS time_labor.{table}")
    op.execute("DROP SCHEMA IF EXISTS time_labor")
