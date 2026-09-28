# Mock de FavoritosProvider — US #22
#
# Implementa o contrato FavoritosProvider com dados hardcoded para
# desenvolvimento e testes. Não acessa banco de dados, não importa
# nenhum model SQLAlchemy.
#
# Substituto temporário até que US #25 (RotaFavorita) e US #29
# (PreferenciasNotificacao) estejam implementadas. A troca ocorre
# em um único ponto (main.py), sem modificar o Worker.
#
# Casos de teste cobertos:
#   Caso 1 — notificações ATIVAS, antecedência 30 min  → Worker DEVE notificar
#   Caso 2 — notificações DESABILITADAS                → Worker deve IGNORAR
#             (critério de aceite 3: respeitar preferências desabilitadas)
#
# Para adicionar um usuário de teste real durante o desenvolvimento,
# configure a variável de ambiente MOCK_FCM_TOKEN_1 (e opcionalmente
# MOCK_FCM_TOKEN_2). Se não configuradas, os tokens de placeholder são
# usados — o PushSender em modo dev logará ao invés de enviar.

import os

from colaboracao.providers.contratos import FavoritoMonitorado, FavoritosProvider


class FavoritosMockProvider:
    """
    Provider mock de favoritos para desenvolvimento da US #22.

    Retorna sempre a mesma lista estática de FavoritoMonitorado.
    Thread-safe pois não possui estado mutável.
    """

    def listar_favoritos_com_preferencias(self) -> list[FavoritoMonitorado]:
        """
        Retorna dois favoritos hardcoded para cobrir os cenários de teste
        críticos da US #22.
        """
        return [
            # ------------------------------------------------------------------
            # Caso 1: notificações ATIVAS — linha 0.110
            # Espera-se que o Worker processe este item e dispare push quando
            # o ETA cruzar os limiares de antecedência (30 min) e
            # proximidade (5 min).
            # ------------------------------------------------------------------
            FavoritoMonitorado(
                usuario_id="00000000-0000-0000-0000-000000000001",
                fcm_token=os.getenv(
                    "MOCK_FCM_TOKEN_1",
                    "mock-fcm-token-usuario-1-notif-ativa",
                ),
                numero_linha="0.110",
                nome_linha="0.110 — Taguatinga / Rodoviária",
                notif_ativas=True,
                antecedencia_min=30,
            ),
            # ------------------------------------------------------------------
            # Caso 2: notificações DESABILITADAS — linha 0.108
            # Espera-se que o Worker detecte notif_ativas=False e IGNORE
            # este item sem consultar o ETA nem enviar push.
            # Cobre o critério de aceite 3 da US #22.
            # ------------------------------------------------------------------
            FavoritoMonitorado(
                usuario_id="00000000-0000-0000-0000-000000000002",
                fcm_token=os.getenv(
                    "MOCK_FCM_TOKEN_2",
                    "mock-fcm-token-usuario-2-notif-desabilitada",
                ),
                numero_linha="0.108",
                nome_linha="0.108 — Ceilândia / Plano Piloto",
                notif_ativas=False,
                antecedencia_min=15,
            ),
        ]


# Verificação estática: garante que FavoritosMockProvider satisfaz o contrato
# em tempo de importação, antes de qualquer execução do Worker.
# Se o contrato mudar e o mock não for atualizado, este assert falha com
# mensagem clara ao importar o módulo.
assert isinstance(FavoritosMockProvider(), FavoritosProvider), (
    "FavoritosMockProvider não satisfaz o contrato FavoritosProvider. "
    "Verifique se o método listar_favoritos_com_preferencias está correto."
)
