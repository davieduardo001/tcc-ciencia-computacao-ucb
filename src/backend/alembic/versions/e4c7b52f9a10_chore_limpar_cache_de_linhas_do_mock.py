"""chore: limpar cache de linhas do mock (US #17 - dados reais do SEMOB)

A tabela `linha` é cache, não dado de usuário: o LinhaService a repopula
sozinho. Até agora ela guardava as linhas fictícias do LinhaMockProvider
(0.110 "Taguatinga/Rodoviária", 0.108, 0.120...), cujos números colidem
com linhas reais do DF que têm trajeto completamente diferente — a 0.110
de verdade é a circular Rodoviária/UnB.

Sem essa limpeza, os registros antigos ficariam presos por até 30 dias
(LINHA_CACHE_MAX_DIAS) e continuariam sendo servidos no lugar dos dados
reais ingeridos pelo mobilidade/ingestao_semob.py.

Revision ID: e4c7b52f9a10
Revises: d3f8a91c2b60
Create Date: 2026-09-13 21:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e4c7b52f9a10'
down_revision: Union[str, None] = 'd3f8a91c2b60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM linha")


def downgrade() -> None:
    # Não há o que desfazer: cache apagado se refaz sozinho na próxima
    # ingestão/busca.
    pass
