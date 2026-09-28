from sqlalchemy import Column, DateTime, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.sql import func

from models.base import Base


class Rota(Base):
    """
    Trajeto de uma linha **em um sentido** (US #20).

    A tabela `linha` guarda um trajeto por linha — o sentido "principal"
    escolhido na ingestão — porque a US #15 busca por número e mostra
    uma linha só. Isso não serve pra calcular origem→destino: a mesma
    linha que leva de Ceilândia à Rodoviária na IDA faz o caminho
    inverso na VOLTA, e quem procura a volta não acharia nada.

    Então aqui cada par (numero, sentido) é uma linha da tabela. São
    ~1.408 registros para as ~923 linhas do DF.
    """

    __tablename__ = "rota"
    __table_args__ = (
        UniqueConstraint("numero", "sentido", name="uq_rota_numero_sentido"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(String(20), nullable=False, index=True)

    # IDA, VOLTA ou CIRCULAR — como vem do SEMOB, sem tradução.
    sentido = Column(String(20), nullable=False)

    # Rótulo legível da linha, o mesmo formato usado em `linha.nome`.
    nome = Column(String(255), nullable=False)

    # list[[lat, lng]] na ordem em que o ônibus percorre.
    trajeto = Column(JSON, nullable=False)

    # list[{"nome": str, "lat": float, "lng": float}] na ordem do trajeto.
    paradas = Column(JSON, nullable=False)

    atualizado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class RotaCelula(Base):
    """
    Índice espacial em grade das rotas — é o que torna a busca
    origem→destino viável em tempo de request.

    Sem isso, responder "quais linhas vão daqui até ali" exigiria varrer
    as ~929 mil coordenadas de trajeto a cada consulta: medi 0,7 s por
    busca, e carregar tudo em memória custaria dezenas de MB por
    processo — o mesmo erro que derrubou o autocomplete com 502.

    Em vez disso, a ingestão quebra o DF numa grade de células de
    ~275 m e grava, para cada rota que passa por uma célula, o menor e o
    maior índice do trajeto ali dentro. A busca vira duas consultas
    indexadas e um join: ~180 mil registros no total.

    `indice_min`/`indice_max` são o que permite saber o **sentido** da
    viagem: se o menor índice na célula da origem for menor que o maior
    índice na célula do destino, o ônibus passa na origem antes de
    passar no destino — ou seja, serve para essa viagem. É essa
    comparação que faz IDA e VOLTA se resolverem sozinhas, sem regra
    especial.
    """

    __tablename__ = "rota_celula"
    __table_args__ = (
        Index("ix_rota_celula_grade", "cel_lat", "cel_lng"),
        Index("ix_rota_celula_rota", "numero", "sentido"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(String(20), nullable=False)
    sentido = Column(String(20), nullable=False)

    # Coordenada da célula: floor(lat / LADO_CELULA_GRAUS), idem lng.
    cel_lat = Column(Integer, nullable=False)
    cel_lng = Column(Integer, nullable=False)

    indice_min = Column(Integer, nullable=False)
    indice_max = Column(Integer, nullable=False)
