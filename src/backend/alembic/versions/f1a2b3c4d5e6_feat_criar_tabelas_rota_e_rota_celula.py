"""feat: criar tabelas rota e rota_celula (US #20 - Rota Origem->Destino)

Revision ID: f1a2b3c4d5e6
Revises: e4c7b52f9a10
Create Date: 2026-09-13 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e4c7b52f9a10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'rota',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('numero', sa.String(length=20), nullable=False),
        sa.Column('sentido', sa.String(length=20), nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('trajeto', sa.JSON(), nullable=False),
        sa.Column('paradas', sa.JSON(), nullable=False),
        sa.Column(
            'atualizado_em',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('numero', 'sentido', name='uq_rota_numero_sentido'),
    )
    op.create_index(op.f('ix_rota_numero'), 'rota', ['numero'], unique=False)

    op.create_table(
        'rota_celula',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('numero', sa.String(length=20), nullable=False),
        sa.Column('sentido', sa.String(length=20), nullable=False),
        sa.Column('cel_lat', sa.Integer(), nullable=False),
        sa.Column('cel_lng', sa.Integer(), nullable=False),
        sa.Column('indice_min', sa.Integer(), nullable=False),
        sa.Column('indice_max', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_rota_celula_grade', 'rota_celula', ['cel_lat', 'cel_lng'], unique=False
    )
    op.create_index(
        'ix_rota_celula_rota', 'rota_celula', ['numero', 'sentido'], unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_rota_celula_rota', table_name='rota_celula')
    op.drop_index('ix_rota_celula_grade', table_name='rota_celula')
    op.drop_table('rota_celula')
    op.drop_index(op.f('ix_rota_numero'), table_name='rota')
    op.drop_table('rota')
