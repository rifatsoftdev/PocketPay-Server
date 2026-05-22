"""allow google users without country code

Revision ID: 8c2d4f9b7a31
Revises: 17e7d69603d8
Create Date: 2026-05-22 12:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8c2d4f9b7a31"
down_revision: Union[str, Sequence[str], None] = "17e7d69603d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow users created from Google login to exist before phone setup."""
    op.alter_column(
        "user_list",
        "country_code",
        existing_type=sa.String(length=4),
        nullable=True,
    )


def downgrade() -> None:
    """Restore country_code as required."""
    op.alter_column(
        "user_list",
        "country_code",
        existing_type=sa.String(length=4),
        nullable=False,
    )
