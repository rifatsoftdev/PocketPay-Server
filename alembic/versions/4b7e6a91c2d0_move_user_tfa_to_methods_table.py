"""move user tfa to methods table

Revision ID: 4b7e6a91c2d0
Revises: 8c2d4f9b7a31
Create Date: 2026-05-22 12:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4b7e6a91c2d0"
down_revision: Union[str, Sequence[str], None] = "8c2d4f9b7a31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Copy existing user_settings TFA data into two_factor_methods and drop old columns."""
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        op.execute(
            """
            INSERT INTO two_factor_methods
                (user_id, method_type, is_enabled, is_primary, delivery_address, secret_key, created_at, updated_at)
            SELECT
                user_id,
                'TOTP',
                COALESCE(two_factor_enabled, false),
                COALESCE(two_factor_enabled, false),
                NULL,
                COALESCE(two_factor ->> 'totp', two_factor ->> 'secret'),
                NOW(),
                NOW()
            FROM user_settings
            WHERE two_factor IS NOT NULL
              AND COALESCE(two_factor ->> 'totp', two_factor ->> 'secret') IS NOT NULL
            ON CONFLICT (user_id, method_type) DO UPDATE SET
                is_enabled = EXCLUDED.is_enabled,
                is_primary = EXCLUDED.is_primary,
                secret_key = EXCLUDED.secret_key,
                updated_at = NOW()
            """
        )
        op.execute(
            """
            INSERT INTO two_factor_methods
                (user_id, method_type, is_enabled, is_primary, delivery_address, secret_key, created_at, updated_at)
            SELECT
                user_id,
                'EMAIL',
                COALESCE(two_factor_enabled, false),
                false,
                two_factor ->> 'email',
                NULL,
                NOW(),
                NOW()
            FROM user_settings
            WHERE two_factor IS NOT NULL
              AND two_factor ->> 'email' IS NOT NULL
            ON CONFLICT (user_id, method_type) DO UPDATE SET
                is_enabled = EXCLUDED.is_enabled,
                delivery_address = EXCLUDED.delivery_address,
                updated_at = NOW()
            """
        )

    op.drop_column("user_settings", "two_factor")
    op.drop_column("user_settings", "two_factor_enabled")


def downgrade() -> None:
    """Restore legacy user_settings TFA columns."""
    op.add_column(
        "user_settings",
        sa.Column("two_factor_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("user_settings", sa.Column("two_factor", sa.JSON(), nullable=True))
    op.alter_column("user_settings", "two_factor_enabled", server_default=None)
