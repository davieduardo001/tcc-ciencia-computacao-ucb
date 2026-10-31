"""feat: consentimento e compartilhamento de posicao na viagem (US #199)

Revision ID: f7a8b9c0d1e2
Revises: a7b8c9d0e1f2
Create Date: 2026-10-23 00:00:00.000000

Migration só aditiva: nada existente é alterado ou apagado.

Colunas de CONSENTIMENTO, não de posição: nenhuma latitude/longitude do
passageiro é persistida (LGPD, art. 7º, I — RN-C1 da #199, revisão da
RN-06 da #171). `compartilha_posicao_em` guarda o instante em que o
compartilhamento foi ativado (nulo = não compartilha, o padrão) e
`consentimento_versao`, a versão do texto de consentimento aceito.
Revogar ("Parar") devolve `compartilha_posicao_em` para nulo e mantém a
versão como prova do aceite.

A posição colaborativa em si vive SÓ EM MEMÓRIA, com validade de 2
minutos — ver mobilidade/posicoes_colaborativas.py.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'viagem',
        sa.Column('compartilha_posicao_em', sa.DateTime(), nullable=True),
    )
    op.add_column(
        'viagem',
        sa.Column('consentimento_versao', sa.String(length=40), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('viagem', 'consentimento_versao')
    op.drop_column('viagem', 'compartilha_posicao_em')
