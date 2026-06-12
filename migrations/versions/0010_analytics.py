"""Analytics schema (Specs/11): SCD2 dimension, certified snapshots, org bridge.

Revision ID: 0010
Revises: 0009
"""
import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS analytics")
    op.create_table(
        "dim_worker",
        sa.Column("row_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_key", sa.Text(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=False),
        sa.Column("org_path", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("worker_type", sa.Text(), nullable=False),
        sa.Column("fte", sa.Numeric(4, 2), nullable=False),
        sa.Column("exited", sa.Boolean(), nullable=False),
        sa.Column("regrettable_exit", sa.Boolean(), nullable=False),
        schema="analytics",
    )
    op.create_table(
        "certified_snapshot",
        sa.Column("snapshot_id", sa.Uuid(), primary_key=True),
        sa.Column("as_of", sa.Date(), nullable=False),
        sa.Column("metric", sa.Text(), nullable=False),
        sa.Column("value", sa.Numeric(18, 4), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("restatement_of", sa.Uuid(), nullable=True),
        sa.Column("annotation", sa.Text(), nullable=True),
        schema="analytics",
    )
    op.create_table(
        "org_bridge",
        sa.Column("bridge_id", sa.Uuid(), primary_key=True),
        sa.Column("old_org_path", sa.Text(), nullable=False),
        sa.Column("new_org_path", sa.Text(), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        schema="analytics",
    )
    # Certified snapshots are immutable at the database level (restatement =
    # new version row; UPDATE/DELETE forbidden — same guard as audit/payroll).
    op.execute("""
        CREATE TRIGGER immutable_analytics_certified_snapshot
            BEFORE UPDATE OR DELETE ON analytics.certified_snapshot
            FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();
    """)


def downgrade() -> None:
    for table in ("org_bridge", "certified_snapshot", "dim_worker"):
        op.execute(f"DROP TABLE IF EXISTS analytics.{table}")
    op.execute("DROP SCHEMA IF EXISTS analytics")
