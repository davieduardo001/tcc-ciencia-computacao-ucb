"""feat: criar tabelas parada e rota_parada (US #173 - mapeamento entre paradas)

Revision ID: c4d5e6f7a8b9
Revises: a2b3c4d5e6f7
Create Date: 2026-10-06 00:00:00.000000

Migration só aditiva: nada existente é alterado ou apagado. Homolog e
produção compartilham banco (issue #42), então esta migration roda em
produção assim que o deploy de homolog sobe.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'parada',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('codigo', sa.String(length=12), nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo'),
    )
    op.create_index('ix_parada_lat_lng', 'parada', ['lat', 'lng'])

    op.create_table(
        'rota_parada',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('numero', sa.String(length=20), nullable=False),
        sa.Column('sentido', sa.String(length=20), nullable=False),
        sa.Column('parada_id', sa.Integer(), nullable=False),
        sa.Column('ordem', sa.Integer(), nullable=False),
        sa.Column('indice_trajeto', sa.Integer(), nullable=False),
        sa.Column('distancia_acumulada_m', sa.Float(), nullable=False),
        sa.Column('distancia_ao_trajeto_m', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['parada_id'], ['parada.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('numero', 'sentido', 'parada_id', name='uq_rota_parada'),
    )
    op.create_index('ix_rota_parada_rota', 'rota_parada', ['numero', 'sentido'])
    op.create_index('ix_rota_parada_parada', 'rota_parada', ['parada_id'])

    # Horário por dia da semana e duração da viagem, por linha × sentido.
    op.add_column('rota', sa.Column('horarios_por_dia', sa.JSON(), nullable=True))
    op.add_column('rota', sa.Column('tempo_percurso_min', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('rota', 'tempo_percurso_min')
    op.drop_column('rota', 'horarios_por_dia')
    op.drop_index('ix_rota_parada_parada', table_name='rota_parada')
    op.drop_index('ix_rota_parada_rota', table_name='rota_parada')
    op.drop_table('rota_parada')
    op.drop_index('ix_parada_lat_lng', table_name='parada')
    op.drop_table('parada')
