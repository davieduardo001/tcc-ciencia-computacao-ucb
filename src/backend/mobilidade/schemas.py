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
