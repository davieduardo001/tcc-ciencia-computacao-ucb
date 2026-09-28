# Camada de providers da US #22 — Receber Notificações de Rotas Preferidas
#
# Esta camada define contratos (typing.Protocol) que o Worker de monitoramento
# consome. As implementações reais serão fornecidas pelas US #25, #29 e #19
# quando concluídas. Durante o desenvolvimento da #22, mocks são injetados.
#
# Estrutura:
#   contratos.py       → Protocol classes + dataclasses de transferência
#   favoritos_mock.py  → mock de FavoritosProvider (dados hardcoded, US #25/#29)
#   eta_mock.py        → mock de ETAProvider (contagem regressiva, US #19)

from .contratos import FavoritosProvider, ETAProvider, PushSender
from .contratos import FavoritoMonitorado, ETAResultado

__all__ = [
    "FavoritosProvider",
    "ETAProvider",
    "PushSender",
    "FavoritoMonitorado",
    "ETAResultado",
]
