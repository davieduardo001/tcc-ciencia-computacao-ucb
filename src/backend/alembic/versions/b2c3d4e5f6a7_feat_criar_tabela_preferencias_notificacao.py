"""feat: criar tabela preferencias_notificacao

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-07 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('preferencias_notificacao',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('usuario_id', sa.Uuid(), nullable=False),
    sa.Column('antecedencia_minutos', sa.Integer(), nullable=False),
    sa.Column('notificacoes_ativas', sa.Boolean(), nullable=False),
    sa.Column('alerta_chegada', sa.Boolean(), nullable=False),
    sa.Column('alerta_cancelamento', sa.Boolean(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('usuario_id')
    )


def downgrade() -> None:
    op.drop_table('preferencias_notificacao')
