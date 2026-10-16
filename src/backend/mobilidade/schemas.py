from typing import Literal

from pydantic import BaseModel, Field


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
    # Issue #190 — código da parada física (`parada.codigo`) deste ponto na
    # rota do trecho. `None` quando não há parada ingerida a até 40 m: o
    # front mostra o ponto no mapa e não consegue pedir o tempo.
    parada_codigo: str | None = None


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
    # Card #179 — a parada ATÉ A QUAL o `eta_minutos` foi medido: a mais
    # próxima do usuário, no sentido deste veículo. `None` quando não havia
    # parada ingerida por perto e o ETA veio da projeção do GPS no traçado.
    parada_codigo: str | None = None
    parada_nome: str | None = None


class ChegadaResponse(BaseModel):
    """
    Quando o ônibus de uma linha chega numa parada (card #179, ⑤b).

    `fonte` diz de onde veio o número — RN-10: `ao_vivo` é a posição real
    do ônibus; `previsto` é horário de saída + tempo de percurso, para
    quando não há ônibus a caminho; `None` é "sem dado" (RN-09: não inventa).
    """

    numero: str
    nome: str
    rota_sentido: str
    eta_minutos: float | None = None
    fonte: Literal["ao_vivo", "previsto"] | None = None
    # só `ao_vivo`
    prefixo: str | None = None
    veiculos_a_caminho: int = 0
    # só `previsto`: "HH:MM" da passagem prevista nesta parada
    horario_previsto: str | None = None


class ChegadasParadaResponse(BaseModel):
    parada_codigo: str
    parada_nome: str
    calculado_em: str
    chegadas: list[ChegadaResponse]


# ---------------------------------------------------------------------------
# Issue #190 — tempo do ônibus nas paradas de subir e descer de uma rota
# ---------------------------------------------------------------------------


class PernaChegadaRequest(BaseModel):
    """Um trecho da rota escolhida: a linha, o sentido e as duas paradas."""

    numero: str = Field(min_length=1, max_length=20)
    sentido: str = Field(min_length=1, max_length=20)
    embarque_codigo: str | None = Field(default=None, max_length=40)
    desembarque_codigo: str | None = Field(default=None, max_length=40)


class ChegadasDaRotaRequest(BaseModel):
    # Uma rota tem 1 ou 2 trechos hoje; o teto protege o custo do cálculo.
    pernas: list[PernaChegadaRequest] = Field(min_length=1, max_length=6)


class ChegadaNoPontoResponse(BaseModel):
    """
    Quando o ônibus daquele trecho chega a uma parada de subir ou descer.

    `fonte` (RN-10): `ao_vivo` é a posição real do ônibus; `previsto` é
    horário de saída + tempo de percurso; `None` é "sem dado" (RN-09).
    """

    parada_codigo: str | None = None
    eta_minutos: float | None = None
    fonte: Literal["ao_vivo", "previsto"] | None = None
    # só `ao_vivo`: o ônibus que o passageiro pegaria
    prefixo: str | None = None
    # só `previsto`: "HH:MM" da passagem prevista
    horario_previsto: str | None = None


class ChegadasDaPernaResponse(BaseModel):
    numero: str
    sentido: str
    embarque: ChegadaNoPontoResponse
    desembarque: ChegadaNoPontoResponse


class ChegadasDaRotaResponse(BaseModel):
    calculado_em: str
    pernas: list[ChegadasDaPernaResponse]


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
    # US #173 — sentido da rota e posição da parada nela. Nulos quando a
    # parada foi resolvida pelo caminho antigo (antes da reingestão).
    rota_sentido: str | None = None
    ordem: int | None = None
    # Issue #174 — os próximos horários DESTA linha (até 3). Campo novo e
    # opcional: clientes antigos seguem lendo `proximos_horarios` da parada.
    proximos_horarios: list[str] = []


class ParadaDetalheResponse(BaseModel):
    """
    Cenário 1: `proximos_horarios` traz os horários previstos mais
    próximos (até 3, combinados entre as linhas — mantido por
    compatibilidade; o painel usa os de cada linha em `linhas[]`). Cenário 2 (parada sem horário disponível) é a lista vazia —
    o front trata isso como aviso, não erro.
    """

    nome: str
    codigo: str
    lat: float
    lng: float
    linhas: list[ParadaLinhaResponse]
    proximos_horarios: list[str]


class ParadaBuscadaResponse(BaseModel):
    """US #21 — uma parada na lista de resultados da busca."""

    codigo: str
    # Vazio quando o SEMOB só traz o CEP do abrigo — o front mostra um
    # rótulo neutro.
    nome: str
    lat: float
    lng: float
    qtd_linhas: int
    # Só na busca por endereço: metros até o lugar encontrado.
    distancia_m: int | None = None


class BuscaParadaResponse(BaseModel):
    """
    US #21. `tipo` diz qual cenário respondeu: `nome` (Cenário 1),
    `endereco` (Cenário 2, com `referencia` = lugar geocodificado, para o
    mapa centralizar) ou `nenhum` (Cenário 3, `paradas` vazia).
    """

    tipo: Literal["nome", "endereco", "nenhum"]
    paradas: list[ParadaBuscadaResponse]
    referencia: LugarResponse | None = None
