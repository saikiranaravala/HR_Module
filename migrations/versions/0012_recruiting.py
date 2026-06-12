"""Recruiting schema (Specs/06): candidates, requisitions, applications, offers.

Revision ID: 0012
Revises: 0011
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS recruiting")
    op.create_table(
        "candidate_profile",
        sa.Column("candidate_id", sa.Uuid(), primary_key=True),
        sa.Column("full_name", sa.Text(), nullable=True),  # nullable: erasure
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("internal_worker_id", sa.Text(), nullable=True),
        sa.Column("do_not_rehire", sa.Boolean(), nullable=False),  # T2 policy-gated
        sa.Column("consent_captured_on", sa.Date(), nullable=True),
        sa.Column("erased", sa.Boolean(), nullable=False),
        schema="recruiting",
    )
    op.create_table(
        "requisition",
        sa.Column("requisition_id", sa.Uuid(), primary_key=True),
        sa.Column("position_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("grade", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("jurisdiction", sa.Text(), nullable=True),
        sa.Column("headcount_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("range_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("range_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("posting_text", sa.Text(), nullable=True),
        schema="recruiting",
    )
    op.create_table(
        "application",
        sa.Column("application_id", sa.Uuid(), primary_key=True),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("requisition_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("disposition_code", sa.Text(), nullable=True),
        sa.Column("internal", sa.Boolean(), nullable=False),
        sa.Column("confidential", sa.Boolean(), nullable=False),
        sa.Column("ai_rank", sa.Integer(), nullable=True),     # advisory only
        sa.Column("ai_explanation", sa.Text(), nullable=True),
        sa.Column("applied_on", sa.Date(), nullable=False),
        schema="recruiting",
    )
    op.create_table(
        "offer",
        sa.Column("offer_id", sa.Uuid(), primary_key=True),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("supersedes", sa.Uuid(), nullable=True),
        sa.Column("base_annual", sa.Numeric(12, 2), nullable=False),  # T2
        sa.Column("currency", sa.Text(), nullable=False),
        sa.Column("components", JSONB(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("requires_comp_approval", sa.Boolean(), nullable=False),
        sa.Column("rescind_reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        schema="recruiting",
    )


def downgrade() -> None:
    for table in ("offer", "application", "requisition", "candidate_profile"):
        op.execute(f"DROP TABLE IF EXISTS recruiting.{table}")
    op.execute("DROP SCHEMA IF EXISTS recruiting")
