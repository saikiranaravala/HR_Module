"""Migration-program schema (Specs/16): staging, DQ queue, gate artifacts,
sync conflicts.

Revision ID: 0016
Revises: 0015
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS migration")
    op.create_table(
        "staged_record",
        sa.Column("staged_id", sa.Uuid(), primary_key=True),
        sa.Column("batch_id", sa.Text(), nullable=False),
        sa.Column("source_key", sa.Text(), nullable=False),
        sa.Column("domain", sa.Text(), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("loaded", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("batch_id", "domain", "source_key",
                            name="uq_staged_idempotency"),
        schema="migration",
    )
    op.create_table(
        "dq_exception",
        sa.Column("exception_id", sa.Uuid(), primary_key=True),
        sa.Column("batch_id", sa.Text(), nullable=False),
        sa.Column("domain", sa.Text(), nullable=False),
        sa.Column("rule", sa.Text(), nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=False),
        sa.Column("guidance", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        schema="migration",
    )
    op.create_table(
        "gate_artifact",
        sa.Column("artifact_id", sa.Uuid(), primary_key=True),
        sa.Column("wave", sa.Text(), nullable=False),
        sa.Column("gate", sa.Text(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("report", JSONB(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("signed_by", sa.Text(), nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        schema="migration",
    )
    op.create_table(
        "sync_conflict",
        sa.Column("conflict_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_ref", sa.Text(), nullable=False),
        sa.Column("field", sa.Text(), nullable=False),
        sa.Column("ps_value", sa.Text(), nullable=True),
        sa.Column("meridian_value", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("resolution", sa.Text(), nullable=True),
        schema="migration",
    )
    # Gate artifacts are the program's audit trail: immutable.
    op.execute("""
        CREATE TRIGGER immutable_migration_gate_artifact
            BEFORE UPDATE OR DELETE ON migration.gate_artifact
            FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();
    """)


def downgrade() -> None:
    for table in ("sync_conflict", "gate_artifact", "dq_exception", "staged_record"):
        op.execute(f"DROP TABLE IF EXISTS migration.{table}")
    op.execute("DROP SCHEMA IF EXISTS migration")
