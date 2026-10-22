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

from dataclasses import dataclass, field
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
    # Issue #174 (2): próximos horários DESTA linha (o PRD pede 3 por linha,
    # e não 3 no total misturando as linhas).
    proximos_horarios: list[str] = field(default_factory=list)


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


def vinculos_por_linha(db: Session, parada_id: int) -> dict[str, tuple[RotaParada, Rota]]:
    """
    Um vínculo (parada↔rota) por linha. ~21% das paradas casam IDA e VOLTA
    dentro do raio de vínculo (vias estreitas, lados opostos da rua); vale
    a rota de menor distância ao traçado, que é o lado onde a parada
    realmente está.

    Regra única: o painel da parada (`ParadaService`) e as chegadas
    (`chegada_service`) usam esta função, para nunca divergirem sobre qual
    sentido é o da parada.
    """
    vinculos = (
        db.query(RotaParada, Rota)
        .join(
            Rota,
            and_(Rota.numero == RotaParada.numero, Rota.sentido == RotaParada.sentido),
        )
        .filter(RotaParada.parada_id == parada_id)
        .all()
    )
    por_numero: dict[str, tuple[RotaParada, Rota]] = {}
    for vinculo, rota in vinculos:
        atual = por_numero.get(vinculo.numero)
        if atual is None or vinculo.distancia_ao_trajeto_m < atual[0].distancia_ao_trajeto_m:
            por_numero[vinculo.numero] = (vinculo, rota)
    return por_numero


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

        por_numero = vinculos_por_linha(db, parada.id)
        if not por_numero:
            return None

        horarios_antigos = _horarios_da_lista_antiga(
            db, [r.numero for _, r in por_numero.values() if r.horarios_por_dia is None]
        )

        linhas: list[LinhaNaParada] = []
        todos_horarios: list[str] = []
        for numero, (vinculo, rota) in sorted(por_numero.items()):
            horarios = _horarios_de_hoje(rota, agora, horarios_antigos)
            linhas.append(
                LinhaNaParada(
                    numero=numero,
                    nome=rota.nome,
                    sentido=_rotulo_da_rota(rota),
                    rota_sentido=rota.sentido,
                    ordem=vinculo.ordem,
                    proximos_horarios=_proximos_horarios(horarios, agora.strftime("%H:%M")),
                )
            )
            todos_horarios.extend(horarios)

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
        # Só o necessário para achar a parada: os horários (lista longa por
        # linha) são lidos depois, apenas das linhas que realmente passam aqui.
        colunas = (Linha.numero, Linha.nome, Linha.sentido, Linha.paradas)

        delta_lat = RAIO_MESMA_PARADA_METROS / _METROS_POR_GRAU
        delta_lng = delta_lat / max(cos(radians(lat)), 0.01)

        nome_da_parada: str | None = None
        achadas: list[tuple[str, str, str]] = []

        for numero, nome, sentido, paradas in db.query(*colunas):
            for p in paradas or []:
                # Caixa antes do haversine: a esmagadora maioria dos pontos do
                # catálogo está longe e é descartada com duas subtrações.
                if abs(p["lat"] - lat) > delta_lat or abs(p["lng"] - lng) > delta_lng:
                    continue
                if _distancia_metros(lat, lng, p["lat"], p["lng"]) > RAIO_MESMA_PARADA_METROS:
                    continue
                if nome_da_parada is None and p.get("nome"):
                    nome_da_parada = p["nome"]
                achadas.append((numero, nome, sentido))
                break  # uma parada por linha já basta: não conta a mesma linha duas vezes

        if not achadas:
            return None

        horarios_por_numero = _horarios_da_lista_antiga(db, [n for n, _, _ in achadas])
        linhas: list[LinhaNaParada] = []
        todos_horarios: list[str] = []
        agora_hhmm = agora.strftime("%H:%M")
        for numero, nome, sentido in achadas:
            horarios = horarios_por_numero.get(numero, [])
            linhas.append(
                LinhaNaParada(
                    numero=numero,
                    nome=nome,
                    sentido=sentido,
                    proximos_horarios=_proximos_horarios(horarios, agora_hhmm),
                )
            )
            todos_horarios.extend(horarios)

        return ParadaEncontrada(
            nome=nome_da_parada or "Parada sem nome cadastrado",
            codigo=codigo_da_parada(lat, lng),
            lat=lat,
            lng=lng,
            linhas=linhas,
            proximos_horarios=_proximos_horarios(todos_horarios, agora_hhmm),
        )


def _rotulo_da_rota(rota: Rota) -> str:
    """Mesmo texto que `linha.sentido` mostra no app: "A → B", ou "Circular"."""
    paradas = rota.paradas or []
    pontas = [
        ParadaProxima(nome=p.get("nome", ""), lat=p["lat"], lng=p["lng"])
        for p in (paradas[:1] + paradas[-1:])
    ]
    return rotulo_do_sentido(rota.sentido, pontas)


def _horarios_da_lista_antiga(db: Session, numeros: list[str]) -> dict[str, list[str]]:
    """
    `Linha.horarios_previstos` (lista plana, sem recorte de dia) das linhas
    pedidas, numa única consulta. Antes era uma consulta por rota: com 25
    linhas na parada, eram 25 idas ao banco só para isto.
    """
    if not numeros:
        return {}
    linhas = db.query(Linha.numero, Linha.horarios_previstos).filter(
        Linha.numero.in_(set(numeros))
    )
    return {numero: list(horarios or []) for numero, horarios in linhas}


def _horarios_de_hoje(
    rota: Rota, agora: datetime, horarios_antigos: dict[str, list[str]]
) -> list[str]:
    """
    Saídas do dia corrente (RN-08: nunca mistura dia útil, sábado e
    domingo). Rota ainda sem `horarios_por_dia` (ingestão anterior a esta
    coluna) usa a lista antiga da linha — sem recorte de dia, que é o
    comportamento de antes e não some enquanto a reingestão não roda.
    """
    if rota.horarios_por_dia is not None:
        return horarios_do_dia(rota.horarios_por_dia, agora.weekday())
    return horarios_antigos.get(rota.numero, [])
