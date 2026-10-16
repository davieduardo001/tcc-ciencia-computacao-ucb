"""feat: criar tabela inscricao_push (US #172 - Web Push do alerta de proximidade)

Revision ID: a7b8c9d0e1f2
Revises: e5f6a7b8c9d0
Create Date: 2026-10-16 00:00:00.000000

Migration só aditiva: nada existente é alterado ou apagado. Homolog e
produção compartilham banco (issue #42), então esta migration roda em
produção assim que o deploy de homolog sobe.

`endpoint` é único: um aparelho tem uma inscrição. Se outra conta entrar no
mesmo aparelho, a linha muda de dono em vez de duplicar.

Não há coluna de localização, nome ou user agent de propósito (LGPD): a
tabela guarda só o que é preciso para entregar o aviso, e a linha some
quando a pessoa desativa, sai da conta ou o serviço de push diz que a
inscrição expirou.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'inscricao_push',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('usuario_id', sa.Uuid(), nullable=False),
        sa.Column('endpoint', sa.String(length=1024), nullable=False),
        sa.Column('p256dh', sa.String(length=255), nullable=False),
        sa.Column('auth', sa.String(length=64), nullable=False),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.Column('ultima_falha_em', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('endpoint', name='uq_inscricao_push_endpoint'),
    )
    op.create_index('ix_inscricao_push_usuario_id', 'inscricao_push', ['usuario_id'])


def downgrade() -> None:
    op.drop_index('ix_inscricao_push_usuario_id', table_name='inscricao_push')
    op.drop_table('inscricao_push')
