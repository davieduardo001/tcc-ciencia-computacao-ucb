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

import math
from datetime import datetime, time

# Abaixo disso o veículo é considerado parado (mesmo limiar do frontend,
# que usa isso pra decidir se desenha a seta de direção — ver
# LIMIAR_PARADO_KMH em MapaInterativo.tsx). Sem deslocamento recente, a
# distância/velocidade atual não é um preditor confiável de chegada.
VELOCIDADE_MINIMA_KMH = 3.0

_RAIO_TERRA_KM = 6371.0


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
