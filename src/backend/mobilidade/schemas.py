from typing import Literal

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
    # US #159 — espera estimada até embarcar nesta perna. `None` quando
    # não há dado suficiente (o front usa a duração teórica nesse caso).
    espera_min: float | None = None
    fonte_espera: Literal["tempo_real", "intervalo_medio", "teorica"] = "teorica"
    # Só preenchido quando `fonte_espera == "tempo_real"`.
    prefixo_veiculo: str | None = None
    # Só preenchido quando `fonte_espera == "intervalo_medio"`.
    intervalo_medio_min: float | None = None


class OpcaoViagemResponse(BaseModel):
    pernas: list[PernaResponse]
    baldeacoes: int
    distancia_km: float
    caminhada_metros: int
    duracao_estimada_min: int
    # US #159 — ETA real da viagem inteira, calculado a partir da
    # posição ao vivo dos ônibus. `None` quando não há ônibus
    # identificável se aproximando da parada de embarque — nesse caso
    # `duracao_estimada_min` (velocidade média) continua sendo a
    # referência, e `tipo_estimativa` fica "teorica".
    duracao_real_min: int | None = None
    tipo_estimativa: Literal["tempo_real", "parcial", "teorica"] = "teorica"
    calculado_em: str | None = None


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


# ---------------------------------------------------------------------------
# US #18 — Detalhes de uma parada
# ---------------------------------------------------------------------------


class ParadaLinhaResponse(BaseModel):
    """Uma das linhas que passam pela parada consultada."""

    numero: str
    nome: str
    sentido: str


class ParadaDetalheResponse(BaseModel):
    """
    Cenário 1: `proximos_horarios` traz os horários previstos mais
    próximos. Cenário 2 (parada sem horário disponível) é a lista vazia —
    o front trata isso como aviso, não erro.
    """

    nome: str
    codigo: str
    lat: float
    lng: float
    linhas: list[ParadaLinhaResponse]
    proximos_horarios: list[str]
