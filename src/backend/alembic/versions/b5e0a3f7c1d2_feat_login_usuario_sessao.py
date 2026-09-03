"""feat: adicionar colunas login e tabela sessao

Revision ID: b5e0a3f7c1d2
Revises: ad383a6ffdcf
Create Date: 2026-09-03 20:51:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b5e0a3f7c1d2'
down_revision: Union[str, None] = 'ad383a6ffdcf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('status', sa.String(length=50), nullable=True))
    op.add_column('usuarios', sa.Column('tentativas_falhas', sa.Integer(), nullable=True))
    op.add_column('usuarios', sa.Column('bloqueado_ate', sa.DateTime(), nullable=True))

    op.create_table('sessoes',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('usuario_id', sa.Uuid(), nullable=False),
    sa.Column('access_token', sa.String(length=500), nullable=False),
    sa.Column('refresh_token', sa.String(length=500), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('sessoes')
    op.drop_column('usuarios', 'bloqueado_ate')
    op.drop_column('usuarios', 'tentativas_falhas')
    op.drop_column('usuarios', 'status')