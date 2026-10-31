"""feat: criar tabela alertas_cancelamento (US #28 - alerta de cancelamento de viagem)

Revision ID: c7d8e9f0a1b2
Revises: b1c2d3e4f5a6
Create Date: 2026-10-29 00:00:00.000000

Migration só aditiva: nada existente é alterado ou apagado. Homolog e
produção compartilham banco (issue #42), então esta migration roda em
produção assim que o deploy de homolog sobe.

O índice único (numero_linha, horario_partida) é o que garante o Cenário 3
da US #28 no banco: mesmo com dois ciclos do worker rodando ao mesmo
tempo, só existe um alerta por partida prevista de cada linha.

Nota de cadeia: revisa b1c2d3e4f5a6 (cabeça do homolog no momento). Se
outra migration nascer da mesma cabeça antes do merge, reencadear aqui
para não deixar duas cabeças na cadeia.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'alertas_cancelamento',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('numero_linha', sa.String(length=20), nullable=False),
        sa.Column('horario_partida', sa.String(length=5), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('alternativa_numero', sa.String(length=20), nullable=True),
        sa.Column('detectado_em', sa.DateTime(), nullable=False),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'uq_alerta_cancelamento_linha_horario',
        'alertas_cancelamento',
        ['numero_linha', 'horario_partida'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('uq_alerta_cancelamento_linha_horario', table_name='alertas_cancelamento')
    op.drop_table('alertas_cancelamento')
