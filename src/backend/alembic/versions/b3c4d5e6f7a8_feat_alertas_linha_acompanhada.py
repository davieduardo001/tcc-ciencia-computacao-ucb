"""feat: criar tabelas linhas_acompanhadas e alertas para US #27

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-09-26 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('linhas_acompanhadas',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('usuario_id', sa.Uuid(), nullable=False, index=True),
        sa.Column('linha_id', sa.String(length=20), nullable=False, index=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.Column('ativo', sa.Integer(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'uq_linha_acompanhada_ativa',
        'linhas_acompanhadas',
        ['usuario_id', 'linha_id'],
        unique=True,
        postgresql_where=sa.text('ativo = 1'),
    )

    op.create_table('alertas',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('usuario_id', sa.Uuid(), nullable=False, index=True),
        sa.Column('linha_id', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('atraso_inicio_minutos', sa.Float(), nullable=False),
        sa.Column('ultimo_atraso_notificado', sa.Float(), nullable=True),
        sa.Column('ultimo_alerta_enviado_em', sa.DateTime(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.Column('cancelado_em', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'uq_alerta_ativo_unico',
        'alertas',
        ['usuario_id', 'linha_id'],
        unique=True,
        postgresql_where=sa.text("status = 'ativo'"),
    )


def downgrade() -> None:
    op.drop_index('uq_alerta_ativo_unico', table_name='alertas')
    op.drop_index('uq_linha_acompanhada_ativa', table_name='linhas_acompanhadas')
    op.drop_table('alertas')
    op.drop_table('linhas_acompanhadas')
