"""make user role nullable

Revision ID: 7174f58d69cf
Revises: 0a5afedd2e2d
Create Date: 2026-10-11 00:13:18.507553

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '7174f58d69cf'
down_revision: str | None = '0a5afedd2e2d'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # batch_alter_table: a plain ALTER COLUMN on Postgres, a table-recreate on
    # SQLite (which can't ALTER COLUMN directly) - needed for local sqlite use.
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "role",
            existing_type=sa.VARCHAR(length=6),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "role",
            existing_type=sa.VARCHAR(length=6),
            nullable=False,
        )
