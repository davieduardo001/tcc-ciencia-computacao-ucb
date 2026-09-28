# Deduplicador de notificações — US #22
#
# Controla quais notificações já foram enviadas para cada par
# (usuario_id, numero_linha), impedindo que o Worker dispare a mesma
# notificação repetidamente a cada ciclo de monitoramento.
#
# Estado mantido exclusivamente em memória (dict Python).
# Não usa banco de dados, ORM, Redis ou qualquer persistência externa.
#
# Dois tipos de disparo independentes por corrida:
#   ANTECEDENCIA → enviado quando ETA cruza abaixo de antecedencia_min
#   PROXIMIDADE  → enviado quando ETA cruza abaixo de 5 min (fixo)
#
# O envio de ANTECEDENCIA não impede o envio posterior de PROXIMIDADE.
# O envio de PROXIMIDADE não impede uma nova corrida após reset.
#
# Uma "corrida" representa o trajeto de um ônibus específico se aproximando
# da parada do usuário. Termina (e o estado é resetado) quando o ETA volta
# a subir acima do limiar de antecedência + margem, indicando que o ônibus
# passou ou os dados foram reiniciados.
#
# Thread-safety: o Worker asyncio roda em loop de evento single-thread,
# portanto não há condição de corrida. Se múltiplos workers forem
# introduzidos futuramente, adicionar asyncio.Lock.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enumeração dos tipos de disparo
# ---------------------------------------------------------------------------


class TipoDisparo(Enum):
    """
    Representa os dois limiares de notificação da US #22.

    ANTECEDENCIA: dispara quando ETA <= antecedencia_min configurada pelo
                  usuário (critério de aceite 2 — notificação antecipada).
    PROXIMIDADE:  dispara quando ETA <= LIMIAR_PROXIMIDADE_MINUTOS (5 min),
                  independentemente da configuração do usuário
                  (critério de aceite 1 — ônibus próximo).
    """

    ANTECEDENCIA = "antecedencia"
    PROXIMIDADE = "proximidade"


# ---------------------------------------------------------------------------
# Limiar fixo de proximidade (critério de aceite 1)
# ---------------------------------------------------------------------------

LIMIAR_PROXIMIDADE_MINUTOS: int = 5

# Margem acima do limiar de antecedência usada para detectar o fim de uma
# corrida e resetar o estado. Se ETA > antecedencia_min + MARGEM_RESET,
# considera-se que o ônibus passou ou os dados foram reiniciados.
MARGEM_RESET_MINUTOS: int = 5


# ---------------------------------------------------------------------------
# Estado de envio por par (usuario_id, numero_linha)
# ---------------------------------------------------------------------------


@dataclass
class EstadoEnvio:
    """
    Registra quais disparos já foram realizados para um par
    (usuario_id, numero_linha) na corrida atual.

    Campos:
        antecedencia_enviada: True após o primeiro envio do slot ANTECEDENCIA
        proximidade_enviada:  True após o primeiro envio do slot PROXIMIDADE
        ultimo_envio_em:      timestamp UTC do envio mais recente (ou None)
        ultimo_tipo_enviado:  tipo do envio mais recente (ou None)
    """

    antecedencia_enviada: bool = False
    proximidade_enviada: bool = False
    ultimo_envio_em: Optional[datetime] = field(default=None)
    ultimo_tipo_enviado: Optional[TipoDisparo] = field(default=None)

    def resetar(self) -> None:
        """Limpa o estado da corrida, liberando ambos os slots."""
        self.antecedencia_enviada = False
        self.proximidade_enviada = False
        self.ultimo_envio_em = None
        self.ultimo_tipo_enviado = None


# ---------------------------------------------------------------------------
# Deduplicador principal
# ---------------------------------------------------------------------------


class Deduplicador:
    """
    Controla o envio de notificações para evitar repetições no mesmo ciclo
    de monitoramento.

    Uso esperado pelo Worker (pseudocódigo):
        dedup = Deduplicador()

        # a cada ciclo:
        tipo = dedup.verificar(usuario_id, numero_linha, eta, antecedencia_min)
        if tipo is not None:
            push_sender.enviar_push(...)
            dedup.registrar_envio(usuario_id, numero_linha, tipo)

        # ao detectar fim de corrida (ETA voltou alto):
        dedup.resetar_corrida(usuario_id, numero_linha)

        # para testes:
        dedup.resetar_tudo()
    """

    def __init__(self) -> None:
        # Chave: (usuario_id, numero_linha)
        # Valor: EstadoEnvio da corrida atual
        self._estados: dict[tuple[str, str], EstadoEnvio] = {}

    # ------------------------------------------------------------------
    # API principal
    # ------------------------------------------------------------------

    def verificar(
        self,
        usuario_id: str,
        numero_linha: str,
        eta_minutos: int,
        antecedencia_min: int,
    ) -> Optional[TipoDisparo]:
        """
        Verifica se algum disparo deve ocorrer para este par
        (usuario_id, numero_linha) dado o ETA atual.

        Retorna o TipoDisparo que deve ser realizado, ou None se nenhum
        disparo é necessário (ETA fora dos limiares, já enviado, ou ETA
        voltou alto indicando fim de corrida).

        Lógica de decisão:
            1. Se ETA > antecedencia_min + MARGEM_RESET → reseta corrida,
               retorna None (ônibus passou ou dados reiniciados).
            2. Se ETA <= LIMIAR_PROXIMIDADE_MINUTOS e slot PROXIMIDADE
               ainda não foi enviado → retorna PROXIMIDADE.
               (prioridade sobre ANTECEDENCIA quando os dois limiares
               coincidem, ex: antecedencia_min = 5)
            3. Se ETA <= antecedencia_min e slot ANTECEDENCIA ainda não
               foi enviado e slot PROXIMIDADE ainda não foi enviado
               → retorna ANTECEDENCIA.
               (ANTECEDENCIA não é enviada se PROXIMIDADE já foi — evita
               notificação tardia quando o ônibus já está muito próximo)
            4. Caso contrário → retorna None.

        Args:
            usuario_id:       identificador do usuário
            numero_linha:     número/código da linha (ex: "0.110")
            eta_minutos:      tempo estimado de chegada em minutos inteiros
            antecedencia_min: limiar de antecedência configurado pelo usuário
        """
        chave = (usuario_id, numero_linha)
        estado = self._obter_ou_criar(chave)

        # Passo 1 — detectar fim de corrida (ETA voltou alto)
        if eta_minutos > antecedencia_min + MARGEM_RESET_MINUTOS:
            estado.resetar()
            return None

        # Passo 2 — slot PROXIMIDADE (5 min, fixo — critério de aceite 1)
        if eta_minutos <= LIMIAR_PROXIMIDADE_MINUTOS and not estado.proximidade_enviada:
            return TipoDisparo.PROXIMIDADE

        # Passo 3 — slot ANTECEDENCIA (configurável — critério de aceite 2)
        # Só dispara se PROXIMIDADE ainda não foi enviada. Se o ônibus já
        # está a ≤5 min e nenhuma notificação foi enviada, PROXIMIDADE tem
        # prioridade (passo 2 acima já a captura). Esta condição só é
        # alcançada quando eta > 5, portanto antecedencia_min > 5.
        if (
            eta_minutos <= antecedencia_min
            and not estado.antecedencia_enviada
            and not estado.proximidade_enviada
        ):
            return TipoDisparo.ANTECEDENCIA

        # Passo 4 — nenhum disparo necessário
        return None

    def registrar_envio(
        self,
        usuario_id: str,
        numero_linha: str,
        tipo: TipoDisparo,
    ) -> None:
        """
        Marca o disparo como realizado, bloqueando reenvios do mesmo tipo
        na corrida atual.

        Deve ser chamado pelo Worker imediatamente após o envio bem-sucedido
        (ou mesmo em caso de falha no push — para evitar spam em caso de
        falha recorrente do FCM).

        Args:
            usuario_id:   identificador do usuário
            numero_linha: número/código da linha
            tipo:         TipoDisparo.ANTECEDENCIA ou TipoDisparo.PROXIMIDADE
        """
        chave = (usuario_id, numero_linha)
        estado = self._obter_ou_criar(chave)

        if tipo == TipoDisparo.ANTECEDENCIA:
            estado.antecedencia_enviada = True
        elif tipo == TipoDisparo.PROXIMIDADE:
            estado.proximidade_enviada = True

        estado.ultimo_envio_em = datetime.now(tz=timezone.utc)
        estado.ultimo_tipo_enviado = tipo

    def resetar_corrida(self, usuario_id: str, numero_linha: str) -> None:
        """
        Reseta o estado de uma corrida específica, liberando ambos os slots
        para o próximo ciclo.

        Chamado pelo Worker quando detecta que o ETA voltou alto (ônibus
        passou) ou quando a linha não tem mais dados disponíveis.
        """
        chave = (usuario_id, numero_linha)
        if chave in self._estados:
            self._estados[chave].resetar()

    def resetar_tudo(self) -> None:
        """
        Limpa todo o estado em memória.

        Útil em testes unitários para garantir estado inicial conhecido
        antes de cada caso de teste. Em produção, pode ser chamado ao
        reiniciar o Worker.
        """
        self._estados.clear()

    # ------------------------------------------------------------------
    # Inspeção de estado (para testes e logging)
    # ------------------------------------------------------------------

    def estado(self, usuario_id: str, numero_linha: str) -> EstadoEnvio:
        """
        Retorna uma cópia do EstadoEnvio atual para o par informado.

        Retorna EstadoEnvio vazio (sem envios) se o par ainda não foi visto.
        Útil para asserções em testes e para logging no Worker.
        """
        chave = (usuario_id, numero_linha)
        # Retorna cópia para não expor o estado interno mutável
        est = self._estados.get(chave, EstadoEnvio())
        return EstadoEnvio(
            antecedencia_enviada=est.antecedencia_enviada,
            proximidade_enviada=est.proximidade_enviada,
            ultimo_envio_em=est.ultimo_envio_em,
            ultimo_tipo_enviado=est.ultimo_tipo_enviado,
        )

    def total_corridas_ativas(self) -> int:
        """
        Retorna o número de pares (usuario_id, numero_linha) com estado
        registrado em memória. Útil para monitorar uso de memória em produção.
        """
        return len(self._estados)

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _obter_ou_criar(self, chave: tuple[str, str]) -> EstadoEnvio:
        """Retorna o EstadoEnvio existente ou cria um novo para a chave."""
        if chave not in self._estados:
            self._estados[chave] = EstadoEnvio()
        return self._estados[chave]
