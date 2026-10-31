# Fallback colaborativo — US #199.
#
# Quando o ônibus NÃO reporta posição na SEMOB (feed ausente, posição
# velha ou ônibus sem sentido — Cenário 3 da US #16), passageiros a bordo,
# com consentimento explícito, podem cadastrar onde o ônibus está e um
# `PosicaoVeiculo` "colaborativo" entra no fluxo de ETA no lugar. RN-C2:
# a posição da SEMOB vale mais — ela sempre ganha, e o selo RN-C3 declara
# a origem ("colaborativo", distinto de "ao vivo").
#
# LGPD (RN-C1): nada aqui toca banco, disco ou log. As leituras ficam em
# memória com validade curta (120 s) e nunca levam identificador de
# usuário. A prova do consentimento (versão do texto aceito) é a única
# coisa persistida, na própria viagem — ver models/viagem.py.
#
# Armazenamento: interface mínima (guardar, obter, apagar, expirar) para
# que trocar a memória do processo por um armazenamento compartilhado
# depois seja trocar a implementação — o serviço escala a zero e pode ter
# mais de uma instância (min_machines_running = 0), e a memória local não
# é compartilhada entre elas. Com uma instância (hoje), funciona; a troca
# é uma decisão de deploy, não de código.

from __future__ import annotations

import logging
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal, Protocol

from sqlalchemy.orm import Session

from mobilidade.eta_service import TOLERANCIA_TRAJETO_M
from mobilidade.geometria import distancia_metros
from mobilidade.models.rota import Rota
from mobilidade.models.viagem import Viagem
from mobilidade.posicao_service import (
    VELOCIDADE_MEDIA_MAXIMA_KMH,
    PosicaoVeiculo,
)

if TYPE_CHECKING:
    from mobilidade.rota_service import RotaService

logger = logging.getLogger(__name__)

# Tempo de vida de uma leitura. 2 min cobre o intervalo entre leituras do
# passageiro (10-15 s) com folga para um buraco de rede — o selo honesto
# não pode mostrar uma posição de 10 minutos atrás como "colaborativo".
VALIDADE_SEGUNDOS = 120.0

# Teto de leituras por viagem. 120 s a cada 10-15 s de envio ≈ 8-12;
# guardar mais é memória à toa.
LEITURAS_MAXIMAS = 12

# Anti-martelada: 1 leitura a cada 10 s por viagem (o feed da SEMOB é
# cacheado por 20 s; ler mais rápido não melhora nada).
INTERVALO_MINIMO_ENVIO_S = 10.0

# Um ônibus SEMOB da linha, no sentido da viagem, a menos de isto da
# leitura colaborativa torna a redundante: RN-C2, SEMOB vence.
RAIO_ONIBUS_SEMOB_M = 100.0

# Mínimo de janela para a velocidade média valer (2 leituras consecutivas
# com ao menos isto de intervalo): com menos, ela só repete o ruído do
# instante — igual ao princípio de JANELA_MEDIA_S do SEMOB, só que a janela
# colaborativa mal pode passar de VALIDADE_SEGUNDOS (120 s).
JANELA_VELOCIDADE_MINIMA_S = 30.0

# Prune da tabela de rate-limit: entradas mais velhas que isto são de
# viagens encerradas há tempo — vão revogadas, expiradas ou podadas.
PRUNE_ENVIO_SEGUNDOS = 600.0

MOTIVO_ACEITA = "aceita"
MOTIVO_FORA_DO_TRACADO = "fora_do_tracado"
MOTIVO_VELOCIDADE_IMPOSSIVEL = "velocidade_impossivel"

MotivoLeitura = Literal["aceita", "fora_do_tracado", "velocidade_impossivel"]


@dataclass(frozen=True)
class LeituraColaborativa:
    """
    Uma leitura de GPS de passageiro: posição do ÔNIBUS, não do celular
    do usuário. Vive só na memória do processo (validade curta) e nunca
    vai para banco, disco ou log.
    """

    # UTC com fuso — é comparado com posições COM fuso (PosicaoVeiculo e
    # o `agora` aware das rotas).
    instante: datetime
    lat: float
    lng: float


class ArmazenamentoPosicoesColaborativas(ABC):
    """
    Onde as leituras colaborativas vivem entre o POST e o ETA.

    Interface propositalmente mínima — guardar, obter, apagar, expirar —
    para trocar memória local por armazenamento compartilhado depois sem
    tocar uma linha do serviço.
    """

    @abstractmethod
    def guardar(self, viagem_id: uuid.UUID, leitura: LeituraColaborativa) -> None:
        ...

    @abstractmethod
    def obter(self, viagem_id: uuid.UUID) -> list[LeituraColaborativa]:
        ...

    @abstractmethod
    def apagar(self, viagem_id: uuid.UUID) -> None:
        ...

    @abstractmethod
    def expirar(self) -> int:
        ...


class ArmazenamentoEmMemoria(ArmazenamentoPosicoesColaborativas):
    """
    Dicionário do processo: viagem → leituras recentes.

    `obter` e `expirar` podam o que venceu — o mesmo que `validar-até-lá`
    vigiado à toa. `obter` é lido por TODA consulta de mapa com fallback
    ativo, então a poda vencida acontece mesmo sem o sweep periódico.
    """

    def __init__(
        self,
        validade_s: float = VALIDADE_SEGUNDOS,
        leituras_max: int = LEITURAS_MAXIMAS,
    ) -> None:
        self._validade_s = validade_s
        self._leituras_max = leituras_max
        self._lock = threading.Lock()
        self._por_viagem: dict[uuid.UUID, deque[LeituraColaborativa]] = {}

    def _dentro_da_validade(self, leitura: LeituraColaborativa, agora: datetime) -> bool:
        return (agora - leitura.instante).total_seconds() <= self._validade_s

    def guardar(self, viagem_id: uuid.UUID, leitura: LeituraColaborativa) -> None:
        with self._lock:
            fila = self._por_viagem.get(viagem_id)
            if fila is None:
                fila = self._por_viagem[viagem_id] = deque(maxlen=self._leituras_max)
            fila.append(leitura)

    def obter(self, viagem_id: uuid.UUID) -> list[LeituraColaborativa]:
        with self._lock:
            fila = self._por_viagem.get(viagem_id)
            if fila is None:
                return []
            agora = datetime.now(timezone.utc)
            validas = [leitura for leitura in fila if self._dentro_da_validade(leitura, agora)]
            # Poda na leitura: o deque de backup nunca cresce sem limite.
            self._por_viagem[viagem_id] = deque(validas, maxlen=self._leituras_max)
            return list(validas)

    def apagar(self, viagem_id: uuid.UUID) -> None:
        with self._lock:
            self._por_viagem.pop(viagem_id, None)

    def expirar(self) -> int:
        with self._lock:
            agora = datetime.now(timezone.utc)
            descartadas = 0
            for viagem_id in list(self._por_viagem):
                validas = [
                    leitura
                    for leitura in self._por_viagem[viagem_id]
                    if self._dentro_da_validade(leitura, agora)
                ]
                descartadas += len(self._por_viagem[viagem_id]) - len(validas)
                if not validas:
                    del self._por_viagem[viagem_id]
        return descartadas


class EnvioAdiantado(Exception):
    """Leitura antes do intervalo mínimo — anti-martelada (best-effort)."""


class ServicoPosicoesColaborativas:
    """
    Regras do fallback colaborativo (US #199).

    Entrada — `registrar`: valida e guarda uma leitura nova.
    Saída — `veiculos`: produz o `PosicaoVeiculo` "colaborativo" (fonte
    distinta, RN-C3) para cada viagem compartilhando cuja linha não tem
    cobertura SEMOB equivalente (RN-C2). A posteriori, quem injeta no
    ETA chama este método via `PosicaoService.posicoes_das_linhas`.

    O limite de taxa e o armazenamento vivem no processo: com mais de
    uma instância do serviço, cada uma limita/guarda o seu (documentado
    no cabeçalho; leve e consciente).
    """

    def __init__(
        self,
        armazenamento: ArmazenamentoPosicoesColaborativas | None = None,
        intervalo_minimo_s: float = INTERVALO_MINIMO_ENVIO_S,
    ) -> None:
        self._armazenamento = armazenamento or ArmazenamentoEmMemoria()
        self._intervalo_minimo_s = intervalo_minimo_s
        self._lock = threading.Lock()
        # viagem_id → último aceite (monotonic). Só anti-martelada: efêmero
        # e local, igual ao armazenamento.
        self._ultimo_envio: dict[uuid.UUID, float] = {}

    # ------------------------------------------------------------------
    # Entrada — POST /viagens/{id}/posicao
    # ------------------------------------------------------------------

    def registrar(
        self,
        db: Session,
        viagem: Viagem,
        lat: float,
        lng: float,
        *,
        rota_service: RotaService,
        agora: datetime | None = None,
    ) -> MotivoLeitura:
        """
        Valida e guarda a leitura, devolvendo o motivo do resultado.

        Ordem das checagens (a mais barata primeiro, e a que depende do
        banco o mais fundo): limite de taxa → velocidade incremental →
        encaixe no traçado. Descartar uma leitura não a guarda: a próxima,
        coerente, entra.

        O consentimento vigente NÃO é checado aqui: quem chama já garantiu
        ("viagem ativa com `compartilha_posicao_em` setado"). Nenhuma
        coordenada entra em log em qualquer caminho.
        """
        agora = agora or datetime.now(timezone.utc)
        if agora.tzinfo is None:
            agora = agora.replace(tzinfo=timezone.utc)

        agora_mono = time.monotonic()
        with self._lock:
            ultimo = self._ultimo_envio.get(viagem.id)
        if (
            ultimo is not None
            and (agora_mono - ultimo) < self._intervalo_minimo_s
        ):
            raise EnvioAdiantado()

        leituras = self._armazenamento.obter(viagem.id)
        if leituras:
            anterior = leituras[-1]
            intervalo = (agora - anterior.instante).total_seconds()
            if intervalo > 0:
                kmh = (
                    distancia_metros(anterior.lat, anterior.lng, lat, lng)
                    / intervalo
                    * 3.6
                )
                if kmh > VELOCIDADE_MEDIA_MAXIMA_KMH:
                    # Salto que ônibus nenhum faz (spoofing, GPS furado):
                    # descarta a leitura, deixa o histórico limpo.
                    return MOTIVO_VELOCIDADE_IMPOSSIVEL

        if not self._encaixa_no_tracado(db, rota_service, viagem, lat, lng):
            return MOTIVO_FORA_DO_TRACADO

        self._armazenamento.guardar(viagem.id, LeituraColaborativa(instante=agora, lat=lat, lng=lng))
        with self._lock:
            self._ultimo_envio[viagem.id] = agora_mono
        return MOTIVO_ACEITA

    def _encaixa_no_tracado(
        self,
        db: Session,
        rota_service: RotaService,
        viagem: Viagem,
        lat: float,
        lng: float,
    ) -> bool:
        """
        RN-C4 — a leitura precisa encaixar no traçado da linha (a mesma
        tolerância de 150 m do ETA). Checa os sentidos da linha e o sentido
        da viagem: o passageiro está num ônibus DELA, e os traçados de ida
        e volta se sobrepõem na maior parte do caminho.

        Linha sem rota ingerida: não há traçado contra o qual validar →
        recusa (RN-C5: sem dado confiável, não inventa). Estas linhas
        também não teriam ETA por trajeto de qualquer forma.
        """
        sentidos = {s for (s,) in db.query(Rota.sentido).filter(Rota.numero == viagem.numero_linha).distinct().all() if s}
        if viagem.sentido:
            sentidos.add(viagem.sentido)

        for sentido in sorted(sentidos):
            medido = rota_service.trajeto_medido(db, viagem.numero_linha, sentido)
            if medido is None:
                continue
            if medido[0].indice_mais_proximo((lat, lng), TOLERANCIA_TRAJETO_M) is not None:
                return True

        logger.warning(
            "Leitura colaborativa fora do traçado descartada (linha=%s)",
            viagem.numero_linha,
        )
        return False

    # ------------------------------------------------------------------
    # Saída — o PosicaoVeiculo do fallback
    # ------------------------------------------------------------------

    def veiculos(
        self,
        db: Session,
        alvos: set[str],
        semob: dict[str, list[PosicaoVeiculo]],
        agora: datetime,
    ) -> dict[str, list[PosicaoVeiculo]]:
        """
        Um `PosicaoVeiculo` `colaborativo` por viagem compartilhando da
        linha pedida, SEM cobertura SEMOB equivalente (RN-C2):

          — mesmo prefixo no feed (o ônibus que ela embarcou voltou ao
            feed), ou
          — algum ônibus SEMOB da linha, no sentido da viagem, a menos de
            RAIO_ONIBUS_SEMOB_M da leitura.

        `agora` COM fuso (é o mesmo `agora` das posições SEMOB).
        """
        self.expirar()

        viagens = (
            db.query(Viagem)
            .filter(
                Viagem.encerrada_em.is_(None),
                Viagem.compartilha_posicao_em.isnot(None),
                Viagem.numero_linha.in_(sorted(alvos)),
            )
            .all()
        )
        if not viagens:
            return {}

        resultado: dict[str, list[PosicaoVeiculo]] = {}
        for viagem in viagens:
            leituras = self._armazenamento.obter(viagem.id)
            if not leituras:
                continue  # sem leitura recente, sem veículo a mostrar
            ultima = leituras[-1]
            da_linha = semob.get(viagem.numero_linha, [])
            if self._semob_cobre(viagem, da_linha, ultima):
                continue

            media = self._velocidade_media_kmh(leituras)
            resultado.setdefault(viagem.numero_linha, []).append(
                PosicaoVeiculo(
                    # O prefixo é o do ônibus real em que ela embarcou —
                    # identificador público do feed da SEMOB, não do usuário.
                    prefixo=viagem.veiculo_prefixo,
                    lat=ultima.lat,
                    lng=ultima.lng,
                    sentido=viagem.sentido,
                    # Sem velocidade do instante (não vem de GPS): quem
                    # consome usa a média; com só uma leitura, sem ETA.
                    velocidade=None,
                    direcao=None,
                    atualizado_em=ultima.instante,
                    operadora="colaborativo",
                    velocidade_media_kmh=media,
                    fonte="colaborativo",
                )
            )
        return resultado

    def _semob_cobre(
        self,
        viagem: Viagem,
        da_linha: list[PosicaoVeiculo],
        ultima: LeituraColaborativa,
    ) -> bool:
        if not da_linha:
            return False

        # 1) O ônibus em que ela embarcou voltou ao feed: SEMOB vence.
        if viagem.veiculo_prefixo in {v.prefixo for v in da_linha}:
            return True

        # 2) Algum ônibus da linha, NO SENTIDO da viagem, ao lado da
        # leitura: a SEMOB já está contando essa história sozinha.
        sentido = (viagem.sentido or "").strip().upper()
        for v in da_linha:
            if sentido and (v.sentido or "").strip().upper() != sentido:
                continue
            if distancia_metros(ultima.lat, ultima.lng, v.lat, v.lng) <= RAIO_ONIBUS_SEMOB_M:
                return True
        return False

    def _velocidade_media_kmh(self, leituras: list[LeituraColaborativa]) -> float | None:
        """
        Média do que o ônibus percorreu entre leituras consecutivas — o
        mesmo princípio de `_velocidade_media_kmh` do SEMOB (parada e
        semáforo entram), sobre a janela efêmera do passageiro.
        """
        if len(leituras) < 2:
            return None
        duracao_s = (leituras[-1].instante - leituras[0].instante).total_seconds()
        if duracao_s < JANELA_VELOCIDADE_MINIMA_S:
            return None
        metros = sum(
            distancia_metros(a.lat, a.lng, b.lat, b.lng)
            for a, b in zip(leituras, leituras[1:])
        )
        return min(metros / duracao_s * 3.6, VELOCIDADE_MEDIA_MAXIMA_KMH)

    # ------------------------------------------------------------------
    # Revogação e poda
    # ------------------------------------------------------------------

    def apagar(self, viagem_id: uuid.UUID) -> None:
        """Revogação ("Parar"), "Cheguei" e limpeza: memória vazia na hora."""
        self._armazenamento.apagar(viagem_id)
        with self._lock:
            self._ultimo_envio.pop(viagem_id, None)

    def expirar(self) -> int:
        """Poda leituras vencidas e entradas de viagens encerradas há tempo."""
        agora_mono = time.monotonic()
        with self._lock:
            self._ultimo_envio = {
                viagem_id: quando
                for viagem_id, quando in self._ultimo_envio.items()
                if (agora_mono - quando) <= PRUNE_ENVIO_SEGUNDOS
            }
        return self._armazenamento.expirar()


class FonteColaborativa(Protocol):
    """O que o PosicaoService entende como fonte de posições colaborativas."""

    def veiculos(
        self,
        db: Session,
        alvos: set[str],
        semob: dict[str, list[PosicaoVeiculo]],
        agora: datetime,
    ) -> dict[str, list[PosicaoVeiculo]]:
        ...
