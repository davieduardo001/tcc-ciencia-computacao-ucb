"""feat: adicionar avatar_url ao modelo Usuario

Revision ID: 9b3c4d5e6f7a
Revises: 8f4a2b1c3d5e
Create Date: 2026-09-06 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9b3c4d5e6f7a'
down_revision: Union[str, None] = '8f4a2b1c3d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('avatar_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('usuarios', 'avatar_url')
