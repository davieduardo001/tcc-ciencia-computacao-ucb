# Detalhes de uma parada — US #18 / #173
#
# A parada é resolvida pela tabela `parada` (identidade única, populada
# pela ingestão — ver paradas_fisicas.py): o código é o mesmo qualquer que
# seja a linha pela qual o usuário chegou a ela.
#
# Enquanto a ingestão ainda não rodou depois do deploy (a tabela existe
# mas está vazia), ou para uma coordenada sem parada cadastrada perto, o
# serviço cai no caminho anterior: varrer `Linha.paradas` (JSON), em que
# uma parada compartilhada aparece uma vez em cada linha. Isso evita que
# /paradas responda 404 em todo lugar entre o deploy e a reingestão.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import asin, cos, radians, sin, sqrt

from sqlalchemy import and_
from sqlalchemy.orm import Session

from mobilidade.models.linha import Linha
from mobilidade.models.parada import Parada, RotaParada
from mobilidade.models.rota import Rota
from mobilidade.paradas_fisicas import codigo_da_parada
from mobilidade.posicao_service import FUSO_SEMOB
from mobilidade.semob_source import ParadaProxima, horarios_do_dia, rotulo_do_sentido

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


_METROS_POR_GRAU = 111_320.0


@dataclass(frozen=True)
class LinhaNaParada:
    numero: str
    nome: str
    sentido: str
    # Preenchidos só quando a parada vem da tabela `parada`: sentido da
    # rota ("IDA"/"VOLTA"/"CIRCULAR") e posição da parada nela.
    rota_sentido: str | None = None
    ordem: int | None = None


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
        agora = datetime.now(FUSO_SEMOB)
        encontrada = self._por_parada_fisica(db, lat, lng, agora)
        if encontrada is not None:
            return encontrada
        return self._por_linhas_cacheadas(db, lat, lng, agora)

    def _por_parada_fisica(
        self, db: Session, lat: float, lng: float, agora: datetime
    ) -> ParadaEncontrada | None:
        delta_lat = RAIO_MESMA_PARADA_METROS / _METROS_POR_GRAU
        delta_lng = delta_lat / max(cos(radians(lat)), 0.01)
        candidatas = (
            db.query(Parada)
            .filter(
                Parada.lat.between(lat - delta_lat, lat + delta_lat),
                Parada.lng.between(lng - delta_lng, lng + delta_lng),
            )
            .all()
        )
        dentro_do_raio = [
            (d, p)
            for p in candidatas
            if (d := _distancia_metros(lat, lng, p.lat, p.lng)) <= RAIO_MESMA_PARADA_METROS
        ]
        if not dentro_do_raio:
            return None
        parada = min(dentro_do_raio, key=lambda c: c[0])[1]

        vinculos = (
            db.query(RotaParada, Rota)
            .join(
                Rota,
                and_(Rota.numero == RotaParada.numero, Rota.sentido == RotaParada.sentido),
            )
            .filter(RotaParada.parada_id == parada.id)
            .all()
        )
        if not vinculos:
            return None

        # Uma entrada por linha. ~21% das paradas casam IDA e VOLTA
        # dentro do raio de vínculo (vias estreitas); vale a rota de
        # menor distância ao traçado, que é o lado onde a parada está.
        por_numero: dict[str, tuple[RotaParada, Rota]] = {}
        for vinculo, rota in vinculos:
            atual = por_numero.get(vinculo.numero)
            if atual is None or vinculo.distancia_ao_trajeto_m < atual[0].distancia_ao_trajeto_m:
                por_numero[vinculo.numero] = (vinculo, rota)

        linhas: list[LinhaNaParada] = []
        todos_horarios: list[str] = []
        for numero, (vinculo, rota) in sorted(por_numero.items()):
            linhas.append(
                LinhaNaParada(
                    numero=numero,
                    nome=rota.nome,
                    sentido=_rotulo_da_rota(rota),
                    rota_sentido=rota.sentido,
                    ordem=vinculo.ordem,
                )
            )
            todos_horarios.extend(_horarios_de_hoje(db, rota, agora))

        return ParadaEncontrada(
            nome=parada.nome or "Parada sem nome cadastrado",
            codigo=parada.codigo,
            lat=parada.lat,
            lng=parada.lng,
            linhas=linhas,
            proximos_horarios=_proximos_horarios(todos_horarios, agora.strftime("%H:%M")),
        )

    def _por_linhas_cacheadas(
        self, db: Session, lat: float, lng: float, agora: datetime
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

        return ParadaEncontrada(
            nome=nome_da_parada or "Parada sem nome cadastrado",
            codigo=codigo_da_parada(lat, lng),
            lat=lat,
            lng=lng,
            linhas=linhas,
            proximos_horarios=_proximos_horarios(todos_horarios, agora.strftime("%H:%M")),
        )


def _rotulo_da_rota(rota: Rota) -> str:
    """Mesmo texto que `linha.sentido` mostra no app: "A → B", ou "Circular"."""
    paradas = rota.paradas or []
    pontas = [
        ParadaProxima(nome=p.get("nome", ""), lat=p["lat"], lng=p["lng"])
        for p in (paradas[:1] + paradas[-1:])
    ]
    return rotulo_do_sentido(rota.sentido, pontas)


def _horarios_de_hoje(db: Session, rota: Rota, agora: datetime) -> list[str]:
    """
    Saídas do dia corrente. Rota ainda sem `horarios_por_dia` (ingestão
    anterior a esta coluna) usa a lista antiga da linha — sem recorte de
    dia, que é o comportamento de antes e não some enquanto a reingestão
    não roda.
    """
    if rota.horarios_por_dia is not None:
        return horarios_do_dia(rota.horarios_por_dia, agora.weekday())
    linha = db.query(Linha.horarios_previstos).filter(Linha.numero == rota.numero).first()
    return list(linha[0]) if linha and linha[0] else []
