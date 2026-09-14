from sqlalchemy import Column, DateTime, Integer, JSON, String
from sqlalchemy.sql import func

from models.base import Base


class Linha(Base):
    """
    Cache de linha de ônibus (número, paradas, trajeto, horários previstos).

    Populado sob demanda pelo LinhaService na primeira busca de cada
    número de linha — nunca em lote. `atualizado_em` define quando o
    registro é considerado velho o suficiente para ser buscado de novo
    na fonte (LinhaProvider), evitando chamadas repetidas à API externa.
    """

    __tablename__ = "linha"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(String(20), unique=True, nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    sentido = Column(String(255), nullable=False)

    # list[{"nome": str, "lat": float, "lng": float}], na ordem do trajeto
    paradas = Column(JSON, nullable=False)

    # list[[lat, lng]] — geometria do trajeto decodificada da polyline
    trajeto = Column(JSON, nullable=False)

    # list[str] — horários previstos (ex: ["06:00", "06:20", ...])
    horarios_previstos = Column(JSON, nullable=False)

    atualizado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
