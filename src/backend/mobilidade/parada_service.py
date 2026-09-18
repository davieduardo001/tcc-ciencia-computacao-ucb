# Detalhes de uma parada — US #18
#
# Não existe uma tabela `parada` própria: cada linha guarda sua lista de
# paradas em `Linha.paradas` (JSON), povoada a partir dos abrigos do SEMOB
# (ver semob_source.py). Uma parada física compartilhada por várias linhas
# aparece assim uma vez em cada uma — então "quais linhas passam por aqui"
# é achar, entre as linhas já cacheadas, as que têm uma parada a poucos
# metros da coordenada clicada no mapa.

from __future__ import annotations

import zlib
from dataclasses import dataclass
from datetime import datetime
from math import asin, cos, radians, sin, sqrt

from sqlalchemy.orm import Session

from mobilidade.models.linha import Linha
from mobilidade.posicao_service import FUSO_SEMOB

# Mesmo raio da junção espacial linha/abrigo (ver
# semob_source.RAIO_PARADA_METROS): paradas do mesmo abrigo físico, vindas
# de linhas diferentes, caem bem dentro disso.
RAIO_MESMA_PARADA_METROS = 40.0

_RAIO_TERRA_METROS = 6_371_000.0

# Quantos horários mostrar no painel (Cenário 1 da US #18).
QTD_PROXIMOS_HORARIOS = 3


def _distancia_metros(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = radians(lat1), radians(lat2)
    dp = radians(lat2 - lat1)
    dl = radians(lng2 - lng1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * _RAIO_TERRA_METROS * asin(sqrt(a))


def _codigo_da_parada(lat: float, lng: float) -> str:
    """
    Código curto e estável da parada. Não vem do SEMOB (o abrigo não tem
    id na fonte /pontos), então é derivado da própria coordenada: a mesma
    parada sempre gera o mesmo código, sem precisar de uma tabela própria.
    """
    chave = f"{lat:.5f},{lng:.5f}".encode()
    return f"PR-{zlib.crc32(chave) % 100_000:05d}"


@dataclass(frozen=True)
class LinhaNaParada:
    numero: str
    nome: str
    sentido: str


@dataclass(frozen=True)
class ParadaEncontrada:
    nome: str
    codigo: str
    lat: float
    lng: float
    linhas: list[LinhaNaParada]
    proximos_horarios: list[str]


def _proximos_horarios(todos: list[str], agora: str) -> list[str]:
    """
    Os N próximos horários a partir de `agora` ("HH:MM"). Se o dia já
    esgotou os horários restantes, completa com os primeiros do dia
    seguinte — melhor sugerir o primeiro horário de amanhã do que não
    mostrar nada quando ainda faltam vagas na lista.
    """
    ordenados = sorted(set(todos))
    depois = [h for h in ordenados if h >= agora]
    antes = [h for h in ordenados if h < agora]
    return (depois + antes)[:QTD_PROXIMOS_HORARIOS]


class ParadaService:
    """US #18 — Ver Detalhes de uma Parada."""

    def obter_por_coordenada(
        self, db: Session, lat: float, lng: float
    ) -> ParadaEncontrada | None:
        colunas = (
            Linha.numero,
            Linha.nome,
            Linha.sentido,
            Linha.paradas,
            Linha.horarios_previstos,
        )

        nome_da_parada: str | None = None
        linhas: list[LinhaNaParada] = []
        todos_horarios: list[str] = []

        for numero, nome, sentido, paradas, horarios_previstos in db.query(*colunas):
            for p in paradas or []:
                if _distancia_metros(lat, lng, p["lat"], p["lng"]) > RAIO_MESMA_PARADA_METROS:
                    continue
                if nome_da_parada is None and p.get("nome"):
                    nome_da_parada = p["nome"]
                linhas.append(LinhaNaParada(numero=numero, nome=nome, sentido=sentido))
                todos_horarios.extend(horarios_previstos or [])
                break  # uma parada por linha já basta: não conta a mesma linha duas vezes

        if not linhas:
            return None

        agora = datetime.now(FUSO_SEMOB).strftime("%H:%M")

        return ParadaEncontrada(
            nome=nome_da_parada or "Parada sem nome cadastrado",
            codigo=_codigo_da_parada(lat, lng),
            lat=lat,
            lng=lng,
            linhas=linhas,
            proximos_horarios=_proximos_horarios(todos_horarios, agora),
        )
