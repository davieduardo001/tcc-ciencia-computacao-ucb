"""feat: criar tabela viagem (US #171 - pegar o onibus)

Revision ID: e5f6a7b8c9d0
Revises: c4d5e6f7a8b9
Create Date: 2026-10-14 00:00:00.000000

Migration só aditiva: nada existente é alterado ou apagado. Homolog e
produção compartilham banco (issue #42), então esta migration roda em
produção assim que o deploy de homolog sobe.

O índice único parcial (usuario_id WHERE encerrada_em IS NULL) garante no
banco que cada usuário tem no máximo uma viagem ativa, mesmo com dois
toques simultâneos em "Peguei este ônibus".

Não há coluna de latitude/longitude de propósito (LGPD, RN-06 da #171).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'viagem',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('usuario_id', sa.Uuid(), nullable=False),
        sa.Column('numero_linha', sa.String(length=20), nullable=False),
        sa.Column('sentido', sa.String(length=20), nullable=True),
        sa.Column('veiculo_prefixo', sa.String(length=40), nullable=False),
        sa.Column('parada_destino_codigo', sa.String(length=12), nullable=True),
        sa.Column('embarcou_em', sa.DateTime(), nullable=False),
        sa.Column('encerrada_em', sa.DateTime(), nullable=True),
        sa.Column('motivo_encerramento', sa.String(length=20), nullable=True),
        sa.Column('origem_embarque', sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_viagem_usuario_id', 'viagem', ['usuario_id'])
    op.create_index(
        'uq_viagem_ativa_por_usuario',
        'viagem',
        ['usuario_id'],
        unique=True,
        postgresql_where=sa.text('encerrada_em IS NULL'),
    )


def downgrade() -> None:
    op.drop_index('uq_viagem_ativa_por_usuario', table_name='viagem')
    op.drop_index('ix_viagem_usuario_id', table_name='viagem')
    op.drop_table('viagem')
