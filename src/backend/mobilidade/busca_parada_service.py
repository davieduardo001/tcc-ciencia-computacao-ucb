# Buscar parada por nome ou endereço — US #21.
#
# Duas etapas, na ordem do diagrama de sequência (UC21):
#   1. Nome: o termo é procurado no nome das paradas físicas (tabela
#      `parada`, populada pela ingestão — ver paradas_fisicas.py).
#   2. Endereço / ponto de referência: sem parada com aquele nome, o termo
#      é geocodificado (GeocodeService, o mesmo da US #20) e voltam as
#      paradas num raio de 500 m do lugar encontrado.
#
# Sem PostGIS (ADR-02): o raio usa o mesmo padrão de
# `chegada_service.paradas_proximas_do_usuario` — caixa de lat/lng no SQL,
# servida pelo índice `ix_parada_lat_lng`, e distância exata (haversine)
# em Python só para as poucas candidatas que sobram.

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from math import cos, radians
from typing import Literal

from sqlalchemy import func
from sqlalchemy.orm import Session

from mobilidade.geocode_service import GeocodeService, Lugar
from mobilidade.geometria import distancia_metros
from mobilidade.models.parada import Parada, RotaParada

# Critério da issue: "paradas mais próximas" de um endereço = raio de 500 m.
RAIO_ENDERECO_M = 500.0

# Mesmo mínimo do geocodificador: com 1–2 letras quase toda parada casa.
MIN_CARACTERES = 3

MAX_RESULTADOS = 20

# Teto de candidatas lidas do banco na busca por nome, antes de ordenar.
# Um termo genérico ("sul", "qd") casa com centenas de paradas; o usuário
# não vai ler além das primeiras, então não vale trazer todas.
MAX_CANDIDATAS_NOME = 200

_METROS_POR_GRAU = 111_320.0

# Os nomes vêm do SEMOB com acento ("Ceilândia") e ninguém digita acento
# no celular. `translate` é nativo do Postgres; a extensão `unaccent`
# exigiria CREATE EXTENSION no Neon, como o PostGIS.
_COM_ACENTO = "áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ"
_SEM_ACENTO = "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC"

TipoBusca = Literal["nome", "endereco", "nenhum"]


@dataclass(frozen=True)
class ParadaBuscada:
    codigo: str
    nome: str
    lat: float
    lng: float
    qtd_linhas: int
    # Só na busca por endereço: distância até o lugar geocodificado.
    distancia_m: int | None = None


@dataclass(frozen=True)
class ResultadoBusca:
    tipo: TipoBusca
    paradas: list[ParadaBuscada]
    # Só na busca por endereço: o lugar em torno do qual o mapa centraliza.
    referencia: Lugar | None = None


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore")
    return " ".join(sem_acento.decode("ascii").lower().split())


def _escapar_like(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _consulta_com_linhas(db: Session):
    """
    Paradas com a quantidade de linhas que passam por elas. O join deixa de
    fora a parada sem nenhuma linha vinculada: ela não responde à pergunta
    da US ("quais linhas passam por ali").
    """
    return (
        db.query(Parada, func.count(func.distinct(RotaParada.numero)))
        .join(RotaParada, RotaParada.parada_id == Parada.id)
        .group_by(Parada.id)
    )


class BuscaParadaService:
    """US #21 — Buscar Parada por Nome ou Endereço."""

    def __init__(self, geocode_service: GeocodeService) -> None:
        self._geocode = geocode_service

    async def buscar(self, db: Session, termo: str) -> ResultadoBusca:
        termo_normalizado = _normalizar(termo)
        if len(termo_normalizado) < MIN_CARACTERES:
            return ResultadoBusca(tipo="nenhum", paradas=[])

        # Cenário 1 — busca por nome de parada.
        por_nome = self.buscar_por_nome(db, termo_normalizado)
        if por_nome:
            return ResultadoBusca(tipo="nome", paradas=por_nome)

        # Cenário 2 — endereço ou ponto de referência. O primeiro lugar do
        # Nominatim é o mais relevante (ele já ordena por importância).
        lugares = await self._geocode.buscar(termo)
        if lugares:
            referencia = lugares[0]
            proximas = self.buscar_em_raio(db, referencia.lat, referencia.lng)
            if proximas:
                return ResultadoBusca(tipo="endereco", paradas=proximas, referencia=referencia)

        # Cenário 3 — nada por nome nem perto do endereço.
        return ResultadoBusca(tipo="nenhum", paradas=[])

    def buscar_por_nome(self, db: Session, termo_normalizado: str) -> list[ParadaBuscada]:
        """
        Cada palavra do termo precisa aparecer no nome, em qualquer ordem:
        "502 w3" acha "W3 Sul, SQS 502". Nomes que começam pelo termo vêm
        primeiro; depois, ordem alfabética.
        """
        nome_sem_acento = func.lower(func.translate(Parada.nome, _COM_ACENTO, _SEM_ACENTO))
        consulta = _consulta_com_linhas(db)
        for palavra in termo_normalizado.split():
            consulta = consulta.filter(
                nome_sem_acento.like(f"%{_escapar_like(palavra)}%", escape="\\")
            )

        candidatas = consulta.limit(MAX_CANDIDATAS_NOME).all()

        def ordem(item: tuple[Parada, int]) -> tuple[int, str]:
            nome = _normalizar(item[0].nome)
            return (0 if nome.startswith(termo_normalizado) else 1, nome)

        return [
            ParadaBuscada(
                codigo=parada.codigo,
                nome=parada.nome,
                lat=parada.lat,
                lng=parada.lng,
                qtd_linhas=qtd_linhas,
            )
            for parada, qtd_linhas in sorted(candidatas, key=ordem)[:MAX_RESULTADOS]
        ]

    def buscar_em_raio(
        self, db: Session, lat: float, lng: float, raio_m: float = RAIO_ENDERECO_M
    ) -> list[ParadaBuscada]:
        """Paradas a até `raio_m` de (lat, lng), da mais próxima para a mais distante."""
        delta_lat = raio_m / _METROS_POR_GRAU
        delta_lng = delta_lat / max(cos(radians(lat)), 0.01)

        candidatas = (
            _consulta_com_linhas(db)
            .filter(
                Parada.lat.between(lat - delta_lat, lat + delta_lat),
                Parada.lng.between(lng - delta_lng, lng + delta_lng),
            )
            .all()
        )

        dentro_do_raio = [
            (distancia, parada, qtd_linhas)
            for parada, qtd_linhas in candidatas
            if (distancia := distancia_metros(lat, lng, parada.lat, parada.lng)) <= raio_m
        ]
        dentro_do_raio.sort(key=lambda item: item[0])

        return [
            ParadaBuscada(
                codigo=parada.codigo,
                # Parada só com CEP no SEMOB fica sem nome (ver
                # semob_source.nome_da_parada) — o front mostra um rótulo neutro.
                nome=parada.nome,
                lat=parada.lat,
                lng=parada.lng,
                qtd_linhas=qtd_linhas,
                distancia_m=round(distancia),
            )
            for distancia, parada, qtd_linhas in dentro_do_raio[:MAX_RESULTADOS]
        ]
