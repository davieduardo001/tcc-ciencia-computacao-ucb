# Posição dos ônibus em tempo real — US #16
#
# Fonte: GET /posicao do SEMOB, o mesmo feed que alimenta o app oficial
# DF no Ponto. Devolve GeoJSON por operadora, com a posição de toda a
# frota do DF (~3.500 veículos) numa única resposta — não dá pra pedir
# "só a linha X", então filtramos aqui.
#
# Diferente das linhas (que são estáticas e entram por ingestão em lote),
# posição muda o tempo todo: aqui a leitura é ao vivo, com um cache curto
# em memória. O cache é do feed inteiro, não por linha: como o SEMOB
# devolve tudo de uma vez, um download serve todos os usuários e todas as
# linhas ao mesmo tempo.
#
# Nem todo veículo informa qual linha está fazendo: medido em 13/09/2026,
# 531 de 2.428 veículos com posição recente traziam `numero` preenchido —
# o resto é frota parada, sem viagem atribuída. Por isso uma linha sem
# veículo é situação normal (Cenário 3 da US #16), não erro.

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime

import httpx

from mobilidade.semob_source import URL_POSICAO

logger = logging.getLogger(__name__)

# Quanto tempo o feed baixado vale antes de buscar de novo. O SEMOB
# atualiza a cada poucos segundos; 20s mantém a tela viva sem martelar
# a origem a cada usuário que abrir o mapa.
CACHE_SEGUNDOS = 20.0

# Acima disso a posição é velha demais pra ser exibida como "ao vivo".
# Veículo em garagem chega a ficar dias com a última posição registrada.
IDADE_MAXIMA_MINUTOS = 15.0

# Teto pro download do feed. Medido: o SEMOB responde entre ~0,3 s e
# ~25 s pro mesmo payload. Como a renovação roda em segundo plano, um
# timeout generoso não prejudica ninguém — só desiste do que travou.
TIMEOUT_SEGUNDOS = 25.0

_FORMATO_DATA_SEMOB = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class PosicaoVeiculo:
    """Um ônibus, onde ele está e quando essa posição foi registrada."""

    prefixo: str
    lat: float
    lng: float
    sentido: str | None
    velocidade: float | None
    atualizado_em: datetime
    operadora: str


class PosicaoService:
    """
    Leitura ao vivo do feed de GPS, com cache curto compartilhado.

    O cache é de instância: a rota usa um único PosicaoService no
    processo, então o feed é baixado no máximo uma vez a cada
    CACHE_SEGUNDOS, independente de quantos usuários estejam com o mapa
    aberto.
    """

    def __init__(self, cache_segundos: float = CACHE_SEGUNDOS) -> None:
        self._cache_segundos = cache_segundos
        self._feed: list[dict] | None = None
        self._baixado_em: float = 0.0
        # Guarda a task de renovação em andamento: sem a referência o
        # garbage collector pode cancelá-la no meio, e sem a checagem
        # dez usuários simultâneos disparariam dez downloads iguais.
        self._renovando: asyncio.Task | None = None

    async def posicoes_da_linha(self, numero_linha: str) -> list[PosicaoVeiculo]:
        """
        Veículos rodando a linha informada, com posição recente.

        Lista vazia significa "nenhum veículo em operação" — Cenário 3 da
        US #16. Falha ao consultar o SEMOB também devolve lista vazia:
        o mapa continua mostrando o trajeto, só sem os ônibus.
        """
        numero_alvo = numero_linha.strip()
        if not numero_alvo:
            return []

        feed = await self._obter_feed()
        agora = datetime.now()
        posicoes: list[PosicaoVeiculo] = []

        for operadora in feed:
            nome_operadora = operadora.get("NomeOperadora", "")

            for feature in operadora.get("features", []):
                propriedades = feature.get("properties", {})
                veiculo = propriedades.get("veiculo") or {}

                if (veiculo.get("numero") or "").strip() != numero_alvo:
                    continue

                coordenadas = (feature.get("geometry") or {}).get("coordinates")
                if not coordenadas or len(coordenadas) < 2:
                    continue

                registrado_em = _converter_data(propriedades.get("datalocal"))
                if registrado_em is None:
                    continue
                if (agora - registrado_em).total_seconds() > IDADE_MAXIMA_MINUTOS * 60:
                    continue

                lng, lat = coordenadas[0], coordenadas[1]
                posicoes.append(
                    PosicaoVeiculo(
                        prefixo=(veiculo.get("prefixo") or "").strip(),
                        lat=lat,
                        lng=lng,
                        sentido=(veiculo.get("sentido") or None),
                        velocidade=_converter_velocidade(propriedades.get("velocidade")),
                        atualizado_em=registrado_em,
                        operadora=nome_operadora,
                    )
                )

        return posicoes

    async def _obter_feed(self) -> list[dict]:
        """
        Feed de GPS, servido do cache sempre que houver algo em cache.

        Quando o cache vence, devolve o feed antigo **na hora** e dispara
        a renovação em segundo plano, em vez de fazer o usuário esperar
        o download.

        O motivo é medido: o `/posicao` são ~870 KB e o tempo de resposta
        do SEMOB oscila muito — numa amostra deu 2,6 s, 3,4 s, 6,0 s e
        24,8 s. Como o front faz polling a cada 20 s, aguardar o download
        a cada vencimento significaria travar a tela justamente quando a
        origem está lenta. Servir o feed anterior custa, no pior caso,
        alguns segundos de defasagem na posição — e o filtro de
        IDADE_MAXIMA_MINUTOS continua descartando o que ficar velho
        demais.

        A única espera acontece na partida a frio, quando não há nada em
        cache pra servir.
        """
        if self._feed is None:
            return await self._baixar()

        if (time.monotonic() - self._baixado_em) >= self._cache_segundos:
            self._agendar_renovacao()

        return self._feed

    def _agendar_renovacao(self) -> None:
        if self._renovando is not None and not self._renovando.done():
            return
        try:
            self._renovando = asyncio.create_task(self._baixar())
        except RuntimeError:
            # Sem event loop rodando (ex: chamada síncrona em teste):
            # segue com o feed em cache, sem renovar.
            self._renovando = None

    async def _baixar(self) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SEGUNDOS) as client:
                resposta = await client.get(URL_POSICAO)
                resposta.raise_for_status()
                feed = resposta.json()
        except (httpx.HTTPError, ValueError):
            logger.warning("Feed de posição do SEMOB indisponível", exc_info=True)
            # Mantém o último feed conhecido — melhor uma posição de
            # alguns segundos atrás do que nenhuma.
            return self._feed or []

        self._feed = feed
        self._baixado_em = time.monotonic()
        return feed


def _converter_data(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.strptime(valor, _FORMATO_DATA_SEMOB)
    except ValueError:
        return None


def _converter_velocidade(valor: object) -> float | None:
    """O SEMOB manda velocidade como string, às vezes com vírgula."""
    if valor is None:
        return None
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return None
