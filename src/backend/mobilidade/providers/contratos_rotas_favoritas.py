# Contratos do aviso de rotas favoritas — US #22, levada ao push pela #207
#
# O worker da #22 (colaboracao/monitoring_worker.py) nunca rodou fora de uma
# rota de demonstração: favoritos, ETA e envio eram mocks, e o envio era por
# token FCM. A #207 traz o monitoramento para o mobilidade, onde estão o
# feed ao vivo, o trajeto das linhas e o Web Push, e o envia pelo mesmo
# notificador dos outros alertas (Cenário 8: um canal só).
#
# Mesmo padrão de contratos_proximidade.py: o ServicoRotasFavoritas recebe
# tudo por injeção, e a troca de implementação acontece só em main.py.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from mobilidade.posicao_service import PosicaoVeiculo


@dataclass(frozen=True)
class FavoritaMonitorada:
    """
    Uma rota favorita (US #25) que o worker acompanha.

    Só as colunas que o aviso usa: nada do rótulo que a pessoa deu à rota,
    que não vai para o push (ver web_push.montar_carga_rota_favorita).
    """

    favorita_id: UUID
    usuario_id: UUID
    numero_linha: str
    origem_lat: float
    origem_lng: float
    destino_lat: float
    destino_lng: float


@dataclass(frozen=True)
class EtaEmbarque:
    """
    Quando o próximo ônibus da linha passa na parada de embarque.

    `ao_vivo` = medido pela posição real de um ônibus; senão, é a passagem
    prevista pela grade. Só o ao vivo autoriza o aviso de ônibus próximo:
    "chega em 3 min" tirado só da grade é o ônibus fantasma que o projeto
    combate (RN-09).
    """

    eta_minutos: float
    ao_vivo: bool


class FavoritasProvider(Protocol):
    def listar(self, db: Session) -> list[FavoritaMonitorada]:
        """Favoritas de quem tem aparelho inscrito no push. Nunca levanta."""
        ...


class EtaDoEmbarqueProvider(Protocol):
    def eta(
        self,
        favorita: FavoritaMonitorada,
        veiculos: list[PosicaoVeiculo],
        agora: datetime,
        db: Session,
    ) -> EtaEmbarque | None:
        """ETA até a parada de embarque da favorita, ou None sem dado confiável."""
        ...
