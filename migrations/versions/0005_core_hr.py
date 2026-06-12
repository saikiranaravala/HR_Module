"""Core HR schema (Specs/01): person, names, IDs, workers, assignments, org.

Revision ID: 0005
Revises: 0004
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

TEMPORAL_COLS = lambda: [  # noqa: E731 — shared shape for temporal tables
    sa.Column("effective_date", sa.Date(), primary_key=True),
    sa.Column("effective_sequence", sa.SmallInteger(), primary_key=True),
    sa.Column("action_code", sa.Text(), nullable=False),
    sa.Column("action_reason", sa.Text(), nullable=True),
    sa.Column("created_by", sa.Text(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column("source_channel", sa.Text(), nullable=False),
    sa.Column("correlation_id", sa.Uuid(), nullable=False),
]


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    op.create_table(
        "person",
        sa.Column("person_id", sa.Uuid(), primary_key=True),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("primary_nationality", sa.Text(), nullable=True),
        schema="core",
    )
    op.create_table(
        "person_name",
        sa.Column("person_id", sa.Uuid(), primary_key=True),
        *TEMPORAL_COLS(),
        sa.Column("given_name", sa.Text(), nullable=False),
        sa.Column("family_name", sa.Text(), nullable=False),
        sa.Column("formatted_name", sa.Text(), nullable=False),
        sa.Column("legal_doc_verified", sa.Boolean(), nullable=False),
        schema="core",
    )
    op.create_table(
        "national_id",
        sa.Column("national_id_pk", sa.Uuid(), primary_key=True),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("id_type", sa.Text(), nullable=False),
        sa.Column("value_encrypted", sa.Text(), nullable=False),
        sa.Column("last_four", sa.Text(), nullable=False),
        schema="core",
    )
    op.create_table(
        "work_eligibility",
        sa.Column("eligibility_id", sa.Uuid(), primary_key=True),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("document_type", sa.Text(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        schema="core",
    )
    op.create_table(
        "worker",
        sa.Column("worker_id", sa.Uuid(), primary_key=True),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("legal_entity", sa.Text(), nullable=False),
        sa.Column("entity_country", sa.Text(), nullable=False),
        sa.Column("worker_type", sa.Text(), nullable=False),
        sa.Column("hire_date", sa.Date(), nullable=False),
        sa.Column("original_hire_date", sa.Date(), nullable=False),
        sa.Column("carried_flags", sa.Text(), nullable=True),
        schema="core",
    )
    op.create_table(
        "assignment",
        sa.Column("worker_id", sa.Uuid(), primary_key=True),
        *TEMPORAL_COLS(),
        sa.Column("worker_status", sa.Text(), nullable=False),
        sa.Column("job_code", sa.Text(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=True),
        sa.Column("position_id", sa.Uuid(), nullable=True),
        sa.Column("manager_worker_id", sa.Uuid(), nullable=True),
        sa.Column("location_country", sa.Text(), nullable=False),
        sa.Column("fte", sa.Numeric(4, 2), nullable=False),
        sa.Column("pay_group", sa.Text(), nullable=True),
        schema="core",
    )
    op.create_table(
        "department",
        sa.Column("department_id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        schema="core",
    )
    op.create_table(
        "position",
        sa.Column("position_id", sa.Uuid(), primary_key=True),
        sa.Column("job_code", sa.Text(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column("headcount_budget", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        schema="core",
    )
    for table in ("person_name", "assignment"):
        op.execute(
            f"""
            CREATE TRIGGER immutable_core_{table}
                BEFORE UPDATE OR DELETE ON core.{table}
                FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();
            """
        )


def downgrade() -> None:
    for table in ("position", "department", "assignment", "worker",
                  "work_eligibility", "national_id", "person_name", "person"):
        op.execute(f"DROP TABLE IF EXISTS core.{table}")
    op.execute("DROP SCHEMA IF EXISTS core")
