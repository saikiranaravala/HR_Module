"""Learning schema (Specs/08): content, assignments, completion evidence, certs.

Revision ID: 0014
Revises: 0013
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS learning")
    op.create_table(
        "content_item",
        sa.Column("content_id", sa.Uuid(), primary_key=True),
        sa.Column("content_key", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("supersede_policy", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        schema="learning",
    )
    op.create_table(
        "assignment",
        sa.Column("assignment_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("requirement_key", sa.Text(), nullable=False),
        sa.Column("content_key", sa.Text(), nullable=False),
        sa.Column("content_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column("paused_on", sa.Date(), nullable=True),
        sa.Column("pause_log", JSONB(), nullable=True),
        sa.Column("extension_note", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("suspend_data", sa.Text(), nullable=True),
        sa.Column("suspend_checksum", sa.Text(), nullable=True),
        sa.Column("lightweight", sa.Boolean(), nullable=False),
        schema="learning",
    )
    op.create_table(
        "completion_record",
        sa.Column("completion_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("requirement_key", sa.Text(), nullable=True),
        sa.Column("content_key", sa.Text(), nullable=False),
        sa.Column("content_version", sa.Integer(), nullable=False),  # pinned
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("evidence_ref", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.Text(), nullable=True),
        schema="learning",
    )
    op.create_table(
        "certification",
        sa.Column("certification_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("cert_type", sa.Text(), nullable=False),
        sa.Column("issuer", sa.Text(), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("evidence_ref", sa.Text(), nullable=True),
        sa.Column("job_required", sa.Boolean(), nullable=False),
        schema="learning",
    )
    # Completion evidence is audit-grade: immutable at the database level.
    op.execute("""
        CREATE TRIGGER immutable_learning_completion_record
            BEFORE UPDATE OR DELETE ON learning.completion_record
            FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();
    """)


def downgrade() -> None:
    for table in ("certification", "completion_record", "assignment", "content_item"):
        op.execute(f"DROP TABLE IF EXISTS learning.{table}")
    op.execute("DROP SCHEMA IF EXISTS learning")
