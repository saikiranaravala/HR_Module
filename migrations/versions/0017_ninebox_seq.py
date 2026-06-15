"""Add monotonic seq column to ninebox_placement for stable insertion-order
sorting. placed_at is set in Python (datetime.now) and has ~15 ms resolution
on Windows — two rapid placements in the same test can share a timestamp,
making ORDER BY placed_at non-deterministic.

Revision ID: 0017
Revises: 0016
"""
import sqlalchemy as sa
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ninebox_placement",
        sa.Column("seq", sa.Integer(), sa.Identity(always=True), nullable=False),
        schema="succession",
    )


def downgrade() -> None:
    op.drop_column("ninebox_placement", "seq", schema="succession")
