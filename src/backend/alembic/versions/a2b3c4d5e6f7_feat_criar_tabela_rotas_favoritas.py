"""feat: criar tabela rotas_favoritas (US #25 — Salvar e Visualizar Rota Favorita)

Revision ID: a2b3c4d5e6f7
Revises: 09bed28051ec
Create Date: 2026-10-05 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "09bed28051ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rotas_favoritas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("numero_linha", sa.String(length=20), nullable=False),
        sa.Column("nome_linha", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("origem_lat", sa.Float(), nullable=False),
        sa.Column("origem_lng", sa.Float(), nullable=False),
        sa.Column("destino_lat", sa.Float(), nullable=False),
        sa.Column("destino_lng", sa.Float(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    # Índice principal: todas as queries filtram por usuario_id.
    op.create_index(
        op.f("ix_rotas_favoritas_usuario_id"),
        "rotas_favoritas",
        ["usuario_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_rotas_favoritas_usuario_id"),
        table_name="rotas_favoritas",
    )
    op.drop_table("rotas_favoritas")
