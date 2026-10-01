"""feat: criar tabela ocorrencia

Revision ID: 09bed28051ec
Revises: d5e6f7a8b9c0
Create Date: 2026-10-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '09bed28051ec'
down_revision: Union[str, None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('ocorrencia',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('usuario_id', sa.Uuid(), nullable=False),
    sa.Column('linha_numero', sa.String(length=20), nullable=False),
    sa.Column('tipo', sa.String(length=20), nullable=False),
    sa.Column('descricao', sa.String(length=500), nullable=True),
    sa.Column('local', sa.String(length=255), nullable=True),
    sa.Column('lat', sa.Float(), nullable=True),
    sa.Column('lng', sa.Float(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('contador_confirmacoes', sa.Integer(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), nullable=False),
    sa.Column('expira_em', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ocorrencia_usuario_id'), 'ocorrencia', ['usuario_id'], unique=False)
    op.create_index(op.f('ix_ocorrencia_linha_numero'), 'ocorrencia', ['linha_numero'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ocorrencia_linha_numero'), table_name='ocorrencia')
    op.drop_index(op.f('ix_ocorrencia_usuario_id'), table_name='ocorrencia')
    op.drop_table('ocorrencia')
