import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID

from models.base import Base


class RotaFavorita(Base):
    """
    Rota favorita de um usuário (US #25).

    Representa uma rota calculada (origem → destino via uma linha) que o
    usuário optou por salvar para acesso rápido. Cada registro pertence
    exclusivamente ao usuário autenticado — o isolamento é garantido em
    todas as queries (filtro por `usuario_id`).

    Coordenadas armazenadas como Float separados (lat/lng), sem PostGIS,
    seguindo o padrão adotado em `Ocorrencia.lat/lng` e nos schemas da
    US #20. Não existe tipo GeoPoint no projeto.

    `numero_linha` e `nome_linha` são desnormalizados intencionalmente:
      - `numero_linha` é necessário para o FavoritosProvider do Worker
        (US #22) e para o acesso rápido ao rastreamento.
      - `nome_linha` evita round-trips ao serviço de mobilidade apenas
        para exibir um rótulo legível na tela de favoritos.

    Limite de 20 favoritos por usuário: verificado no service antes do
    INSERT (mesmo padrão de `Ocorrencia.LIMITE_REPORTES_POR_HORA`).
    """

    __tablename__ = "rotas_favoritas"

    # Limite de favoritos por usuário — verificado no service.
    LIMITE_FAVORITOS = 20

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # O ORM não declara ForeignKey (mesmo padrão de Ocorrencia), pra não
    # acoplar o modelo do serviço de colaboração ao de auth. A migration, porém,
    # cria a FK real para usuarios.id — o banco garante a integridade e o
    # autogenerate do Alembic não deve ser usado pra "corrigir" essa diferença.
    usuario_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Número da linha (ex: "0.110") — usado para rastreamento e para o
    # FavoritosProvider da US #22.
    numero_linha = Column(String(20), nullable=False)

    # Nome legível (ex: "0.110 — Taguatinga / Rodoviária") — desnormalizado
    # para exibição sem consulta extra ao serviço de mobilidade.
    nome_linha = Column(String(255), nullable=False)

    # Rótulo definido pelo usuário (ex: "Casa → Trabalho").
    label = Column(String(100), nullable=False)

    # Coordenadas de origem — mesmo tipo de Ocorrencia.lat/lng.
    origem_lat = Column(Float, nullable=False)
    origem_lng = Column(Float, nullable=False)

    # Coordenadas de destino.
    destino_lat = Column(Float, nullable=False)
    destino_lng = Column(Float, nullable=False)

    criado_em = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    atualizado_em = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )
