"""feat: adicionar account_linking_pending ao modelo Usuario

Revision ID: a1b2c3d4e5f6
Revises: 9b3c4d5e6f7a
Create Date: 2026-09-06 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9b3c4d5e6f7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('account_linking_pending', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('usuarios', 'account_linking_pending')
