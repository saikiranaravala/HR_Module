"""ESS/MSS + HR service delivery schema (Specs/10): cases, KB, delegations,
notification prefs, access grants.

Revision ID: 0009
Revises: 0008
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS service_delivery")
    op.create_table(
        "case",
        sa.Column("case_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("queue", sa.Text(), nullable=False),
        sa.Column("priority", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),  # T3 when queue=er
        sa.Column("transcript", JSONB(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("satisfaction", sa.Integer(), nullable=True),
        schema="service_delivery",
    )
    op.create_table(
        "case_note",
        sa.Column("note_id", sa.Uuid(), primary_key=True),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("visibility", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="service_delivery",
    )
    op.create_table(
        "kb_article",
        sa.Column("article_id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("population", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("is_policy", sa.Boolean(), nullable=False),
        sa.Column("published_on", sa.Date(), nullable=True),
        sa.Column("review_due", sa.Date(), nullable=True),
        schema="service_delivery",
    )
    op.create_table(
        "delegation",
        sa.Column("delegation_id", sa.Uuid(), primary_key=True),
        sa.Column("delegator", sa.Text(), nullable=False),
        sa.Column("delegate", sa.Text(), nullable=False),
        sa.Column("scope_types", JSONB(), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        schema="service_delivery",
    )
    op.create_table(
        "notification_pref",
        sa.Column("pref_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("notif_type", sa.Text(), nullable=True),
        sa.Column("channels", JSONB(), nullable=True),
        sa.Column("quiet_start", sa.Integer(), nullable=True),
        sa.Column("quiet_end", sa.Integer(), nullable=True),
        sa.Column("personal_channel_consent", sa.Boolean(), nullable=False),
        schema="service_delivery",
    )
    op.create_table(
        "access_grant",
        sa.Column("grant_id", sa.Uuid(), primary_key=True),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("scope", JSONB(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("released", sa.Boolean(), nullable=False),
        schema="service_delivery",
    )


def downgrade() -> None:
    for table in ("access_grant", "notification_pref", "delegation",
                  "kb_article", "case_note", "case"):
        op.execute(f'DROP TABLE IF EXISTS service_delivery."{table}"')
    op.execute("DROP SCHEMA IF EXISTS service_delivery")
