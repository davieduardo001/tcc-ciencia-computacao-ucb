"""feat: criar tabela alertas_proximidade (US #172 - alerta de proximidade da parada)

Revision ID: d6e7f8a9b0c1
Revises: a2b3c4d5e6f7
Create Date: 2026-10-07 00:00:00.000000

Migration só aditiva: nada existente é alterado ou apagado. Homolog e
produção compartilham banco (issue #42), então esta migration roda em
produção assim que o deploy de homolog sobe.

O índice único (viagem_id, parada_destino_codigo) é o que garante o
Cenário 2 da US #172 no banco: mesmo com dois ciclos do worker rodando
ao mesmo tempo, só existe um alerta por parada por viagem.

Nota de cadeia: revisa a2b3c4d5e6f7 (cabeça do homolog no momento).
O PR #177 (US #173) também revisa a2b3c4d5e6f7 — se ele mergear primeiro,
reencadear esta migration para c4d5e6f7a8b9 antes do merge desta, para
não deixar duas cabeças na cadeia.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd6e7f8a9b0c1'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'alertas_proximidade',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('usuario_id', sa.Uuid(), nullable=False),
        sa.Column('viagem_id', sa.String(length=64), nullable=False),
        sa.Column('linha_id', sa.String(length=20), nullable=False),
        sa.Column('parada_destino_codigo', sa.String(length=12), nullable=False),
        sa.Column('parada_destino_nome', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('eta_minutos', sa.Float(), nullable=True),
        sa.Column('disparado_em', sa.DateTime(), nullable=False),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_alertas_proximidade_usuario_id',
        'alertas_proximidade',
        ['usuario_id'],
    )
    op.create_index(
        'uq_alerta_proximidade_viagem_parada',
        'alertas_proximidade',
        ['viagem_id', 'parada_destino_codigo'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('uq_alerta_proximidade_viagem_parada', table_name='alertas_proximidade')
    op.drop_index('ix_alertas_proximidade_usuario_id', table_name='alertas_proximidade')
    op.drop_table('alertas_proximidade')
