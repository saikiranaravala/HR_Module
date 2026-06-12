"""Integration hub: connector runs/credentials, JML provisioning queue (Specs/13).

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS integration")
    op.create_table(
        "connector_run",
        sa.Column("run_id", sa.Uuid(), primary_key=True),
        sa.Column("connector_key", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("error_normalized", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        schema="integration",
    )
    op.create_table(
        "connector_credential",
        sa.Column("credential_id", sa.Uuid(), primary_key=True),
        sa.Column("connector_key", sa.Text(), nullable=False),
        sa.Column("credential_kind", sa.Text(), nullable=False),
        sa.Column("reference", sa.Text(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=False),
        schema="integration",
    )
    op.create_table(
        "provisioning_action",
        sa.Column("action_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("action_type", sa.Text(), nullable=False),
        sa.Column("effective_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attributes", JSONB(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("alert_raised", sa.Boolean(), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        schema="integration",
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS integration.provisioning_action")
    op.execute("DROP TABLE IF EXISTS integration.connector_credential")
    op.execute("DROP TABLE IF EXISTS integration.connector_run")
    op.execute("DROP SCHEMA IF EXISTS integration")
