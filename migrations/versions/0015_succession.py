"""Succession schema (Specs/09): key positions, slates, talent profiles,
9-box lineage, discovery holds.

Revision ID: 0015
Revises: 0014
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS succession")
    op.create_table(
        "key_position",
        sa.Column("position_id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("incumbent_id", sa.Text(), nullable=True),
        sa.Column("division_path", sa.Text(), nullable=False),
        sa.Column("criticality", JSONB(), nullable=False),
        sa.Column("retirement_band", sa.Text(), nullable=True),  # band, never date
        schema="succession",
    )
    op.create_table(
        "slate_entry",
        sa.Column("entry_id", sa.Uuid(), primary_key=True),
        sa.Column("position_id", sa.Uuid(), nullable=False),
        sa.Column("successor_id", sa.Text(), nullable=False),
        sa.Column("readiness", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("emergency", sa.Boolean(), nullable=False),
        sa.Column("development_plan_ref", sa.Text(), nullable=True),
        sa.Column("last_validated", sa.Date(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        schema="succession",
    )
    op.create_table(
        "talent_profile",
        sa.Column("profile_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("aspirations", sa.Text(), nullable=True),
        sa.Column("aspirations_consent", sa.Boolean(), nullable=False),
        sa.Column("mobility_prefs", JSONB(), nullable=True),
        sa.Column("experiences", JSONB(), nullable=True),
        sa.Column("interim", sa.Boolean(), nullable=False),
        sa.Column("history_note", sa.Text(), nullable=True),
        schema="succession",
    )
    op.create_table(
        "ninebox_placement",
        sa.Column("placement_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("session_id", sa.Text(), nullable=False),
        sa.Column("performance", sa.Text(), nullable=False),
        sa.Column("potential", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),  # mandatory
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("placed_at", sa.DateTime(timezone=True), nullable=False),
        schema="succession",
    )
    op.create_table(
        "discovery_hold",
        sa.Column("hold_id", sa.Uuid(), primary_key=True),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("requested_by", sa.Text(), nullable=False),
        sa.Column("counsel", sa.Text(), nullable=False),
        sa.Column("privileged", sa.Boolean(), nullable=False),
        sa.Column("counsel_approved", sa.Boolean(), nullable=False),
        sa.Column("released", sa.Boolean(), nullable=False),
        sa.Column("artifact_refs", JSONB(), nullable=True),
        schema="succession",
    )
    # 9-box lineage is append-only at the database level.
    op.execute("""
        CREATE TRIGGER immutable_succession_ninebox_placement
            BEFORE UPDATE OR DELETE ON succession.ninebox_placement
            FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();
    """)


def downgrade() -> None:
    for table in ("discovery_hold", "ninebox_placement", "talent_profile",
                  "slate_entry", "key_position"):
        op.execute(f"DROP TABLE IF EXISTS succession.{table}")
    op.execute("DROP SCHEMA IF EXISTS succession")
