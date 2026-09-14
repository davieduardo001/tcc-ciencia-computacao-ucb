"""feat: criar tabela linha (US #15 - Buscar Linha por Numero)

Revision ID: d3f8a91c2b60
Revises: a1b2c3d4e5f6
Create Date: 2026-09-12 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd3f8a91c2b60'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('linha',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('numero', sa.String(length=20), nullable=False),
    sa.Column('nome', sa.String(length=255), nullable=False),
    sa.Column('sentido', sa.String(length=255), nullable=False),
    sa.Column('paradas', sa.JSON(), nullable=False),
    sa.Column('trajeto', sa.JSON(), nullable=False),
    sa.Column('horarios_previstos', sa.JSON(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('numero')
    )
    op.create_index(op.f('ix_linha_numero'), 'linha', ['numero'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_linha_numero'), table_name='linha')
    op.drop_table('linha')
