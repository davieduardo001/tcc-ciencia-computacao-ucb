"""feat: adicionar provider e google_id ao modelo Usuario

Revision ID: 8f4a2b1c3d5e
Revises: c7d9e1f2a3b4
Create Date: 2026-09-05 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8f4a2b1c3d5e'
down_revision: Union[str, None] = 'c7d9e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('provider', sa.String(length=50), nullable=True))
    op.add_column('usuarios', sa.Column('google_id', sa.String(length=255), nullable=True))
    op.alter_column('usuarios', 'senha_hash', nullable=True)


def downgrade() -> None:
    op.alter_column('usuarios', 'senha_hash', nullable=False)
    op.drop_column('usuarios', 'google_id')
    op.drop_column('usuarios', 'provider')