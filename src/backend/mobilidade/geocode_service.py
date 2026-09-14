# Geocodificação de origem e destino — US #20.
#
# Por que existe: os nomes de parada que a ingestão do SEMOB produz são
# endereços de rua ("SHSN Chácara 67 Condomínio Bom Fim, Ceilândia",
# "Eixo L Norte, SQN 207"). Ninguém digita isso. Para o usuário informar
# "de onde para onde", ele precisa buscar por ponto de referência —
# "Rodoviária", "UnB", "Shopping Taguatinga" — e isso exige um
# geocodificador.
#
# Usamos o Nominatim do OpenStreetMap: gratuito, sem chave e sem
# billing, da mesma família do tile server que o Leaflet já consome.
# Deliberadamente NÃO usamos a Geocoding API do Google, que exige conta
# de faturamento ativa.
#
# Roda no backend, e não direto no navegador, por três motivos:
#   1. A política de uso do Nominatim exige um User-Agent identificando
#      a aplicação — o navegador não deixa definir esse cabeçalho.
#   2. A mesma política pede no máximo 1 requisição por segundo; só dá
#      pra garantir isso em um ponto central.
#   3. O cache é compartilhado entre todos os usuários.

from __future__ import annotations

import asyncio
import logging
import time
import unicodedata
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

URL_BUSCA = "https://nominatim.openstreetmap.org/search"
URL_REVERSA = "https://nominatim.openstreetmap.org/reverse"

# A política de uso do Nominatim exige identificar a aplicação.
USER_AGENT = (
    "Movecity-TCC-UCB/1.0 "
    "(projeto academico; github.com/davieduardo001/tcc-ciencia-computacao-ucb)"
)

# Caixa que cobre o Distrito Federal e o entorno imediato. Restringe os
# resultados: sem isso, "Rodoviária" traz a de São Paulo primeiro.
VIEWBOX_DF = "-48.40,-15.40,-47.25,-16.15"

# Intervalo mínimo entre chamadas, em segundos (política do Nominatim).
INTERVALO_MINIMO_S = 1.1

TIMEOUT_S = 8.0
MIN_CARACTERES = 3
MAX_RESULTADOS = 6

# Tempo de vida do cache. Ponto de referência não muda de lugar; o prazo
# existe só pra corrigir eventual resultado ruim sem redeploy.
CACHE_SEGUNDOS = 24 * 60 * 60


@dataclass(frozen=True)
class Lugar:
    nome: str
    endereco: str
    lat: float
    lng: float


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore")
    return " ".join(sem_acento.decode("ascii").lower().split())


class GeocodeService:
    """
    Busca de lugares por nome, com cache e respeito ao limite de uso.

    Nunca lança exceção para o chamador: geocodificação é um auxílio de
    busca, e uma falha de rede no Nominatim não deve derrubar a tela de
    planejamento de viagem. Em qualquer erro devolve lista vazia, e a
    UI continua oferecendo "usar minha localização" e clicar no mapa.
    """

    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, list[Lugar]]] = {}
        self._ultima_chamada = 0.0
        self._trava = asyncio.Lock()

    async def buscar(self, termo: str) -> list[Lugar]:
        termo_normalizado = _normalizar(termo)
        if len(termo_normalizado) < MIN_CARACTERES:
            return []

        em_cache = self._do_cache(termo_normalizado)
        if em_cache is not None:
            return em_cache

        dados = await self._chamar(
            URL_BUSCA,
            {
                "q": f"{termo}, Distrito Federal, Brasil",
                "format": "jsonv2",
                "limit": str(MAX_RESULTADOS),
                "countrycodes": "br",
                "viewbox": VIEWBOX_DF,
                "bounded": "1",
                "addressdetails": "1",
            },
        )
        if dados is None:
            return []

        lugares = [lugar for lugar in map(self._para_lugar, dados) if lugar]
        self._cache[termo_normalizado] = (time.monotonic(), lugares)
        return lugares

    async def reverso(self, lat: float, lng: float) -> Lugar | None:
        """
        Nome legível para um ponto — usado por "usar minha localização" e
        pelo clique no mapa, pra que o campo não fique mostrando
        coordenada crua.
        """
        chave = f"rev:{lat:.5f},{lng:.5f}"
        em_cache = self._do_cache(chave)
        if em_cache is not None:
            return em_cache[0] if em_cache else None

        dados = await self._chamar(
            URL_REVERSA,
            {
                "lat": f"{lat}",
                "lon": f"{lng}",
                "format": "jsonv2",
                "zoom": "18",
                "addressdetails": "1",
            },
        )
        if dados is None:
            return None

        lugar = self._para_lugar(dados if isinstance(dados, dict) else None)
        self._cache[chave] = (time.monotonic(), [lugar] if lugar else [])
        return lugar

    # -- internos ----------------------------------------------------------

    def _do_cache(self, chave: str) -> list[Lugar] | None:
        entrada = self._cache.get(chave)
        if entrada is None:
            return None
        gravado_em, valor = entrada
        if time.monotonic() - gravado_em > CACHE_SEGUNDOS:
            del self._cache[chave]
            return None
        return valor

    async def _chamar(self, url: str, params: dict[str, str]) -> object | None:
        """
        Faz a chamada respeitando o intervalo mínimo entre requisições.

        A trava serializa as chamadas de propósito: a política do
        Nominatim é sobre a aplicação inteira, não por usuário. Como
        quase tudo é servido do cache, na prática isso raramente
        segura alguém.
        """
        try:
            async with self._trava:
                espera = INTERVALO_MINIMO_S - (time.monotonic() - self._ultima_chamada)
                if espera > 0:
                    await asyncio.sleep(espera)
                self._ultima_chamada = time.monotonic()

                async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
                    resposta = await client.get(
                        url, params=params, headers={"User-Agent": USER_AGENT}
                    )
                    resposta.raise_for_status()
                    return resposta.json()
        except Exception:
            logger.warning("Geocodificação indisponível (%s)", url, exc_info=True)
            return None

    @staticmethod
    def _para_lugar(bruto: object) -> Lugar | None:
        if not isinstance(bruto, dict):
            return None
        try:
            lat = float(bruto["lat"])
            lng = float(bruto["lon"])
        except (KeyError, TypeError, ValueError):
            return None

        endereco = bruto.get("display_name") or ""
        nome = bruto.get("name") or endereco.split(",")[0].strip()
        if not nome:
            return None

        return Lugar(nome=nome, endereco=endereco, lat=lat, lng=lng)
