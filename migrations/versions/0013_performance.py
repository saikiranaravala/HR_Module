"""Performance schema (Specs/07): goals, cycles, review docs, calibration
lineage, check-ins, feedback.

Revision ID: 0013
Revises: 0012
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS performance")
    op.create_table(
        "goal",
        sa.Column("goal_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("goal_type", sa.Text(), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.Column("parent_goal_id", sa.Uuid(), nullable=True),
        sa.Column("visibility", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("supersedes", sa.Uuid(), nullable=True),
        schema="performance",
    )
    op.create_table(
        "review_cycle",
        sa.Column("cycle_id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("template_key", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("launched_on", sa.Date(), nullable=False),
        sa.Column("window_end", sa.Date(), nullable=False),
        schema="performance",
    )
    op.create_table(
        "review_doc",
        sa.Column("doc_id", sa.Uuid(), primary_key=True),
        sa.Column("cycle_id", sa.Uuid(), nullable=False),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("manager_id", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("rating", sa.Text(), nullable=True),  # nullable: ratingless
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("self_assessment", sa.Text(), nullable=True),
        sa.Column("ai_drafted", sa.Boolean(), nullable=False),
        sa.Column("ai_draft_edited", sa.Boolean(), nullable=False),
        sa.Column("prorated", sa.Boolean(), nullable=False),
        sa.Column("extension_until", sa.Date(), nullable=True),
        sa.Column("restricted", sa.Boolean(), nullable=False),  # PIP T3
        sa.Column("amends", sa.Uuid(), nullable=True),  # dual-record amendment
        sa.Column("amendment_reason", sa.Text(), nullable=True),
        sa.Column("skip_level_disagreement", sa.Text(), nullable=True),
        sa.Column("acknowledged_comment", sa.Text(), nullable=True),
        sa.Column("closeout_reason", sa.Text(), nullable=True),
        sa.Column("handoff_log", JSONB(), nullable=True),
        schema="performance",
    )
    op.create_table(
        "calibration_adjustment",
        sa.Column("adjustment_id", sa.Uuid(), primary_key=True),
        sa.Column("doc_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Text(), nullable=False),
        sa.Column("before_rating", sa.Text(), nullable=True),
        sa.Column("after_rating", sa.Text(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),  # mandatory
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("adjusted_at", sa.DateTime(timezone=True), nullable=False),
        schema="performance",
    )
    op.create_table(
        "checkin",
        sa.Column("checkin_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("manager_id", sa.Text(), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("shared_notes", sa.Text(), nullable=True),
        sa.Column("private_notes", sa.Text(), nullable=True),
        sa.Column("private_notes_author", sa.Text(), nullable=True),
        schema="performance",
    )
    op.create_table(
        "feedback",
        sa.Column("feedback_id", sa.Uuid(), primary_key=True),
        sa.Column("author_id", sa.Text(), nullable=False),
        sa.Column("subject_id", sa.Text(), nullable=False),
        sa.Column("visibility", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("competency", sa.Text(), nullable=True),
        sa.Column("campaign_id", sa.Text(), nullable=True),
        sa.Column("given_on", sa.Date(), nullable=False),
        schema="performance",
    )
    # Calibration lineage is append-only at the database level.
    op.execute("""
        CREATE TRIGGER immutable_performance_calibration_adjustment
            BEFORE UPDATE OR DELETE ON performance.calibration_adjustment
            FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();
    """)


def downgrade() -> None:
    for table in ("feedback", "checkin", "calibration_adjustment",
                  "review_doc", "review_cycle", "goal"):
        op.execute(f"DROP TABLE IF EXISTS performance.{table}")
    op.execute("DROP SCHEMA IF EXISTS performance")
