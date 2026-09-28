from pydantic import BaseModel


class ParadaResponse(BaseModel):
    nome: str
    lat: float
    lng: float


class LinhaResponse(BaseModel):
    numero: str
    nome: str
    sentido: str
    paradas: list[ParadaResponse]
    trajeto: list[tuple[float, float]]
    horarios_previstos: list[str]


class LinhaNaoEncontrada(BaseModel):
    detail: str = "Linha não encontrada."


class LinhaResumoResponse(BaseModel):
    numero: str
    nome: str
    sentido: str


# ---------------------------------------------------------------------------
# US #20 — Rota de origem até destino
# ---------------------------------------------------------------------------


class LugarResponse(BaseModel):
    """Resultado da busca por ponto de referência (origem/destino)."""

    nome: str
    endereco: str
    lat: float
    lng: float


class PontoEmbarqueResponse(BaseModel):
    lat: float
    lng: float
    parada_nome: str
    caminhada_metros: int


class PernaResponse(BaseModel):
    """Um trecho feito dentro de um mesmo ônibus."""

    numero: str
    sentido: str
    nome: str
    embarque: PontoEmbarqueResponse
    desembarque: PontoEmbarqueResponse
    distancia_km: float
    paradas_no_trecho: int
    trajeto: list[tuple[float, float]]


class OpcaoViagemResponse(BaseModel):
    pernas: list[PernaResponse]
    baldeacoes: int
    distancia_km: float
    caminhada_metros: int
    duracao_estimada_min: int


# ---------------------------------------------------------------------------
# US #16 — Posição do ônibus em tempo real
# ---------------------------------------------------------------------------


class PosicaoVeiculoResponse(BaseModel):
    """Um ônibus da linha, ao vivo (US #16)."""

    prefixo: str
    lat: float
    lng: float
    sentido: str | None = None
    velocidade: float | None = None
    direcao: float | None = None
    atualizado_em: str
    operadora: str
    # US #19 — só calculado quando o cliente informa lat/lng (posição do
    # usuário). `None` quando não informado, ou quando o veículo está
    # parado/sem velocidade (Cenário 5: pílula sem tempo).
    eta_minutos: float | None = None


class PosicoesLinhaResponse(BaseModel):
    """
    Resposta do rastreamento de uma linha.

    `veiculos` vazio é o Cenário 3 da US #16 ("nenhum veículo em
    operação") — situação normal fora do horário de pico, não erro.
    """

    numero: str
    veiculos: list[PosicaoVeiculoResponse]
    # US #19, Cenário 3 — só preenchido quando `veiculos` está vazio e o
    # cliente informou lat/lng: próximo horário da tabela teórica, já
    # que sem GPS não há distância/velocidade pra estimar nada.
    proximo_horario_previsto: str | None = None
