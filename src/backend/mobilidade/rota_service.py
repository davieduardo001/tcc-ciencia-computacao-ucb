# Cálculo de rota origem → destino por ônibus — US #20.
#
# Responde "quais linhas me levam daqui até ali, onde embarco e onde
# desço", usando só os dados que a ingestão do SEMOB já traz: a
# geometria real de cada rota e os abrigos de parada geocodificados.
#
# O que este serviço NÃO faz, de propósito: planejar por horário ("saia
# 7h12, baldeie às 7h48"). Isso exige um motor de roteamento temporal
# sobre GTFS (RAPTOR/CSA) e está registrado na US #115.

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import tuple_ as sql_tuple
from sqlalchemy.orm import Session

from mobilidade.models.rota import Rota, RotaCelula
from mobilidade.semob_source import _distancia_metros

logger = logging.getLogger(__name__)

# Lado da célula do índice espacial, em graus (~275 m). A busca olha as
# 3x3 células ao redor do ponto, então o alcance efetivo a pé fica entre
# ~275 m e ~550 m dependendo de onde o ponto cai dentro da célula.
LADO_CELULA_GRAUS = 0.0025

# Distância máxima a pé, em metros, entre o ponto informado e o traçado
# da linha. Aplicado depois do índice, sobre a geometria de verdade.
RAIO_CAMINHADA_METROS = 800.0

# Quantas rotas candidatas do índice chegam a ter a geometria carregada
# para o cálculo preciso. Segura o custo quando a origem é um corredor
# movimentado (a Rodoviária do Plano Piloto tem dezenas de linhas).
MAX_CANDIDATAS = 25

# Até onde uma parada conhecida pode estar do ponto de embarque para dar
# nome a ele. Além disso o front mostra a coordenada — melhor não ter
# nome do que apontar a parada errada.
DISTANCIA_MAXIMA_NOME_PARADA = 250.0

# Quantas opções o serviço devolve em cada modalidade.
MAX_DIRETAS = 8
MAX_BALDEACOES = 5

# Velocidade média usada para estimar duração. É um ônibus urbano em
# trânsito misto do DF: não é promessa de horário, é ordem de grandeza.
# Planejamento por horário real é a US #115.
VELOCIDADE_MEDIA_KMH = 22.0


def celula(lat: float, lng: float) -> tuple[int, int]:
    return (int(lat // LADO_CELULA_GRAUS), int(lng // LADO_CELULA_GRAUS))


def celulas_vizinhas(lat: float, lng: float) -> list[tuple[int, int]]:
    ci, cj = celula(lat, lng)
    return [(ci + di, cj + dj) for di in (-1, 0, 1) for dj in (-1, 0, 1)]


@dataclass(frozen=True)
class PontoEmbarque:
    """Onde subir ou descer, e quanto se caminha até lá."""

    lat: float
    lng: float
    parada_nome: str
    caminhada_metros: int


@dataclass(frozen=True)
class Perna:
    """Um trecho feito dentro de um mesmo ônibus."""

    numero: str
    sentido: str
    nome: str
    embarque: PontoEmbarque
    desembarque: PontoEmbarque
    distancia_km: float
    paradas_no_trecho: int
    trajeto: list[tuple[float, float]]


@dataclass(frozen=True)
class OpcaoViagem:
    """Uma forma de fazer a viagem: uma ou duas pernas de ônibus."""

    pernas: list[Perna]

    @property
    def baldeacoes(self) -> int:
        return len(self.pernas) - 1

    @property
    def distancia_km(self) -> float:
        return round(sum(p.distancia_km for p in self.pernas), 1)

    @property
    def caminhada_metros(self) -> int:
        # A caminhada do desembarque de uma perna até o embarque da
        # seguinte é a própria baldeação, já contada no embarque.
        return self.pernas[0].embarque.caminhada_metros + sum(
            p.desembarque.caminhada_metros for p in self.pernas
        ) + sum(p.embarque.caminhada_metros for p in self.pernas[1:])

    @property
    def duracao_estimada_min(self) -> int:
        minutos = self.distancia_km / VELOCIDADE_MEDIA_KMH * 60
        minutos += self.caminhada_metros / 1000 / 5.0 * 60  # 5 km/h a pé
        minutos += 6 * self.baldeacoes  # espera média no ponto de troca
        return max(1, round(minutos))


class RotaService:
    """
    Busca por geometria: em vez de casar nomes de parada (que no SEMOB
    são endereços de rua, inúteis para digitar), casa as coordenadas de
    origem e destino contra o traçado de cada rota.

    Uma rota serve à viagem quando passa perto da origem, perto do
    destino, e **nessa ordem** — a comparação de índices ao longo do
    traçado é o que faz IDA e VOLTA se separarem sozinhas.
    """

    def calcular(
        self,
        db: Session,
        origem: tuple[float, float],
        destino: tuple[float, float],
        raio_metros: float = RAIO_CAMINHADA_METROS,
    ) -> list[OpcaoViagem]:
        """
        Opções de viagem entre dois pontos, diretas primeiro.

        Devolve lista vazia quando não há nenhuma — Cenário 3 da US.
        """
        if _distancia_metros(*origem, *destino) < 2 * raio_metros:
            # Origem e destino na mesma vizinhança: sugerir ônibus aqui
            # seria pior do que não sugerir nada.
            return []

        perto_origem = self._rotas_perto(db, origem)
        perto_destino = self._rotas_perto(db, destino)

        if not perto_origem or not perto_destino:
            return []

        diretas = self._diretas(db, perto_origem, perto_destino, origem, destino, raio_metros)
        if diretas:
            return diretas[:MAX_DIRETAS]

        return self._com_baldeacao(
            db, perto_origem, perto_destino, origem, destino, raio_metros
        )

    # -- índice espacial ---------------------------------------------------

    def _rotas_perto(
        self, db: Session, ponto: tuple[float, float]
    ) -> dict[tuple[str, str], tuple[int, int]]:
        """
        Rotas que passam pelas 3x3 células ao redor do ponto, com a
        janela de índices do trajeto observada ali.

        Uma consulta indexada em `rota_celula`, sem tocar na geometria.
        """
        celulas = celulas_vizinhas(*ponto)
        registros = (
            db.query(
                RotaCelula.numero,
                RotaCelula.sentido,
                RotaCelula.indice_min,
                RotaCelula.indice_max,
            )
            .filter(sql_tuple(RotaCelula.cel_lat, RotaCelula.cel_lng).in_(celulas))
            .all()
        )

        janelas: dict[tuple[str, str], tuple[int, int]] = {}
        for numero, sentido, minimo, maximo in registros:
            chave = (numero, sentido)
            atual = janelas.get(chave)
            if atual is None:
                janelas[chave] = (minimo, maximo)
            else:
                janelas[chave] = (min(atual[0], minimo), max(atual[1], maximo))
        return janelas

    # -- viagens diretas ---------------------------------------------------

    def _diretas(
        self,
        db: Session,
        perto_origem: dict[tuple[str, str], tuple[int, int]],
        perto_destino: dict[tuple[str, str], tuple[int, int]],
        origem: tuple[float, float],
        destino: tuple[float, float],
        raio_metros: float,
    ) -> list[OpcaoViagem]:
        candidatas = [
            chave
            for chave in perto_origem.keys() & perto_destino.keys()
            # O ônibus precisa passar na origem antes do destino.
            if perto_origem[chave][0] < perto_destino[chave][1]
        ]
        if not candidatas:
            return []

        # Ordena pela janela mais curta antes de cortar: o índice já
        # indica quais viagens são as mais diretas.
        candidatas.sort(key=lambda c: perto_destino[c][1] - perto_origem[c][0])

        opcoes: list[OpcaoViagem] = []
        for rota in self._carregar(db, candidatas[:MAX_CANDIDATAS]):
            perna = self._montar_perna(rota, origem, destino, raio_metros)
            if perna is not None:
                opcoes.append(OpcaoViagem(pernas=[perna]))

        opcoes.sort(key=lambda o: (o.duracao_estimada_min, o.caminhada_metros))
        return opcoes

    # -- viagens com uma baldeação ----------------------------------------

    def _com_baldeacao(
        self,
        db: Session,
        perto_origem: dict[tuple[str, str], tuple[int, int]],
        perto_destino: dict[tuple[str, str], tuple[int, int]],
        origem: tuple[float, float],
        destino: tuple[float, float],
        raio_metros: float,
    ) -> list[OpcaoViagem]:
        """
        Uma baldeação: rota A pega perto da origem, rota B deixa perto do
        destino, e as duas se cruzam em algum ponto.

        Só uma baldeação, de propósito. Duas ou mais começa a produzir
        itinerários que ninguém faria na prática sem levar horário em
        conta, e horário é a US #115.
        """
        saindo = sorted(perto_origem.keys() - perto_destino.keys())[:MAX_CANDIDATAS]
        chegando = sorted(perto_destino.keys() - perto_origem.keys())[:MAX_CANDIDATAS]
        if not saindo or not chegando:
            return []

        celulas_a = self._celulas_por_rota(db, saindo)
        celulas_b = self._celulas_por_rota(db, chegando)

        # Pares de rotas que se cruzam. Para cada par, o ponto de troca
        # escolhido é o que **minimiza a viagem inteira** — trecho
        # rodado na perna A até a troca, mais trecho da perna B da troca
        # até o destino.
        #
        # A primeira versão disto maximizava o avanço na perna A, o que
        # parecia razoável e era péssimo na prática: Aeroporto→UnB saía
        # com 60 km e ~3 h, porque a troca era empurrada pro fim de uma
        # linha circular. Como os pontos do traçado são mais ou menos
        # equidistantes, a diferença de índices serve de proxy barato
        # para distância, sem carregar geometria nenhuma aqui.
        pares: list[tuple[int, tuple[str, str], tuple[str, str], tuple[int, int]]] = []
        for a in saindo:
            partida_a = perto_origem[a][0]
            for b in chegando:
                chegada_b = perto_destino[b][1]
                comuns = celulas_a[a].keys() & celulas_b[b].keys()

                melhor_custo, melhor_cel = None, None
                for c in comuns:
                    troca_a = celulas_a[a][c][0]
                    troca_b = celulas_b[b][c][0]
                    if troca_a <= partida_a:
                        continue  # a troca aconteceria antes de eu embarcar
                    if troca_b >= chegada_b:
                        continue  # depois da troca, B já passou do destino
                    custo = (troca_a - partida_a) + (chegada_b - troca_b)
                    if melhor_custo is None or custo < melhor_custo:
                        melhor_custo, melhor_cel = custo, c

                if melhor_cel is not None:
                    pares.append((melhor_custo, a, b, melhor_cel))

        if not pares:
            return []

        pares.sort(key=lambda p: p[0])
        pares = pares[: MAX_BALDEACOES * 4]

        necessarias = {a for _, a, _, _ in pares} | {b for _, _, b, _ in pares}
        rotas = {(r.numero, r.sentido): r for r in self._carregar(db, sorted(necessarias))}

        opcoes: list[OpcaoViagem] = []
        vistos: set[tuple[str, str, str, str]] = set()
        for _, a, b, cel in pares:
            rota_a, rota_b = rotas.get(a), rotas.get(b)
            if rota_a is None or rota_b is None:
                continue

            assinatura = (a[0], a[1], b[0], b[1])
            if assinatura in vistos:
                continue

            troca = self._centro_da_celula(cel)
            perna_a = self._montar_perna(rota_a, origem, troca, raio_metros)
            if perna_a is None:
                continue

            # A segunda perna parte de onde a primeira **de fato**
            # deixou o passageiro, não do centro da célula de troca.
            # Medir contra a célula faria a "caminhada até a próxima
            # linha" ser um número inventado.
            desceu = (perna_a.desembarque.lat, perna_a.desembarque.lng)
            perna_b = self._montar_perna(rota_b, desceu, destino, raio_metros)
            if perna_b is None:
                continue

            vistos.add(assinatura)
            opcoes.append(OpcaoViagem(pernas=[perna_a, perna_b]))
            if len(opcoes) >= MAX_BALDEACOES:
                break

        opcoes.sort(key=lambda o: (o.duracao_estimada_min, o.caminhada_metros))
        return opcoes

    def _celulas_por_rota(
        self, db: Session, rotas: list[tuple[str, str]]
    ) -> dict[tuple[str, str], dict[tuple[int, int], tuple[int, int]]]:
        registros = (
            db.query(
                RotaCelula.numero,
                RotaCelula.sentido,
                RotaCelula.cel_lat,
                RotaCelula.cel_lng,
                RotaCelula.indice_min,
                RotaCelula.indice_max,
            )
            .filter(sql_tuple(RotaCelula.numero, RotaCelula.sentido).in_(rotas))
            .all()
        )
        saida: dict[tuple[str, str], dict[tuple[int, int], tuple[int, int]]] = {
            rota: {} for rota in rotas
        }
        for numero, sentido, cel_lat, cel_lng, minimo, maximo in registros:
            saida.setdefault((numero, sentido), {})[(cel_lat, cel_lng)] = (minimo, maximo)
        return saida

    @staticmethod
    def _centro_da_celula(cel: tuple[int, int]) -> tuple[float, float]:
        return (
            (cel[0] + 0.5) * LADO_CELULA_GRAUS,
            (cel[1] + 0.5) * LADO_CELULA_GRAUS,
        )

    # -- geometria ---------------------------------------------------------

    def _carregar(self, db: Session, chaves: list[tuple[str, str]]) -> list[Rota]:
        if not chaves:
            return []
        return (
            db.query(Rota)
            .filter(sql_tuple(Rota.numero, Rota.sentido).in_(chaves))
            .all()
        )

    def _montar_perna(
        self,
        rota: Rota,
        origem: tuple[float, float],
        destino: tuple[float, float],
        raio_metros: float,
    ) -> Perna | None:
        """
        Confere o palpite do índice contra a geometria de verdade e
        calcula embarque, desembarque e distância percorrida.

        O índice trabalha em células de ~275 m, então ele aproxima: aqui
        é onde a distância a pé é medida de fato e a candidata pode ser
        descartada.
        """
        trajeto = [(float(lat), float(lng)) for lat, lng in (rota.trajeto or [])]
        if len(trajeto) < 2:
            return None

        i_origem, d_origem = self._mais_proximo(trajeto, origem)
        if d_origem > raio_metros:
            return None

        # O desembarque só pode estar depois do embarque.
        i_destino, d_destino = self._mais_proximo(trajeto, destino, inicio=i_origem + 1)
        if i_destino is None or d_destino > raio_metros:
            return None

        percorrido = sum(
            _distancia_metros(*trajeto[i], *trajeto[i + 1])
            for i in range(i_origem, i_destino)
        )
        if percorrido < 300:
            # Trecho curto demais pra justificar pegar ônibus.
            return None

        paradas = [
            (p.get("nome", ""), float(p.get("lat", 0.0)), float(p.get("lng", 0.0)))
            for p in (rota.paradas or [])
        ]

        embarque, i_parada_embarque = self._ponto(trajeto[i_origem], origem, paradas)
        desembarque, i_parada_desembarque = self._ponto(
            trajeto[i_destino], destino, paradas
        )

        # `paradas` já vem na ordem em que a linha passa (ver
        # semob_source.paradas_ao_longo_do_trajeto), então quantas
        # paradas há no trecho é a diferença entre os dois índices —
        # sem nenhum cálculo de distância extra.
        #
        # O índice é a parada mais próxima *sem limite de distância*, de
        # propósito: para contar, só importa a posição ao longo da rota.
        # O limite de 250 m vale só pra decidir se dá pra usar o nome
        # dela. Misturar as duas coisas fazia uma viagem de 27 km ser
        # exibida como "0 paradas" quando o desembarque caía longe de
        # qualquer abrigo cadastrado.
        paradas_no_trecho = max(0, i_parada_desembarque - i_parada_embarque)

        return Perna(
            numero=rota.numero,
            sentido=rota.sentido,
            nome=rota.nome,
            embarque=embarque,
            desembarque=desembarque,
            distancia_km=round(percorrido / 1000, 1),
            paradas_no_trecho=paradas_no_trecho,
            trajeto=trajeto[i_origem : i_destino + 1],
        )

    @staticmethod
    def _mais_proximo(
        trajeto: list[tuple[float, float]],
        alvo: tuple[float, float],
        inicio: int = 0,
    ) -> tuple[int | None, float]:
        melhor_i, melhor_d = None, float("inf")
        for i in range(inicio, len(trajeto)):
            d = _distancia_metros(*trajeto[i], *alvo)
            if d < melhor_d:
                melhor_i, melhor_d = i, d
        return melhor_i, melhor_d

    @staticmethod
    def _ponto(
        no_trajeto: tuple[float, float],
        informado: tuple[float, float],
        paradas: list[tuple[str, float, float]],
    ) -> tuple[PontoEmbarque, int]:
        """
        Nomeia o embarque/desembarque pela parada conhecida mais próxima
        do ponto do traçado, devolvendo também a posição dela na lista.

        Quando a parada mais próxima está longe demais, usa a coordenada
        do traçado e nome vazio — o front mostra o ponto no mapa.
        Apontar uma parada a 2 km seria pior do que não ter nome. O
        índice, porém, é devolvido do mesmo jeito: ele serve pra contar
        paradas no trecho, e pra isso só a posição importa.
        """
        indice, melhor = 0, float("inf")
        for i, (_, plat, plng) in enumerate(paradas):
            d = _distancia_metros(*no_trajeto, plat, plng)
            if d < melhor:
                melhor, indice = d, i

        if not paradas or melhor > DISTANCIA_MAXIMA_NOME_PARADA:
            return (
                PontoEmbarque(
                    lat=no_trajeto[0],
                    lng=no_trajeto[1],
                    parada_nome="",
                    caminhada_metros=round(_distancia_metros(*no_trajeto, *informado)),
                ),
                indice,
            )

        nome, lat, lng = paradas[indice]
        return (
            PontoEmbarque(
                lat=lat,
                lng=lng,
                parada_nome=nome,
                caminhada_metros=round(_distancia_metros(lat, lng, *informado)),
            ),
            indice,
        )
