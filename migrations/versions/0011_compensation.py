"""Compensation schema (Specs/05): temporal ranges + comp records, cycles.

Revision ID: 0011
Revises: 0010
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

TEMPORAL_COLS = lambda: [  # noqa: E731 — shared shape for temporal tables
    sa.Column("effective_date", sa.Date(), primary_key=True),
    sa.Column("effective_sequence", sa.SmallInteger(), primary_key=True),
    sa.Column("action_code", sa.Text(), nullable=False),
    sa.Column("action_reason", sa.Text(), nullable=True),
    sa.Column("created_by", sa.Text(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column("source_channel", sa.Text(), nullable=False),
    sa.Column("correlation_id", sa.Uuid(), nullable=False),
]


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS comp")
    op.create_table(
        "grade_range",
        sa.Column("range_key", sa.Text(), primary_key=True),
        *TEMPORAL_COLS(),
        sa.Column("grade", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False),
        sa.Column("range_min", sa.Numeric(12, 2), nullable=False),
        sa.Column("range_mid", sa.Numeric(12, 2), nullable=False),
        sa.Column("range_max", sa.Numeric(12, 2), nullable=False),
        schema="comp",
    )
    op.create_table(
        "comp_record",
        sa.Column("comp_key", sa.Uuid(), primary_key=True),
        *TEMPORAL_COLS(),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("record_role", sa.Text(), nullable=False),
        sa.Column("base_annual", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False),
        sa.Column("grade", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("fte", sa.Numeric(4, 2), nullable=False),
        schema="comp",
    )
    op.create_table(
        "comp_cycle",
        sa.Column("cycle_id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("corporate_currency", sa.Text(), nullable=False),
        sa.Column("fx_rates", JSONB(), nullable=False),
        sa.Column("budget_pool", sa.Numeric(14, 2), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        schema="comp",
    )
    op.create_table(
        "cycle_line",
        sa.Column("line_id", sa.Uuid(), primary_key=True),
        sa.Column("cycle_id", sa.Uuid(), nullable=False),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("manager_id", sa.Text(), nullable=False),
        sa.Column("snapshot", JSONB(), nullable=False),
        sa.Column("merit_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("out_of_guideline", sa.Boolean(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        schema="comp",
    )
    for table in ("grade_range", "comp_record"):
        op.execute(f"""
            CREATE TRIGGER immutable_comp_{table}
                BEFORE UPDATE OR DELETE ON comp.{table}
                FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();
        """)


def downgrade() -> None:
    for table in ("cycle_line", "comp_cycle", "comp_record", "grade_range"):
        op.execute(f"DROP TABLE IF EXISTS comp.{table}")
    op.execute("DROP SCHEMA IF EXISTS comp")
