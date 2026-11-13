"""feat: criar tabela aviso_rota_favorita (US #207 - push das rotas preferidas)

Revision ID: d8e9f0a1b2c3
Revises: f7a8b9c0d1e2
Create Date: 2026-11-11 00:00:00.000000

Migration só aditiva: nada existente é alterado ou apagado. Homolog e
produção compartilham banco (issue #42), então esta migration roda em
produção assim que o deploy de homolog sobe.

A chave primária `favorita_id` é o que garante "um estado por favorita":
dois ciclos simultâneos do worker não criam duas linhas para a mesma
rota. Sem FK para `rotas_favoritas` (tabela do serviço de colaboração).

Nota de cadeia: revisa f7a8b9c0d1e2 (cabeça do homolog no momento). Se
outra migration nascer da mesma cabeça antes do merge, reencadear aqui
para não deixar duas cabeças na cadeia.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd8e9f0a1b2c3'
down_revision: Union[str, None] = 'f7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'aviso_rota_favorita',
        sa.Column('favorita_id', sa.Uuid(), nullable=False),
        sa.Column('antecedencia_enviada', sa.Boolean(), nullable=False),
        sa.Column('proximidade_enviada', sa.Boolean(), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('favorita_id'),
    )


def downgrade() -> None:
    op.drop_table('aviso_rota_favorita')
