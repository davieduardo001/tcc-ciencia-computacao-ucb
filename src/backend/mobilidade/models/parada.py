from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String, UniqueConstraint

from models.base import Base


class Parada(Base):
    """
    Parada física única (US #173).

    O SEMOB publica os abrigos em `/pontos` sem nenhum identificador, e o
    mesmo abrigo costuma aparecer como mais de um registro a poucos metros
    (medido: ~900 pares a até 15 m). A ingestão funde esses registros por
    proximidade (ver `paradas_fisicas.py`) e grava aqui uma linha por
    parada física, com um `codigo` estável.

    Quem consome (ETA, alerta de proximidade, "pegar o ônibus") deve usar
    o `codigo`, não o `id`: a tabela é reconstruída a cada ingestão, então
    o `id` muda; o `codigo` é derivado do centróide e se mantém.
    """

    __tablename__ = "parada"
    __table_args__ = (Index("ix_parada_lat_lng", "lat", "lng"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(12), nullable=False, unique=True)
    nome = Column(String(255), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)


class RotaParada(Base):
    """
    Posição de uma parada física dentro de uma rota (linha × sentido).

    `indice_trajeto` e `distancia_acumulada_m` são pré-calculados na
    ingestão: o ETA deixa de reprojetar a coordenada da parada no
    traçado a cada requisição.

    `distancia_ao_trajeto_m` existe porque o vínculo parada↔rota usa um
    raio de 40 m, e ~21% dos pares (parada, linha) caem dentro dele tanto
    na IDA quanto na VOLTA (vias estreitas, lados opostos da rua). Nesses
    casos a rota de menor distância é o lado onde a parada realmente está.
    """

    __tablename__ = "rota_parada"
    __table_args__ = (
        UniqueConstraint("numero", "sentido", "parada_id", name="uq_rota_parada"),
        Index("ix_rota_parada_rota", "numero", "sentido"),
        Index("ix_rota_parada_parada", "parada_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(String(20), nullable=False)
    sentido = Column(String(20), nullable=False)
    parada_id = Column(Integer, ForeignKey("parada.id"), nullable=False)

    # Posição da parada na rota, a partir de 0, na ordem do trajeto.
    ordem = Column(Integer, nullable=False)
    indice_trajeto = Column(Integer, nullable=False)
    distancia_acumulada_m = Column(Float, nullable=False)
    distancia_ao_trajeto_m = Column(Float, nullable=False)
