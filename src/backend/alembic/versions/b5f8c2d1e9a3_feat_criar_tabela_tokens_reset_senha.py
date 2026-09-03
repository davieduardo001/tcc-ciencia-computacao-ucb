"""feat: criar tabela tokens_reset_senha

Revision ID: b5f8c2d1e9a3
Revises: ad383a6ffdcf
Create Date: 2026-09-03 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b5f8c2d1e9a3'
down_revision: Union[str, None] = 'ad383a6ffdcf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tokens_reset_senha',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('usuario_id', sa.Uuid(), nullable=False),
    sa.Column('token', sa.String(length=255), nullable=False),
    sa.Column('usado', sa.Boolean(), nullable=False),
    sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expira_em', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token')
    )


def downgrade() -> None:
    op.drop_table('tokens_reset_senha')
