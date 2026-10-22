import uuid

from sqlalchemy import Column, DateTime, Index, String, Uuid, text

from models.base import Base


class Viagem(Base):
    """
    Viagem em andamento ou encerrada de um passageiro — US #171.

    Uma linha aqui significa "este usuário embarcou neste veículo". É o que
    separa **Aguardando** de **Em viagem** (RN-04) e o que alimenta o alerta
    de proximidade da #172.

    LGPD (RN-06): só o mínimo é persistido. A posição do usuário serve para
    validar o embarque e é descartada na hora — não existe coluna de
    latitude/longitude nesta tabela, e é de propósito. `veiculo_prefixo` é o
    identificador público do ônibus (sai no feed da SEMOB), não uma posição.

    Campos:
        usuario_id             → passageiro; vem do X-User-Id do Gateway
        numero_linha           → linha em que embarcou (ex.: "0.110")
        sentido                → sentido do veículo no embarque; nulo
                                 quando o feed não informa
        veiculo_prefixo        → ônibus identificado por proximidade
        parada_destino_codigo  → código estável da parada (ADR-14), opcional.
                                 Sem FK: a tabela `parada` é reconstruída a
                                 cada ingestão
        embarcou_em            → UTC (sem fuso, como as demais tabelas)
        encerrada_em           → nulo enquanto a viagem está ativa
        motivo_encerramento    → "usuario" | "expirada"
        origem_embarque        → "manual" hoje; "proximidade" reservado
                                 para uma inferência automática futura
    """

    __tablename__ = "viagem"
    __table_args__ = (
        # RN-15: uma viagem ativa por usuário, garantida pelo banco — dois
        # toques simultâneos em "Peguei este ônibus" não criam duas.
        Index(
            "uq_viagem_ativa_por_usuario",
            "usuario_id",
            unique=True,
            postgresql_where=text("encerrada_em IS NULL"),
            sqlite_where=text("encerrada_em IS NULL"),
        ),
    )

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    usuario_id = Column(Uuid, nullable=False, index=True)
    numero_linha = Column(String(20), nullable=False)
    sentido = Column(String(20), nullable=True)
    veiculo_prefixo = Column(String(40), nullable=False)
    parada_destino_codigo = Column(String(12), nullable=True)
    embarcou_em = Column(DateTime, nullable=False)
    encerrada_em = Column(DateTime, nullable=True)
    motivo_encerramento = Column(String(20), nullable=True)
    origem_embarque = Column(String(20), nullable=False, default="manual")
