# Serviço de envio de push notifications — US #22
#
# Implementa o contrato PushSender definido em providers/contratos.py.
#
# Esta implementação é deliberadamente desacoplada do Firebase Admin SDK.
# Em vez de realizar chamadas externas, registra as notificações em memória
# (self.notificacoes_enviadas), o que permite:
#   - testar toda a lógica do Worker sem credenciais Firebase;
#   - inspecionar exatamente quais payloads seriam enviados;
#   - verificar os critérios de aceite da US #22 em ambiente de CI.
#
# Quando o Firebase Admin SDK for integrado (etapa futura), basta substituir
# esta classe em main.py. O Worker, o ETAService e o Deduplicador não mudam.
#
# NÃO importa firebase_admin nem realiza nenhuma chamada de rede.

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from colaboracao.providers.contratos import PushSender

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Estrutura de um registro de notificação enviada
# ---------------------------------------------------------------------------


@dataclass
class NotificacaoRegistrada:
    """
    Representa uma notificação que passou pela lógica de envio do PushService.

    Permite inspecionar em testes e em logs exatamente o que seria enviado
    para o FCM, incluindo token, payload completo e timestamp.

    Campos:
        fcm_token    → token do dispositivo destinatário
        title        → título da notificação (exibido pelo SO)
        body         → corpo da notificação (texto principal)
        data         → payload de dados adicionais (strings apenas — requisito FCM)
        enviado_em   → timestamp UTC do momento do registro
    """

    fcm_token: str
    title: str
    body: str
    data: dict[str, str]
    enviado_em: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    # Atalhos para acesso direto nos testes sem navegar em data{}
    @property
    def numero_linha(self) -> str:
        return self.data.get("numero_linha", "")

    @property
    def nome_linha(self) -> str:
        return self.data.get("nome_linha", "")

    @property
    def eta_minutos(self) -> int:
        """
        Retorna eta_minutos como inteiro.
        No payload FCM todos os valores de data{} são strings — a conversão
        aqui é apenas para conveniência em testes.
        """
        return int(self.data.get("eta_minutos", "0"))


# ---------------------------------------------------------------------------
# Implementação do PushService
# ---------------------------------------------------------------------------


class PushService:
    """
    Implementação testável de PushSender para a US #22.

    Registra notificações em memória (self.notificacoes_enviadas) ao invés
    de enviar para o Firebase. Adequada para desenvolvimento, testes e CI.

    Uso:
        sender = PushService()
        sender.enviar_push("token-abc", "0.110", "Linha Centro", 5)
        assert len(sender.notificacoes_enviadas) == 1
        assert sender.notificacoes_enviadas[0].title == "Ônibus próximo"
    """

    def __init__(self) -> None:
        # Histórico de todas as notificações que passaram por este serviço.
        # Ordem de inserção preservada — útil para asserções em sequência.
        self.notificacoes_enviadas: list[NotificacaoRegistrada] = []

    # ------------------------------------------------------------------
    # Implementação do contrato PushSender
    # ------------------------------------------------------------------

    def enviar_push(
        self,
        fcm_token: str,
        numero_linha: str,
        nome_linha: str,
        eta_minutos: int,
    ) -> bool:
        """
        Registra a notificação em memória e loga o payload.

        Realiza validação de entradas antes de qualquer processamento.
        Retorna True após registro bem-sucedido.

        Args:
            fcm_token:    token FCM do dispositivo (não pode ser vazio)
            numero_linha: identificador da linha, ex: "0.110" (não pode ser vazio)
            nome_linha:   nome legível da linha (não pode ser vazio)
            eta_minutos:  tempo estimado de chegada em minutos (>= 0)

        Returns:
            True se o registro foi realizado com sucesso.

        Raises:
            ValueError: se qualquer entrada for inválida.
        """
        self._validar(fcm_token, numero_linha, nome_linha, eta_minutos)

        title, body = self._montar_mensagem(numero_linha, nome_linha, eta_minutos)
        data = self._montar_data(numero_linha, nome_linha, eta_minutos)

        notificacao = NotificacaoRegistrada(
            fcm_token=fcm_token,
            title=title,
            body=body,
            data=data,
        )
        self.notificacoes_enviadas.append(notificacao)

        logger.info(
            "[PushService] notificacao registrada | linha=%r | eta=%d min | token=%.8s…",
            numero_linha,
            eta_minutos,
            fcm_token,
        )

        return True

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    @staticmethod
    def _validar(
        fcm_token: str,
        numero_linha: str,
        nome_linha: str,
        eta_minutos: int,
    ) -> None:
        """Valida as entradas e lança ValueError para valores inválidos."""
        if not fcm_token or not fcm_token.strip():
            raise ValueError("fcm_token não pode ser vazio.")
        if not numero_linha or not numero_linha.strip():
            raise ValueError("numero_linha não pode ser vazio.")
        if not nome_linha or not nome_linha.strip():
            raise ValueError("nome_linha não pode ser vazio.")
        if eta_minutos < 0:
            raise ValueError(
                f"eta_minutos deve ser >= 0, recebido: {eta_minutos}."
            )

    @staticmethod
    def _montar_mensagem(
        numero_linha: str,
        nome_linha: str,
        eta_minutos: int,
    ) -> tuple[str, str]:
        """
        Monta title e body da notificação de acordo com o ETA.

        Critério de aceite 1 (≤ 5 min) recebe mensagem de urgência.
        Demais casos recebem mensagem de antecedência.
        """
        if eta_minutos <= 5:
            title = "Ônibus próximo"
            body = (
                f"O ônibus da linha {numero_linha} chegará em "
                f"aproximadamente {eta_minutos} minuto"
                + ("." if eta_minutos == 1 else "s.")
            )
        else:
            title = "Lembrete de rota"
            body = (
                f"O ônibus da linha {numero_linha} chegará em "
                f"aproximadamente {eta_minutos} minutos."
            )

        return title, body

    @staticmethod
    def _montar_data(
        numero_linha: str,
        nome_linha: str,
        eta_minutos: int,
    ) -> dict[str, str]:
        """
        Monta o payload data{} da notificação FCM.

        Todos os valores são strings — requisito do protocolo FCM.
        O Worker pode incluir campos adicionais futuramente sem alterar
        a estrutura base.
        """
        return {
            "numero_linha": numero_linha,
            "nome_linha": nome_linha,
            "eta_minutos": str(eta_minutos),
        }

    # ------------------------------------------------------------------
    # Utilitários de inspeção (para testes e logging)
    # ------------------------------------------------------------------

    def limpar(self) -> None:
        """
        Limpa o histórico de notificações enviadas.
        Útil para isolar casos de teste sem criar nova instância.
        """
        self.notificacoes_enviadas.clear()

    def total_enviadas(self) -> int:
        """Retorna o número de notificações registradas até o momento."""
        return len(self.notificacoes_enviadas)

    def ultima(self) -> Optional[NotificacaoRegistrada]:
        """Retorna a notificação mais recente, ou None se nenhuma foi enviada."""
        return self.notificacoes_enviadas[-1] if self.notificacoes_enviadas else None


# ---------------------------------------------------------------------------
# Verificação estática de contrato
# ---------------------------------------------------------------------------

# Garante em tempo de importação que PushService satisfaz PushSender.
# Se a assinatura do contrato mudar e PushService não for atualizado,
# este assert falha imediatamente com mensagem clara.
assert isinstance(PushService(), PushSender), (
    "PushService não satisfaz o contrato PushSender. "
    "Verifique se o método enviar_push está correto."
)
