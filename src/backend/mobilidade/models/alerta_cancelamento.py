from sqlalchemy import Column, DateTime, Index, String, Uuid, func
from models.base import Base
import uuid


class AlertaCancelamento(Base):
    """
    Alerta de cancelamento de viagem — US #28.

    Uma linha aqui significa "a partida prevista de HOJE para esta linha já
    foi avaliada e considerada cancelada" — é a garantia do Cenário 3 (o
    alerta não se repete para a mesma partida): o índice único
    (numero_linha, horario_partida) impede a segunda inserção mesmo se
    dois ciclos do worker rodarem ao mesmo tempo.

    O registro é POR DIA: `detectado_em` guarda o instante da detecção e a
    comparação de horário é feita com o relógio local (fuso SEMOB) no
    serviço — ver servico_cancelamento.py.

    Campos:
        numero_linha        → linha cuja partida prevista não teve veículo
                              (ex: "0.110")
        horario_partida     → horário previsto da tabela teórica ("HH:MM")
        status              → "suspeito": detectado por AUSÊNCIA de veículo
                              (Cenário 3); "confirmado": reservado para o
                              cancelamento anunciado pelo operador, quando
                              existir fonte para isso (hoje não existe —
                              ver suposição no cabeçalho do serviço)
        alternativa_numero  → linha sugerida com sobreposição de paradas
                              >= 70% (Cenário 2), ou None quando não há
        detectado_em        → instante em que o worker registrou o alerta
        criado_em           → idem detectado_em na prática (linha nasce
                              detectada)
    """

    __tablename__ = "alertas_cancelamento"
    __table_args__ = (
        Index(
            "uq_alerta_cancelamento_linha_horario",
            "numero_linha",
            "horario_partida",
            unique=True,
        ),
    )

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    numero_linha = Column(String(20), nullable=False)
    horario_partida = Column(String(5), nullable=False)
    status = Column(String(20), nullable=False, default="suspeito")
    alternativa_numero = Column(String(20), nullable=True)
    detectado_em = Column(DateTime, nullable=False)
    criado_em = Column(DateTime, default=func.now())
