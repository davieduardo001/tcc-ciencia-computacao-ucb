"""feat: criar tabela confirmacoes_ocorrencia (US #26 — Confirmar Ocorrência)

Revision ID: b1c2d3e4f5a6
Revises: a7b8c9d0e1f2
Create Date: 2026-10-05 00:00:00.000000

Migration só aditiva: nenhum dado existente é alterado.

A constraint UNIQUE(ocorrencia_id, usuario_id) é o mecanismo principal
de prevenção de confirmações duplicadas — o banco rejeita a segunda
inserção com IntegrityError mesmo sob requisições concorrentes, sem
depender de uma consulta prévia.

FK para ocorrencia.id garante integridade referencial; sem FK para
usuarios.id para não acoplar colaboracao ao schema auth (decisão
arquitetural registrada em RotaFavorita e Ocorrencia).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "confirmacoes_ocorrencia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ocorrencia_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ocorrencia_id"], ["ocorrencia.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ocorrencia_id",
            "usuario_id",
            name="uq_confirmacao_ocorrencia_usuario",
        ),
    )
    op.create_index(
        "ix_confirmacoes_ocorrencia_ocorrencia_id",
        "confirmacoes_ocorrencia",
        ["ocorrencia_id"],
        unique=False,
    )
    op.create_index(
        "ix_confirmacoes_ocorrencia_usuario_id",
        "confirmacoes_ocorrencia",
        ["usuario_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_confirmacoes_ocorrencia_usuario_id",
        table_name="confirmacoes_ocorrencia",
    )
    op.drop_index(
        "ix_confirmacoes_ocorrencia_ocorrencia_id",
        table_name="confirmacoes_ocorrencia",
    )
    op.drop_table("confirmacoes_ocorrencia")
