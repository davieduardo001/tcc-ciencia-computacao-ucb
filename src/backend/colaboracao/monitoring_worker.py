# Worker de monitoramento de rotas preferidas — US #22
#
# Orquestra um ciclo de monitoramento: para cada favorito ativo com
# notificações habilitadas, consulta o ETA e dispara push notification
# quando os limiares configurados são cruzados — sem repetições.
#
# Dependências recebidas por injeção — o Worker não instancia nenhum
# mock nem qualquer implementação concreta:
#   FavoritosProvider → fornece a lista de favoritos (US #25 + #29)
#   ETAService        → consulta o ETA isolando o Worker de falhas de rede
#   PushSender        → envia a notificação (Firebase em produção)
#   Deduplicador      → controla quais notificações já foram enviadas
#
# O Worker não contém lógica de agendamento (asyncio loop, APScheduler,
# Celery). Expõe apenas executar_ciclo() — o agendamento fica em main.py.

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from colaboracao.deduplicador import Deduplicador, TipoDisparo
from colaboracao.eta_service import ETAService
from colaboracao.providers.contratos import FavoritosProvider, PushSender

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Registro de resultado de um item processado no ciclo
# ---------------------------------------------------------------------------


@dataclass
class ResultadoCicloItem:
    """
    Descreve o que aconteceu com um favorito específico durante o ciclo.

    Campos:
        usuario_id    → identifica o favorito processado
        numero_linha  → linha monitorada
        tipo_disparo  → TipoDisparo tentado (ou None se não houve tentativa)
        eta_minutos   → ETA consultado (ou None se ETA indisponível / notif. desativa)
        enviado       → True se push_sender retornou True
        motivo_skip   → razão legível quando nenhum disparo foi realizado
    """

    usuario_id: str
    numero_linha: str
    tipo_disparo: Optional[TipoDisparo]
    eta_minutos: Optional[int]
    enviado: bool
    motivo_skip: Optional[str] = None


# ---------------------------------------------------------------------------
# Worker principal
# ---------------------------------------------------------------------------


class MonitoramentoWorker:
    """
    Executa um ciclo de monitoramento das rotas favoritas.

    Recebe todas as dependências por injeção de dependência — compatível
    com qualquer implementação que satisfaça os contratos:
        FavoritosProvider, ETAService (wrapping ETAProvider), PushSender,
        Deduplicador.

    Uso em main.py:
        worker = MonitoramentoWorker(
            favoritos_provider=FavoritosMockProvider(),   # ou real
            eta_service=ETAService(ETAMockProvider()),    # ou real
            push_sender=PushService(),                    # ou Firebase real
            deduplicador=Deduplicador(),
        )
        # a cada ciclo (ex: asyncio.sleep(60)):
        resultados = worker.executar_ciclo()
    """

    def __init__(
        self,
        favoritos_provider: FavoritosProvider,
        eta_service: ETAService,
        push_sender: PushSender,
        deduplicador: Deduplicador,
    ) -> None:
        """
        Args:
            favoritos_provider: fornece a lista de FavoritoMonitorado
            eta_service:        consulta ETA; falhas retornam disponivel=False
            push_sender:        envia (ou registra) push notifications
            deduplicador:       controla deduplicação em memória
        """
        if not isinstance(favoritos_provider, FavoritosProvider):
            raise TypeError(
                f"favoritos_provider deve satisfazer FavoritosProvider, "
                f"recebido: {type(favoritos_provider).__name__}"
            )
        if not isinstance(push_sender, PushSender):
            raise TypeError(
                f"push_sender deve satisfazer PushSender, "
                f"recebido: {type(push_sender).__name__}"
            )
        if not isinstance(deduplicador, Deduplicador):
            raise TypeError(
                f"deduplicador deve ser Deduplicador, "
                f"recebido: {type(deduplicador).__name__}"
            )
        if not isinstance(eta_service, ETAService):
            raise TypeError(
                f"eta_service deve ser ETAService, "
                f"recebido: {type(eta_service).__name__}"
            )

        self._favoritos   = favoritos_provider
        self._eta         = eta_service
        self._push        = push_sender
        self._dedup       = deduplicador

    # ------------------------------------------------------------------
    # Ciclo principal
    # ------------------------------------------------------------------

    def executar_ciclo(self) -> list[ResultadoCicloItem]:
        """
        Processa todos os favoritos ativos uma única vez.

        Para cada FavoritoMonitorado retornado pelo provider:
          1. Se notif_ativas == False → ignora (critério de aceite 3).
          2. Consulta o ETA via ETAService.
          3. Se ETA indisponível → ignora sem log de erro (situação normal).
          4. Consulta o Deduplicador com o ETA atual.
          5. Se há disparo autorizado → chama PushSender.
          6. Registra no Deduplicador SOMENTE se PushSender retornou True.
          7. Falha em um favorito não interrompe os demais.

        Retorna lista de ResultadoCicloItem — um por favorito processado,
        independentemente de ter havido envio ou não. Útil para testes,
        logging e métricas.
        """
        favoritos = self._favoritos.listar_favoritos_com_preferencias()
        resultados: list[ResultadoCicloItem] = []

        logger.debug("[Worker] ciclo iniciado | favoritos=%d", len(favoritos))

        for fav in favoritos:
            item = self._processar_favorito(fav)
            resultados.append(item)

        enviados = sum(1 for r in resultados if r.enviado)
        logger.debug(
            "[Worker] ciclo concluido | processados=%d | enviados=%d",
            len(resultados),
            enviados,
        )

        return resultados

    # ------------------------------------------------------------------
    # Processamento individual — isolado para facilitar testes
    # ------------------------------------------------------------------

    def _processar_favorito(self, fav) -> ResultadoCicloItem:
        """
        Processa um único FavoritoMonitorado e retorna o resultado.

        Nunca lança exceção — erros são capturados, logados e refletidos
        em ResultadoCicloItem com enviado=False.
        """
        # Passo 1 — verificar se notificações estão ativas (critério 3)
        if not fav.notif_ativas:
            logger.debug(
                "[Worker] notificacoes desativadas | usuario=%s | linha=%s",
                fav.usuario_id,
                fav.numero_linha,
            )
            return ResultadoCicloItem(
                usuario_id=fav.usuario_id,
                numero_linha=fav.numero_linha,
                tipo_disparo=None,
                eta_minutos=None,
                enviado=False,
                motivo_skip="notificacoes_desativadas",
            )

        # Passo 2 — consultar ETA
        try:
            eta_resultado = self._eta.consultar(fav.numero_linha)
        except Exception as exc:
            # ETAService não deveria lançar exceto para numero_linha vazio,
            # mas protegemos o ciclo de qualquer surpresa futura.
            logger.warning(
                "[Worker] erro ao consultar ETA | linha=%s | erro=%s",
                fav.numero_linha,
                exc,
            )
            return ResultadoCicloItem(
                usuario_id=fav.usuario_id,
                numero_linha=fav.numero_linha,
                tipo_disparo=None,
                eta_minutos=None,
                enviado=False,
                motivo_skip="erro_consulta_eta",
            )

        # Passo 3 — ETA indisponível
        if not eta_resultado.disponivel:
            logger.debug(
                "[Worker] ETA indisponivel | linha=%s", fav.numero_linha
            )
            return ResultadoCicloItem(
                usuario_id=fav.usuario_id,
                numero_linha=fav.numero_linha,
                tipo_disparo=None,
                eta_minutos=None,
                enviado=False,
                motivo_skip="eta_indisponivel",
            )

        eta = eta_resultado.eta_minutos

        # Passo 4 — consultar Deduplicador
        tipo = self._dedup.verificar(
            usuario_id=fav.usuario_id,
            numero_linha=fav.numero_linha,
            eta_minutos=eta,
            antecedencia_min=fav.antecedencia_min,
        )

        # Nenhum disparo autorizado (fora dos limiares ou já enviado)
        if tipo is None:
            logger.debug(
                "[Worker] sem disparo | usuario=%s | linha=%s | eta=%d",
                fav.usuario_id,
                fav.numero_linha,
                eta,
            )
            return ResultadoCicloItem(
                usuario_id=fav.usuario_id,
                numero_linha=fav.numero_linha,
                tipo_disparo=None,
                eta_minutos=eta,
                enviado=False,
                motivo_skip="sem_disparo_necessario",
            )

        # Passo 5 — enviar push notification
        logger.info(
            "[Worker] enviando | usuario=%s | linha=%s | tipo=%s | eta=%d",
            fav.usuario_id,
            fav.numero_linha,
            tipo.value,
            eta,
        )

        try:
            sucesso = self._push.enviar_push(
                fcm_token=fav.fcm_token,
                numero_linha=fav.numero_linha,
                nome_linha=fav.nome_linha,
                eta_minutos=eta,
            )
        except Exception as exc:
            # PushSender não deveria lançar, mas protegemos o ciclo.
            logger.error(
                "[Worker] excecao no push_sender | linha=%s | erro=%s",
                fav.numero_linha,
                exc,
            )
            sucesso = False

        # Passo 6 — registrar no Deduplicador SOMENTE se envio bem-sucedido
        if sucesso:
            self._dedup.registrar_envio(
                usuario_id=fav.usuario_id,
                numero_linha=fav.numero_linha,
                tipo=tipo,
            )
            logger.info(
                "[Worker] envio registrado | usuario=%s | linha=%s | tipo=%s",
                fav.usuario_id,
                fav.numero_linha,
                tipo.value,
            )

        return ResultadoCicloItem(
            usuario_id=fav.usuario_id,
            numero_linha=fav.numero_linha,
            tipo_disparo=tipo,
            eta_minutos=eta,
            enviado=sucesso,
            motivo_skip=None if sucesso else "falha_push_sender",
        )
