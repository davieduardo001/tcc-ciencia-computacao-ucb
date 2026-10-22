# Identidade de parada física — US #173
#
# O /pontos do SEMOB não tem ID e repete o mesmo abrigo em registros
# vizinhos. Este módulo funde esses registros em paradas físicas únicas e
# as vincula às rotas. É lógica pura (sem banco): a ingestão chama e grava.
#
# Raio de fusão de 10 m, medido sobre os dados reais (4.654 abrigos
# associados a algum trajeto): resulta em 4.318 paradas e só 1 das 307
# fusões junta lados opostos da rua em sentidos exclusivos da mesma
# linha. Com 5 m sobravam duplicatas; com 15 m o risco não melhora e
# funde mais.

from __future__ import annotations

import zlib
from collections import defaultdict
from dataclasses import dataclass

from mobilidade.geometria import TrajetoMedido, distancia_metros, mais_proximo

RAIO_FUSAO_M = 10.0

# Mesmo lado de célula de semob_source (~55 m): >= ao raio, então 3x3
# células cobrem toda a vizinhança.
_LADO_CELULA_GRAUS = 0.0005

_ESPACO_CODIGOS = 100_000


@dataclass(frozen=True)
class PontoParada:
    """Um abrigo como publicado pelo SEMOB (antes da fusão)."""

    nome: str
    lat: float
    lng: float


@dataclass(frozen=True)
class ParadaFisica:
    codigo: str
    nome: str
    lat: float
    lng: float
    membros: tuple[PontoParada, ...]


@dataclass(frozen=True)
class VinculoRota:
    parada: ParadaFisica
    ordem: int
    indice_trajeto: int
    distancia_acumulada_m: float
    distancia_ao_trajeto_m: float


def chave_do_ponto(lat: float, lng: float) -> tuple[float, float]:
    """Chave de um abrigo, igual à usada por semob_source para deduplicar."""
    return (round(lat, 6), round(lng, 6))


def fundir_pontos(pontos: list[PontoParada]) -> list[ParadaFisica]:
    """
    Agrupa abrigos a até RAIO_FUSAO_M uns dos outros (encadeado: A perto
    de B e B perto de C funde os três) e devolve uma parada por grupo,
    posicionada no centróide.

    Determinístico: a mesma entrada, em qualquer ordem, gera os mesmos
    códigos — a ingestão mensal não pode trocar o código de uma parada.
    """
    unicos = sorted(set(pontos), key=lambda p: (p.lat, p.lng, p.nome))

    pai = list(range(len(unicos)))

    def raiz(i: int) -> int:
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i

    grade: dict[tuple[int, int], list[int]] = defaultdict(list)
    for i, p in enumerate(unicos):
        grade[(int(p.lat / _LADO_CELULA_GRAUS), int(p.lng / _LADO_CELULA_GRAUS))].append(i)

    for i, p in enumerate(unicos):
        ci, cj = int(p.lat / _LADO_CELULA_GRAUS), int(p.lng / _LADO_CELULA_GRAUS)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for j in grade.get((ci + di, cj + dj), ()):
                    if j <= i:
                        continue
                    q = unicos[j]
                    if distancia_metros(p.lat, p.lng, q.lat, q.lng) <= RAIO_FUSAO_M:
                        pai[raiz(i)] = raiz(j)

    grupos: dict[int, list[PontoParada]] = defaultdict(list)
    for i, p in enumerate(unicos):
        grupos[raiz(i)].append(p)

    # Ordena pelos centróides para a atribuição de códigos (e o
    # desempate de colisões) não depender da ordem de entrada.
    centroides = []
    for membros in grupos.values():
        lat = sum(m.lat for m in membros) / len(membros)
        lng = sum(m.lng for m in membros) / len(membros)
        centroides.append((lat, lng, membros))
    centroides.sort(key=lambda c: (c[0], c[1]))

    usados: set[str] = set()
    paradas = []
    for lat, lng, membros in centroides:
        codigo = _codigo_livre(lat, lng, usados)
        usados.add(codigo)
        paradas.append(
            ParadaFisica(
                codigo=codigo,
                nome=_nome_do_grupo(lat, lng, membros),
                lat=lat,
                lng=lng,
                membros=tuple(membros),
            )
        )
    return paradas


def codigo_da_parada(lat: float, lng: float, tentativa: int = 0) -> str:
    """
    Código curto derivado do centróide: a mesma parada gera o mesmo código
    em toda ingestão. `tentativa` desempata colisões (ver `_codigo_livre`).
    """
    chave = f"{lat:.5f},{lng:.5f}".encode()
    return f"PR-{(zlib.crc32(chave) + tentativa) % _ESPACO_CODIGOS:05d}"


def _codigo_livre(lat: float, lng: float, usados: set[str]) -> str:
    # ~4.300 paradas num espaço de 100.000 códigos: colisão (paradoxo do
    # aniversário) é esperada, não rara. Sondagem linear determinística.
    for tentativa in range(_ESPACO_CODIGOS):
        codigo = codigo_da_parada(lat, lng, tentativa)
        if codigo not in usados:
            return codigo
    raise RuntimeError("Espaço de códigos de parada esgotado")


def _nome_do_grupo(lat: float, lng: float, membros: list[PontoParada]) -> str:
    """Nome do abrigo mais próximo do centróide que tenha nome."""
    com_nome = [m for m in membros if m.nome]
    if not com_nome:
        return ""
    return min(com_nome, key=lambda m: distancia_metros(lat, lng, m.lat, m.lng)).nome


def indexar_por_ponto(paradas: list[ParadaFisica]) -> dict[tuple[float, float], ParadaFisica]:
    """Do abrigo original (por `chave_do_ponto`) para a parada que o absorveu."""
    return {
        chave_do_ponto(m.lat, m.lng): parada for parada in paradas for m in parada.membros
    }


def vincular(
    trajeto: TrajetoMedido,
    pontos_da_rota: list[PontoParada],
    parada_do_ponto: dict[tuple[float, float], ParadaFisica],
) -> list[VinculoRota]:
    """
    Posição de cada parada física ao longo de uma rota.

    Dois abrigos da mesma parada física podem estar ambos a menos de 40 m
    do traçado; vale o mais próximo dele (a unicidade é por rota+parada).
    O resultado sai na ordem em que o ônibus passa — não na ordem de
    entrada — e `ordem` é a posição nessa sequência.
    """
    melhor: dict[str, tuple[int, float, ParadaFisica]] = {}

    for ponto in pontos_da_rota:
        parada = parada_do_ponto.get(chave_do_ponto(ponto.lat, ponto.lng))
        if parada is None:
            continue
        indice, distancia = mais_proximo(trajeto.pontos, (ponto.lat, ponto.lng))
        if indice is None:
            continue
        atual = melhor.get(parada.codigo)
        if atual is None or distancia < atual[1]:
            melhor[parada.codigo] = (indice, distancia, parada)

    ordenados = sorted(melhor.values(), key=lambda m: (m[0], m[2].codigo))
    return [
        VinculoRota(
            parada=parada,
            ordem=ordem,
            indice_trajeto=indice,
            distancia_acumulada_m=trajeto.acumulado[indice],
            distancia_ao_trajeto_m=round(distancia, 2),
        )
        for ordem, (indice, distancia, parada) in enumerate(ordenados)
    ]
