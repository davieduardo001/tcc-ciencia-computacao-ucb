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
from collections import deque
from collections.abc import Iterable
from typing import TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from mobilidade.semob_source import URL_POSICAO, _distancia_metros

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from mobilidade.posicoes_colaborativas import FonteColaborativa

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

# ---------------------------------------------------------------------------
# Velocidade efetivamente percorrida (card #179, ⑤b / D3b).
#
# O feed traz a velocidade do INSTANTE. Dividir a distância restante por
# ela oscila muito — 60 km/h numa avenida livre, 5 km/h no semáforo — e
# faz o ETA sumir (< 3 km/h) justo quando o ônibus está só parado num
# ponto. Quanto o ônibus REALMENTE andou nos últimos minutos, parada e
# trânsito inclusos, é um preditor melhor do que ele ainda vai levar.
#
# O histórico fica em memória do processo, com janela curta, e NUNCA é
# persistido: é um cache como o do feed (ADR-04). Processo recém-iniciado
# (o Fly escala a zero) não tem histórico — e então o ETA cai de volta pra
# velocidade instantânea, sem nada quebrar.
# ---------------------------------------------------------------------------

# Quanto do passado entra na média, e quanto de dado é o mínimo pra ela
# valer: com menos que isso, ela só repetiria o ruído do instante.
JANELA_MEDIA_S = 300.0
JANELA_MINIMA_S = 90.0
LEITURAS_MINIMAS_MEDIA = 3

# Quanto histórico guardar por veículo (além disso, é memória à toa).
HISTORICO_MAXIMO_S = 600.0
LEITURAS_MAXIMAS = 40

# Teto de sanidade: deslocamento de GPS com salto não vira "130 km/h".
VELOCIDADE_MEDIA_MAXIMA_KMH = 90.0

_FORMATO_DATA_SEMOB = "%Y-%m-%d %H:%M:%S"


def _fuso_de_brasilia():
    """
    Fuso em que o SEMOB publica o `datalocal`.

    O campo vem sem indicação de fuso ("2026-09-13 22:13:22") e está em
    horário de Brasília. Comparar isso com o relógio do processo só
    funciona por acidente quando a máquina também está em UTC-3: os
    containers do Fly.io rodam em UTC, e lá toda posição parecia ter 3
    horas de idade — o filtro de IDADE_MAXIMA_MINUTOS descartava a frota
    inteira e o mapa nunca mostrava nenhum ônibus.

    Cai para o deslocamento fixo quando a imagem não tem a base de fusos
    instalada. O Brasil não usa horário de verão desde 2019, então
    UTC-3 é exato hoje; o ZoneInfo é preferido para o caso de isso
    mudar.
    """
    try:
        return ZoneInfo("America/Sao_Paulo")
    except ZoneInfoNotFoundError:  # pragma: no cover - depende da imagem
        logger.warning("tzdata indisponível; usando UTC-3 fixo para o SEMOB")
        return timezone(timedelta(hours=-3))


FUSO_SEMOB = _fuso_de_brasilia()


@dataclass(frozen=True)
class PosicaoVeiculo:
    """Um ônibus, onde ele está e quando essa posição foi registrada."""

    prefixo: str
    lat: float
    lng: float
    sentido: str | None
    velocidade: float | None
    # Rumo em graus (0 = norte). Vem no feed como `direcao` e estava
    # sendo descartado — é o que permite apontar o ícone do ônibus na
    # direção em que ele está indo, em vez de um ponto sem orientação.
    direcao: float | None
    atualizado_em: datetime
    operadora: str
    # Velocidade média realmente percorrida nos últimos minutos (km/h), a
    # partir do histórico em memória. `None` quando ainda não há histórico
    # suficiente — quem usa cai para `velocidade`. Ver JANELA_MEDIA_S.
    velocidade_media_kmh: float | None = None
    # US #199 (RN-10/RN-C3) — origem da posição. A SEMOB (que este módulo
    # lê) é sempre "ao_vivo"; o fallback colaborativo injeta veículos com
    # fonte "colaborativo" (posição informada por passageiro) por cima.
    fonte: str = "ao_vivo"


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
        # prefixo → leituras recentes (instante, lat, lng), da mais antiga
        # para a mais nova. Só veículos com linha atribuída.
        self._historico: dict[str, deque[tuple[datetime, float, float]]] = {}

    async def posicoes_da_linha(
        self,
        numero_linha: str,
        *,
        db: Session | None = None,
        colaborativos: FonteColaborativa | None = None,
    ) -> list[PosicaoVeiculo]:
        """
        Veículos rodando a linha informada, com posição recente.

        Lista vazia significa "nenhum veículo em operação" — Cenário 3 da
        US #16. Falha ao consultar o SEMOB também devolve lista vazia:
        o mapa continua mostrando o trajeto, só sem os ônibus.

        US #199 — com `colaborativos` (e `db`), o fallback colaborativo é
        consultado por cima do feed: linhas SEM cobertura SEMOB podem ter
        veículos "colaborativos" (fonte própria, RN-C3) na resposta.
        """
        numero_alvo = numero_linha.strip()
        if not numero_alvo:
            return []

        resultado = await self.posicoes_das_linhas(
            [numero_alvo], db=db, colaborativos=colaborativos
        )
        return resultado.get(numero_alvo, [])

    async def posicoes_das_linhas(
        self,
        numeros_linha: Iterable[str],
        *,
        db: Session | None = None,
        colaborativos: FonteColaborativa | None = None,
    ) -> dict[str, list[PosicaoVeiculo]]:
        """
        Igual a `posicoes_da_linha`, para várias linhas de uma vez —
        usada pela rota planejada (US #159), que precisa das posições de
        todas as linhas envolvidas na viagem. Percorre o feed cacheado
        **uma única vez**, não uma vez por linha: o custo é o mesmo de
        uma chamada só, e não gera nenhuma requisição extra ao SEMOB.
        """
        alvos = {n.strip() for n in numeros_linha if n and n.strip()}
        posicoes: dict[str, list[PosicaoVeiculo]] = {n: [] for n in alvos}
        if not alvos:
            return posicoes

        feed = await self._obter_feed()
        # Em UTC, não no relógio local do processo: o container não sabe
        # em que fuso está e não deve precisar saber.
        agora = datetime.now(timezone.utc)

        for operadora in feed:
            nome_operadora = operadora.get("NomeOperadora", "")

            for feature in operadora.get("features", []):
                propriedades = feature.get("properties", {})
                veiculo = propriedades.get("veiculo") or {}

                numero = (veiculo.get("numero") or "").strip()
                if numero not in alvos:
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
                prefixo = (veiculo.get("prefixo") or "").strip()
                posicoes[numero].append(
                    PosicaoVeiculo(
                        prefixo=prefixo,
                        lat=lat,
                        lng=lng,
                        sentido=(veiculo.get("sentido") or None),
                        velocidade=_converter_numero(propriedades.get("velocidade")),
                        direcao=_converter_numero(propriedades.get("direcao")),
                        atualizado_em=registrado_em,
                        operadora=nome_operadora,
                        velocidade_media_kmh=self._velocidade_media_kmh(prefixo, registrado_em),
                    )
                )

        # US #199 — soma os veículos colaborativos ao feed. Nunca
        # derrubam o mapa: qualquer falha da fonte é engolida e devolvida
        # só com SEMOB (RN-C2: SEMOB vale mais — a colaborativa é a
        # lacuna que ela cobre, não um risco ao que já funciona).
        if colaborativos is not None:
            if db is None:
                logger.warning("Fonte colaborativa pedida sem sessão de banco; ignorada")
            else:
                try:
                    extras = colaborativos.veiculos(db, alvos, posicoes, agora)
                except Exception:  # noqa: BLE001 — o fallback nunca derruba o feed
                    logger.warning("Fonte colaborativa falhou; seguindo só com SEMOB", exc_info=True)
                    extras = {}
                for numero, veiculos_do_fallback in extras.items():
                    posicoes.setdefault(numero, []).extend(veiculos_do_fallback)

        return posicoes

    def _registrar_historico(self, feed: list[dict]) -> None:
        """
        Guarda, por veículo com linha atribuída, a posição de cada leitura
        nova do feed. Chamado a cada download — o histórico cresce com o
        tempo de vida do processo, e a janela curta o mantém pequeno.
        """
        agora = datetime.now(timezone.utc)
        limite = agora - timedelta(seconds=HISTORICO_MAXIMO_S)

        for operadora in feed:
            for feature in operadora.get("features", []):
                propriedades = feature.get("properties", {})
                veiculo = propriedades.get("veiculo") or {}

                prefixo = (veiculo.get("prefixo") or "").strip()
                if not prefixo or not (veiculo.get("numero") or "").strip():
                    continue  # frota parada, sem viagem atribuída

                coordenadas = (feature.get("geometry") or {}).get("coordinates")
                if not coordenadas or len(coordenadas) < 2:
                    continue

                registrado_em = _converter_data(propriedades.get("datalocal"))
                if registrado_em is None or registrado_em < limite:
                    continue

                fila = self._historico.get(prefixo)
                if fila is None:
                    fila = self._historico[prefixo] = deque(maxlen=LEITURAS_MAXIMAS)
                # A mesma leitura reaparece enquanto o veículo não reporta
                # de novo; só entra o que é mais novo que o último.
                if fila and fila[-1][0] >= registrado_em:
                    continue
                fila.append((registrado_em, coordenadas[1], coordenadas[0]))

        # Poda quem parou de reportar (garagem, fim de turno).
        for prefixo in [p for p, fila in self._historico.items() if not fila or fila[-1][0] < limite]:
            del self._historico[prefixo]

    def _velocidade_media_kmh(self, prefixo: str, ate: datetime) -> float | None:
        """
        Média do que o veículo percorreu nos últimos JANELA_MEDIA_S, somando
        o deslocamento entre leituras consecutivas — então parada e
        semáforo entram na conta, ao contrário da velocidade instantânea.

        `None` com histórico insuficiente (poucas leituras, ou menos de
        JANELA_MINIMA_S de intervalo entre a primeira e a última).
        """
        fila = self._historico.get(prefixo)
        if not fila:
            return None

        desde = ate - timedelta(seconds=JANELA_MEDIA_S)
        leituras = [leitura for leitura in fila if desde <= leitura[0] <= ate]
        if len(leituras) < LEITURAS_MINIMAS_MEDIA:
            return None

        duracao_s = (leituras[-1][0] - leituras[0][0]).total_seconds()
        if duracao_s < JANELA_MINIMA_S:
            return None

        metros = sum(
            _distancia_metros(a[1], a[2], b[1], b[2]) for a, b in zip(leituras, leituras[1:])
        )
        return min(metros / duracao_s * 3.6, VELOCIDADE_MEDIA_MAXIMA_KMH)

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
        try:
            self._registrar_historico(feed)
        except Exception:  # noqa: BLE001 — o histórico é um extra; nunca derruba o feed
            logger.warning("Falha ao registrar o histórico de posições", exc_info=True)
        return feed


def _converter_data(valor: str | None) -> datetime | None:
    """
    `datalocal` do SEMOB para datetime com fuso.

    A string não traz fuso nenhum, mas é horário de Brasília — ver
    FUSO_SEMOB. Devolver com fuso explícito evita que a comparação
    dependa de onde o processo está rodando.
    """
    if not valor:
        return None
    try:
        return datetime.strptime(valor, _FORMATO_DATA_SEMOB).replace(tzinfo=FUSO_SEMOB)
    except ValueError:
        return None


def _converter_numero(valor: object) -> float | None:
    """
    O SEMOB manda velocidade e direção como string decimal com vírgula
    ("41", "218,72"). Vale para os dois campos.
    """
    if valor is None:
        return None
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return None
