"""Workflow engine durable state (Specs/12 §2).

Revision ID: 0002
Revises: 0001
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS workflow")
    op.create_table(
        "workflow_instance",
        sa.Column("instance_id", sa.Uuid(), primary_key=True),
        sa.Column("definition_key", sa.Text(), nullable=False),
        sa.Column("definition_version", sa.Integer(), nullable=False),
        sa.Column("subject_ref", sa.Text(), nullable=False),
        sa.Column("initiator", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("current_step_index", sa.Integer(), nullable=False),
        sa.Column("payload", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        schema="workflow",
    )
    op.create_table(
        "step_execution",
        sa.Column("execution_id", sa.Uuid(), primary_key=True),
        sa.Column("instance_id", sa.Uuid(), nullable=False),
        sa.Column("step_id", sa.Text(), nullable=False),
        sa.Column("step_type", sa.Text(), nullable=False),
        sa.Column("resolved_assignee", sa.Text(), nullable=True),
        sa.Column("resolution_reason", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("acted_by", sa.Text(), nullable=True),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=True),
        schema="workflow",
    )
    op.create_index("ix_step_execution_instance", "step_execution", ["instance_id"], schema="workflow")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS workflow.step_execution")
    op.execute("DROP TABLE IF EXISTS workflow.workflow_instance")
    op.execute("DROP SCHEMA IF EXISTS workflow")
