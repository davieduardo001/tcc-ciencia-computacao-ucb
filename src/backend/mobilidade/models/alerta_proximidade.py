from sqlalchemy import Column, DateTime, Float, Index, String, Uuid, func
from models.base import Base
import uuid


class AlertaProximidade(Base):
    """
    Alerta de proximidade da parada de destino — US #172.

    Uma linha aqui significa "o alerta já foi emitido para esta parada
    nesta viagem" — é a garantia do Cenário 2 (o alerta não se repete para
    a mesma parada na mesma viagem): o índice único
    (viagem_id, parada_destino_codigo) impede a segunda inserção mesmo se
    dois ciclos rodarem ao mesmo tempo.

    Campos:
        usuario_id            → passageiro que recebeu o alerta
        viagem_id              → PROVISÓRIO: identificador da viagem, sem
                                 FK porque a entidade de viagem é da
                                 US #171 (ainda aberta)
        linha_id               → linha em operação no momento do alerta
        parada_destino_codigo  → PROVISÓRIO: código estável da parada de
                                 destino, sem FK porque a tabela `parada`
                                 vem da #173 (PR #177)
        parada_destino_nome    → nome legível, para exibir sem consulta
        status                 → "disparado" hoje; "cancelado" reserva
                                 espaço para a viagem terminar antes do
                                 alerta (US #171)
        eta_minutos            → ETA calculado no momento do disparo,
                                 para diagnóstico (ETA em linha reta até
                                 a #173 entregar o trajeto)
        disparado_em            → instante em que a notificação foi emitida
        criado_em               → idem disparado_em na prática (linha nasce
                                  disparada)
    """

    __tablename__ = "alertas_proximidade"
    __table_args__ = (
        Index(
            "uq_alerta_proximidade_viagem_parada",
            "viagem_id",
            "parada_destino_codigo",
            unique=True,
        ),
    )

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    usuario_id = Column(Uuid, nullable=False, index=True)
    viagem_id = Column(String(64), nullable=False)
    linha_id = Column(String(20), nullable=False)
    parada_destino_codigo = Column(String(12), nullable=False)
    parada_destino_nome = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="disparado")
    eta_minutos = Column(Float, nullable=True)
    disparado_em = Column(DateTime, nullable=False)
    criado_em = Column(DateTime, default=func.now())
