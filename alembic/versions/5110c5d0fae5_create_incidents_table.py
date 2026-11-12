"""Create the incidents table.

Revision ID: 5110c5d0fae5
Revises:
Create Date: 2026-09-28 19:15:31.986930
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5110c5d0fae5"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create incidents table."""

    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_name", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("investigation_state", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_incidents_id"),
        "incidents",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop incidents table."""

    op.drop_index(
        op.f("ix_incidents_id"),
        table_name="incidents",
    )

    op.drop_table("incidents")