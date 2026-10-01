import uuid
from datetime import datetime, timedelta

from sqlalchemy import Column, DateTime, Float, Integer, String, Uuid
from models.base import Base


class Ocorrencia(Base):
    """
    Reporte de ocorrência em uma linha (US #23).

    Vinculada só a `linha_numero` (string) — nunca a uma Parada, que
    ainda não é tabela própria (vive como JSON dentro de `linha`; ver
    documento_arquitetura.md, linha 338). Por isso nenhum FK de banco pra
    `linha`: a linha é cacheada sob demanda, então um reporte pode chegar
    pra uma linha que o cache ainda não viu.
    """

    __tablename__ = "ocorrencia"

    # Tipos crowd-validados: nascem "pendente", precisam de 2 confirmações
    # independentes (US #26) pra virar "confirmada".
    TIPOS_CROWD_VALIDADOS = ["atraso", "nao_passou", "lotacao", "obra_via", "onibus_quebrou"]

    # Tipos de exibição imediata: não esperam confirmação cruzada — um
    # acidente ou um problema de segurança não pode ficar represado
    # atrás de uma 2ª confirmação antes de aparecer pra outros passageiros.
    TIPOS_IMEDIATOS = ["acidente", "seguranca"]

    TIPOS_VALIDOS = TIPOS_CROWD_VALIDADOS + TIPOS_IMEDIATOS

    STATUS_VALIDOS = ["pendente", "confirmada", "expirada"]

    # Minutos até expirar, por tipo — situações mais voláteis somem mais
    # rápido da listagem (US #24), mas o registro nunca é apagado.
    TTL_MINUTOS = {
        "lotacao": 15,
        "atraso": 30,
        "acidente": 30,
        "seguranca": 30,
        "nao_passou": 60,
        "onibus_quebrou": 60,
        "obra_via": 120,
    }

    LIMITE_REPORTES_POR_HORA = 3

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    usuario_id = Column(Uuid, nullable=False, index=True)
    linha_numero = Column(String(20), nullable=False, index=True)
    tipo = Column(String(20), nullable=False)
    descricao = Column(String(500), nullable=True)
    local = Column(String(255), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="pendente")
    contador_confirmacoes = Column(Integer, nullable=False, default=0)
    criado_em = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
    expira_em = Column(DateTime, nullable=False)

    @staticmethod
    def calcular_expiracao(tipo: str, criado_em: datetime) -> datetime:
        return criado_em + timedelta(minutes=Ocorrencia.TTL_MINUTOS[tipo])

    @property
    def status_inicial(self) -> str:
        return "confirmada" if self.tipo in Ocorrencia.TIPOS_IMEDIATOS else "pendente"
