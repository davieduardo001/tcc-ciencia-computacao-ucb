# Contratos da US #22 — Receber Notificações de Rotas Preferidas
#
# Define as interfaces (typing.Protocol) que o Worker de monitoramento consome.
# Nenhum model SQLAlchemy, nenhum endpoint HTTP, nenhuma dependência de banco.
#
# Responsabilidades por contrato:
#   FavoritosProvider → implementação real fornecida pelas US #25 + #29
#   ETAProvider       → implementação real fornecida pela US #19
#   PushSender        → implementação real exclusiva da US #22 (firebase-admin)
#
# Durante o desenvolvimento da #22, mocks são injetados no lugar das
# implementações reais. A substituição ocorre em um único ponto (main.py),
# sem reescrever o Worker.

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Estruturas de dados transferidas entre o Worker e os providers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FavoritoMonitorado:
    """
    Representa um favorito ativo de um usuário que deve ser monitorado
    pelo Worker a cada ciclo.

    Campos:
        usuario_id        → UUID do usuário (str) — necessário para deduplicação
                           e para rastrear envios por usuário
        fcm_token         → token FCM do dispositivo — necessário para enviar
                           a push notification; fornecido pela US #22 via
                           endpoint POST /preferencias/fcm-token
        numero_linha      → identificador textual da linha (ex: "0.110") —
                           usado para consultar o ETA no ETAProvider
        nome_linha        → nome legível da linha (ex: "0.110 — Taguatinga /
                           Rodoviária") — compõe o payload da notificação
        notif_ativas      → se False, o Worker ignora este favorito (critério
                           de aceite 3: respeitar notificações desabilitadas)
        antecedencia_min  → minutos de antecedência configurados pelo usuário
                           (critério de aceite 2: notificação antecipada);
                           padrão 30 min conforme UC22
    """

    usuario_id: str
    fcm_token: str
    numero_linha: str
    nome_linha: str
    notif_ativas: bool
    antecedencia_min: int


@dataclass(frozen=True)
class ETAResultado:
    """
    Representa o resultado de uma consulta de ETA para uma linha.

    Campos:
        numero_linha  → espelha a entrada, facilita logging
        eta_minutos   → tempo estimado de chegada em minutos inteiros;
                       valor irrelevante quando disponivel=False
        disponivel    → False quando a fonte de dados não respondeu, a linha
                       está inativa ou o dado é considerado inválido; o Worker
                       deve ignorar silenciosamente este caso
    """

    numero_linha: str
    eta_minutos: int
    disponivel: bool


# ---------------------------------------------------------------------------
# Contratos (Protocol)
# ---------------------------------------------------------------------------


@runtime_checkable
class FavoritosProvider(Protocol):
    """
    Contrato para obter a lista de favoritos monitoráveis.

    Implementação real: query JOIN entre rotas_favoritas (US #25) e
    preferencias_notificacao (US #29), filtrando apenas registros com
    fcm_token preenchido.

    Implementação mock: lista hardcoded em favoritos_mock.py.
    """

    def listar_favoritos_com_preferencias(self) -> list[FavoritoMonitorado]:
        """
        Retorna todos os favoritos ativos que possuem FCM token registrado.
        O Worker chama este método a cada ciclo de monitoramento.

        Retorna lista vazia se não houver favoritos — nunca lança exceção.
        """
        ...


@runtime_checkable
class ETAProvider(Protocol):
    """
    Contrato para consultar o tempo estimado de chegada de uma linha.

    Implementação real: chamada HTTP ao serviço mobilidade, que por sua vez
    consume a API SEMOB/GDF (US #19).

    Implementação mock: contagem regressiva por linha em eta_mock.py.
    """

    def obter_eta(self, numero_linha: str) -> ETAResultado:
        """
        Consulta o ETA para a linha informada.

        Nunca lança exceção: em caso de falha, retorna ETAResultado com
        disponivel=False para que o Worker ignore silenciosamente.
        """
        ...


@runtime_checkable
class PushSender(Protocol):
    """
    Contrato para enviar push notifications via FCM.

    Implementação real: firebase-admin (push_service.py) — exclusivo da #22.
    Não há mock obrigatório: em modo dev, a implementação real pode logar
    ao invés de enviar quando FIREBASE_CREDENTIALS_JSON estiver vazio.
    """

    def enviar_push(
        self,
        fcm_token: str,
        numero_linha: str,
        nome_linha: str,
        eta_minutos: int,
    ) -> bool:
        """
        Envia uma push notification para o dispositivo identificado por
        fcm_token.

        Retorna True se o envio foi aceito pelo FCM, False caso contrário.
        Nunca lança exceção: falhas de rede ou token inválido devem ser
        tratadas internamente e refletidas no retorno.
        """
        ...
