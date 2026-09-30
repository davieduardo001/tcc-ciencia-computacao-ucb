# Tempo estimado de chegada — US #19
#
# Cenário 1/2: com GPS disponível, o ETA de cada veículo é a distância em
# linha reta até a posição do usuário dividida pela velocidade atual
# reportada pelo SEMOB. Sem PostGIS no banco (ver AGENT.md), a distância é
# calculada em Python via Haversine — não precisa de roteamento viário
# aqui, só uma estimativa pra ordenar/priorizar o que está mais perto.
#
# Cenário 3: quando a linha não tem nenhum veículo com GPS reportando,
# cai pro horário previsto mais próximo do agora — nunca inventa um
# tempo a partir de dado que não existe.
#
# Cenário 5: veículo parado (ou sem velocidade informada) não tem ETA
# calculável — mostrar um número ali seria estimar em cima de um veículo
# que pode estar preso no trânsito, não a caminho.

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, time
from typing import TYPE_CHECKING, Literal

from mobilidade.geometria import TrajetoMedido
from mobilidade.rota_service import VELOCIDADE_MEDIA_KMH

if TYPE_CHECKING:
    from mobilidade.posicao_service import PosicaoVeiculo
    from mobilidade.rota_service import OpcaoViagem

logger = logging.getLogger(__name__)

# Abaixo disso o veículo é considerado parado (mesmo limiar do frontend,
# que usa isso pra decidir se desenha a seta de direção — ver
# LIMIAR_PARADO_KMH em MapaInterativo.tsx). Sem deslocamento recente, a
# distância/velocidade atual não é um preditor confiável de chegada.
VELOCIDADE_MINIMA_KMH = 3.0

_RAIO_TERRA_KM = 6371.0

# ---------------------------------------------------------------------------
# US #159 — ETA ao longo do trajeto real (não em linha reta).
#
# `calcular_eta_minutos` (abaixo) resolve o Cenário 1 da #19 (pílula do
# mapa): distância em linha reta até a posição do usuário. Funciona bem
# ali porque o alvo é onde a pessoa está agora, sem um trajeto
# conhecido para projetar.
#
# Já a rota planejada (#159) tem um trajeto conhecido e uma parada de
# embarque fixa — dá pra (e a própria regra de negócio da #19 exige)
# medir a distância real ao longo do traçado, e também saber se o
# veículo já passou da parada (o que a distância em linha reta não
# revela: um ônibus 300 m à frente da parada, já indo embora, mede
# "perto" do mesmo jeito que um que está chegando).
# ---------------------------------------------------------------------------

TOLERANCIA_TRAJETO_M = 150.0
TOLERANCIA_NA_PARADA_M = 50.0
IDADE_MAXIMA_ETA_MIN = 5.0
ETA_MAXIMO_MIN = 90.0

# Quão perto (em metros, projetados ao longo do trajeto) dois veículos
# precisam estar para contar como "o mesmo ônibus" ao estimar intervalo
# — evita que uma posição reportada em duplicidade vire um intervalo de
# ~0 minutos.
DISTANCIA_MINIMA_ENTRE_VEICULOS_M = 300.0
MIN_VEICULOS_INTERVALO = 2
INTERVALO_VALIDO_MIN = (3.0, 60.0)

# Mesma espera fixa usada em `OpcaoViagem.duracao_estimada_min`
# (rota_service.py) quando não há intervalo real para estimar.
ESPERA_BALDEACAO_MIN = 6.0

FonteEspera = Literal["tempo_real", "intervalo_medio", "teorica"]
TipoEstimativa = Literal["tempo_real", "parcial", "teorica"]


def _distancia_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distância em linha reta entre dois pontos (fórmula de Haversine)."""
    rad_lat1, rad_lat2 = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(delta_lng / 2) ** 2
    )
    return 2 * _RAIO_TERRA_KM * math.asin(math.sqrt(a))


def calcular_eta_minutos(
    *,
    lat_veiculo: float,
    lng_veiculo: float,
    velocidade_kmh: float | None,
    lat_usuario: float,
    lng_usuario: float,
) -> float | None:
    """
    ETA de um veículo até a posição do usuário, em minutos.

    `None` quando o veículo não tem velocidade informada ou está parado
    (Cenário 5) — o front então mostra só o número da linha na pílula.
    """
    if velocidade_kmh is None or velocidade_kmh < VELOCIDADE_MINIMA_KMH:
        return None

    distancia = _distancia_km(lat_veiculo, lng_veiculo, lat_usuario, lng_usuario)
    return round((distancia / velocidade_kmh) * 60, 1)


def proximo_horario_previsto(
    horarios_previstos: list[str], agora: datetime
) -> str | None:
    """
    Próximo horário da tabela teórica a partir de `agora` (Cenário 3).

    `horarios_previstos` vem no formato "HH:MM" (ver models/linha.py).
    Quando todos os horários do dia já passaram, devolve o primeiro do
    dia seguinte — melhor sugerir a primeira partida de amanhã do que
    não devolver nada.
    """
    if not horarios_previstos:
        return None

    horarios_validos = sorted(
        h for h in horarios_previstos if _horario_valido(h)
    )
    if not horarios_validos:
        return None

    agora_hhmm = agora.strftime("%H:%M")
    for horario in horarios_validos:
        if horario >= agora_hhmm:
            return horario

    return horarios_validos[0]


def _horario_valido(horario: str) -> bool:
    try:
        hora, minuto = horario.split(":")
        time(int(hora), int(minuto))
        return True
    except (ValueError, TypeError):
        return False


def eta_minutos_veiculo(
    veiculo: PosicaoVeiculo,
    *,
    lat_alvo: float,
    lng_alvo: float,
    agora: datetime,
    trajeto: TrajetoMedido | None = None,
    sentido_alvo: str | None = None,
) -> float | None:
    """
    Ponto de entrada único do motor de ETA (US #19), usado tanto pela
    pílula do mapa (`GET /linhas/{numero}/posicoes`) quanto pela rota
    planejada (`GET /rotas`, US #159).

    Quando o trajeto da linha é conhecido, mede a distância real ao
    longo dele (projeta o veículo e o alvo no traçado, descarta veículo
    de sentido errado ou que já passou do alvo). Sem trajeto resolvível
    — só acontece se a linha ainda não tiver rota ingerida — cai para a
    estimativa em linha reta original, que é o que a US #19 já tinha
    antes desta entrega.
    """
    if trajeto is not None:
        indice_alvo = trajeto.indice_mais_proximo((lat_alvo, lng_alvo), TOLERANCIA_TRAJETO_M)
        if indice_alvo is not None:
            return _eta_por_trajeto(veiculo, trajeto, indice_alvo, sentido_alvo, agora)

    return calcular_eta_minutos(
        lat_veiculo=veiculo.lat,
        lng_veiculo=veiculo.lng,
        velocidade_kmh=veiculo.velocidade,
        lat_usuario=lat_alvo,
        lng_usuario=lng_alvo,
    )


def _eta_por_trajeto(
    veiculo: PosicaoVeiculo,
    trajeto: TrajetoMedido,
    indice_alvo: int,
    sentido_alvo: str | None,
    agora: datetime,
) -> float | None:
    if veiculo.velocidade is None or veiculo.velocidade < VELOCIDADE_MINIMA_KMH:
        return None

    if sentido_alvo is not None:
        sentido_veiculo = (veiculo.sentido or "").strip().upper()
        if sentido_veiculo != sentido_alvo.strip().upper():
            return None

    idade_min = (agora - veiculo.atualizado_em).total_seconds() / 60
    if idade_min > IDADE_MAXIMA_ETA_MIN:
        return None

    indice_veiculo = trajeto.indice_mais_proximo((veiculo.lat, veiculo.lng), TOLERANCIA_TRAJETO_M)
    if indice_veiculo is None:
        return None

    metros = trajeto.metros_entre(indice_veiculo, indice_alvo)
    if metros < -TOLERANCIA_NA_PARADA_M:
        if (sentido_alvo or "").strip().upper() == "CIRCULAR":
            # Linha circular: o ônibus "atrás" do alvo só está atrás
            # porque já deu a volta — vai chegar de novo lá na frente.
            metros = (
                trajeto.comprimento_m
                - trajeto.acumulado[indice_veiculo]
                + trajeto.acumulado[indice_alvo]
            )
        else:
            # Já passou da parada e não vai voltar: não é "chegando".
            return None

    metros = max(0.0, metros)
    minutos_de_viagem = metros / (veiculo.velocidade * 1000 / 60)
    minutos_restantes = max(0.0, minutos_de_viagem - idade_min)
    if minutos_restantes > ETA_MAXIMO_MIN:
        return None

    return round(minutos_restantes, 1)


def intervalo_medio_min(
    veiculos: list[PosicaoVeiculo],
    trajeto: TrajetoMedido,
    sentido: str,
    agora: datetime,
) -> float | None:
    """
    Intervalo médio (headway) estimado entre os veículos ativos de uma
    linha, a partir de uma única leitura do feed: projeta cada veículo
    no trajeto, ordena pela posição ao longo dele e tira a mediana do
    espaçamento entre consecutivos.

    É o que a #159 usa para estimar a espera na 2ª perna de uma
    baldeação, quando não há como saber qual ônibus específico vai
    passar pela parada de troca (não existe motor de horários — US
    #115 fica fora de escopo).

    `None` quando sobram menos de 2 veículos utilizáveis, ou quando o
    resultado foge da faixa plausível de 3–60 min — nesses casos a
    espera cai para a estimativa fixa de `ESPERA_BALDEACAO_MIN`.
    """
    sentido_alvo = sentido.strip().upper()
    posicoes_m: list[float] = []

    for v in veiculos:
        if (v.sentido or "").strip().upper() != sentido_alvo:
            continue
        idade_min = (agora - v.atualizado_em).total_seconds() / 60
        if idade_min > IDADE_MAXIMA_ETA_MIN:
            continue
        indice = trajeto.indice_mais_proximo((v.lat, v.lng), TOLERANCIA_TRAJETO_M)
        if indice is None:
            continue
        posicoes_m.append(trajeto.acumulado[indice])

    posicoes_m.sort()
    agrupadas: list[float] = []
    for posicao in posicoes_m:
        # Comboio (dois veículos quase na mesma posição, ou a mesma
        # posição reportada em duplicidade) conta como um só — senão o
        # espaçamento entre eles derruba a mediana para perto de zero.
        if agrupadas and posicao - agrupadas[-1] < DISTANCIA_MINIMA_ENTRE_VEICULOS_M:
            continue
        agrupadas.append(posicao)

    if len(agrupadas) < MIN_VEICULOS_INTERVALO:
        return None

    espacamentos = [b - a for a, b in zip(agrupadas, agrupadas[1:])]
    if sentido_alvo == "CIRCULAR":
        espacamentos.append(trajeto.comprimento_m - agrupadas[-1] + agrupadas[0])

    espacamentos.sort()
    meio = len(espacamentos) // 2
    mediana_m = (
        espacamentos[meio]
        if len(espacamentos) % 2
        else (espacamentos[meio - 1] + espacamentos[meio]) / 2
    )

    minutos = mediana_m / (VELOCIDADE_MEDIA_KMH * 1000 / 60)
    if not (INTERVALO_VALIDO_MIN[0] <= minutos <= INTERVALO_VALIDO_MIN[1]):
        return None
    return round(minutos, 1)


@dataclass(frozen=True)
class EstimativaPerna:
    espera_min: float | None
    fonte: FonteEspera
    prefixo_veiculo: str | None = None
    intervalo_medio_min: float | None = None


@dataclass(frozen=True)
class EstimativaViagem:
    pernas: list[EstimativaPerna]
    duracao_real_min: int | None
    tipo: TipoEstimativa


def estimar_viagem(
    opcao: OpcaoViagem,
    posicoes_por_linha: dict[str, list[PosicaoVeiculo]],
    trajetos_por_perna: dict[tuple[str, str], TrajetoMedido],
    agora: datetime,
) -> EstimativaViagem:
    """
    ETA real de uma opção de viagem (US #159): tempo até o ônibus mais
    próximo chegar à parada de embarque, mais a duração do trajeto; com
    baldeação, soma a espera estimada da 2ª perna (por intervalo médio,
    ou a espera fixa quando não há intervalo estimável).

    Nunca lança: qualquer falha inesperada cai para a estimativa
    teórica (a mesma que a rota já mostrava antes da #159), igual à
    postura de `ETAService.consultar` do lado de `colaboracao`.
    """
    try:
        return _estimar_viagem(opcao, posicoes_por_linha, trajetos_por_perna, agora)
    except Exception:
        logger.warning(
            "Falha ao estimar ETA da rota (linha=%s)",
            opcao.pernas[0].numero if opcao.pernas else "?",
        )
        return EstimativaViagem(
            pernas=[EstimativaPerna(espera_min=None, fonte="teorica") for _ in opcao.pernas],
            duracao_real_min=None,
            tipo="teorica",
        )


def _minutos_a_pe(metros: float) -> float:
    return metros / 1000 / 5.0 * 60  # 5 km/h, mesma referência de rota_service


def _minutos_a_bordo(distancia_km: float) -> float:
    return distancia_km / VELOCIDADE_MEDIA_KMH * 60


def _estimar_viagem(
    opcao: OpcaoViagem,
    posicoes_por_linha: dict[str, list[PosicaoVeiculo]],
    trajetos_por_perna: dict[tuple[str, str], TrajetoMedido],
    agora: datetime,
) -> EstimativaViagem:
    perna1 = opcao.pernas[0]
    trajeto1 = trajetos_por_perna.get((perna1.numero, perna1.sentido))
    minutos_a_pe_embarque = _minutos_a_pe(perna1.embarque.caminhada_metros)

    espera1: float | None = None
    prefixo1: str | None = None
    if trajeto1 is not None:
        indice_embarque = trajeto1.indice_mais_proximo(
            (perna1.embarque.lat, perna1.embarque.lng), TOLERANCIA_TRAJETO_M
        )
        if indice_embarque is not None:
            candidatos = []
            for v in posicoes_por_linha.get(perna1.numero, []):
                eta = _eta_por_trajeto(v, trajeto1, indice_embarque, perna1.sentido, agora)
                # Um ônibus que chega antes de a pessoa terminar de
                # andar até a parada não é "o próximo" — ela não
                # embarcaria nele mesmo que existisse.
                if eta is not None and eta >= minutos_a_pe_embarque:
                    candidatos.append((eta, v.prefixo))
            if candidatos:
                espera1, prefixo1 = min(candidatos)

    if espera1 is None:
        return EstimativaViagem(
            pernas=[
                EstimativaPerna(espera_min=None, fonte="teorica") for _ in opcao.pernas
            ],
            duracao_real_min=None,
            tipo="teorica",
        )

    pernas_estimativa = [
        EstimativaPerna(espera_min=espera1, fonte="tempo_real", prefixo_veiculo=prefixo1)
    ]
    total_min = espera1 + _minutos_a_bordo(perna1.distancia_km)
    tipo: TipoEstimativa = "tempo_real"

    if len(opcao.pernas) > 1:
        perna2 = opcao.pernas[1]
        trajeto2 = trajetos_por_perna.get((perna2.numero, perna2.sentido))
        intervalo = (
            intervalo_medio_min(
                posicoes_por_linha.get(perna2.numero, []), trajeto2, perna2.sentido, agora
            )
            if trajeto2 is not None
            else None
        )
        minutos_a_pe_baldeacao = _minutos_a_pe(perna2.embarque.caminhada_metros)

        if intervalo is not None:
            espera2 = math.ceil(intervalo / 2) + minutos_a_pe_baldeacao
            pernas_estimativa.append(
                EstimativaPerna(
                    espera_min=espera2, fonte="intervalo_medio", intervalo_medio_min=intervalo
                )
            )
        else:
            espera2 = ESPERA_BALDEACAO_MIN + minutos_a_pe_baldeacao
            pernas_estimativa.append(EstimativaPerna(espera_min=espera2, fonte="teorica"))
            tipo = "parcial"

        total_min += espera2 + _minutos_a_bordo(perna2.distancia_km)

    total_min += _minutos_a_pe(opcao.pernas[-1].desembarque.caminhada_metros)

    return EstimativaViagem(
        pernas=pernas_estimativa, duracao_real_min=max(1, round(total_min)), tipo=tipo
    )
