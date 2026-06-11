"""Platform foundation: audit_event, policy_decision_log, immutability guards.

Requirement IDs: TECH-5 (decision log), TECH-6 (hash-chained audit).
Catalog tags for these tables live in the model definitions
(platform_core.audit / platform_core.policy.engine) and surface through the
records-of-processing endpoint.

Revision ID: 0001
Revises:
Create Date: 2026-06-10
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS platform")

    op.create_table(
        "audit_event",
        sa.Column("audit_id", sa.Uuid(), primary_key=True),
        sa.Column("seq", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("on_behalf_of", sa.Text(), nullable=True),
        sa.Column("actor_type", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_ref", sa.Text(), nullable=False),
        sa.Column("before", JSONB(), nullable=True),
        sa.Column("after", JSONB(), nullable=True),
        sa.Column("sensitivity_tier", sa.Text(), nullable=False),
        sa.Column("source_channel", sa.Text(), nullable=False),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("prev_hash", sa.Text(), nullable=False),
        sa.Column("row_hash", sa.Text(), nullable=False),
        schema="platform",
    )
    op.create_index("ix_audit_event_entity_ref", "audit_event", ["entity_ref"], schema="platform")

    op.create_table(
        "policy_decision_log",
        sa.Column("decision_id", sa.Uuid(), primary_key=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("subject_id", sa.Text(), nullable=False),
        sa.Column("capability", sa.Text(), nullable=False),
        sa.Column("resource_ref", sa.Text(), nullable=True),
        sa.Column("allow", sa.Boolean(), nullable=False),
        sa.Column("reasons", sa.Text(), nullable=False),
        sa.Column("policy_version", sa.Text(), nullable=False),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        schema="platform",
    )

    # Append-only enforcement (TECH-6): UPDATE/DELETE blocked at the database.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION platform.forbid_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'rows in %.% are immutable (temporal/audit pattern): % denied',
                TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER immutable_platform_audit_event
            BEFORE UPDATE OR DELETE ON platform.audit_event
            FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS platform.policy_decision_log")
    op.execute("DROP TABLE IF EXISTS platform.audit_event")
    op.execute("DROP FUNCTION IF EXISTS platform.forbid_mutation() CASCADE")
    op.execute("DROP SCHEMA IF EXISTS platform")
