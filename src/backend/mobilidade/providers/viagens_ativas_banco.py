# Viagens ativas reais (US #171) para o alerta de proximidade (#172)
#
# Implementa o `ViagensAtivasProvider` que a #172 deixou provisório
# (`ViagensAtivasProvisorias`, que devolvia sempre `[]`). A troca é uma linha
# em mobilidade/main.py; o ServicoProximidade não muda, porque consome os
# campos de `ViagemAtiva`, não a fonte.

from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from mobilidade.models.parada import Parada
from mobilidade.models.viagem import Viagem
from mobilidade.providers.contratos_proximidade import ViagemAtiva
from mobilidade.viagem_service import agora_utc, expirar_vencidas
from shared.database import SessionLocal

logger = logging.getLogger(__name__)


class ViagensAtivasDoBanco:
    """
    ViagensAtivasProvider que lê a tabela `viagem`.

    - Só entram viagens **com parada de destino**: sem destino não há o que
      avisar ("a parada de destino" é o Cenário 1 da #172).
    - Destino cujo código sumiu da tabela `parada` (ela é reconstruída a
      cada ingestão) também fica de fora, com aviso no log — melhor não
      alertar do que alertar para um ponto inventado.
    - Nunca lança exceção: banco fora vira lista vazia e o worker tenta no
      próximo ciclo (contrato do provider).
    - Abre a própria sessão porque `listar_ativas()` não recebe uma: o
      worker passa a dele só para o resto do ciclo.
    """

    def __init__(self, sessao_factory: Callable[[], Session] = SessionLocal) -> None:
        self._sessao_factory = sessao_factory

    def listar_ativas(self) -> list[ViagemAtiva]:
        try:
            db = self._sessao_factory()
        except Exception:
            logger.warning("Sem sessao para listar viagens ativas", exc_info=True)
            return []

        try:
            # RN-17: viagem vencida não pode gerar alerta.
            expirar_vencidas(db, agora_utc())

            linhas = (
                db.query(Viagem, Parada)
                .outerjoin(Parada, Parada.codigo == Viagem.parada_destino_codigo)
                .filter(
                    Viagem.encerrada_em.is_(None),
                    Viagem.parada_destino_codigo.isnot(None),
                )
                .all()
            )

            ativas: list[ViagemAtiva] = []
            for viagem, parada in linhas:
                if parada is None:
                    logger.warning(
                        "Destino da viagem nao esta na tabela parada | viagem=%s | codigo=%s",
                        viagem.id,
                        viagem.parada_destino_codigo,
                    )
                    continue
                ativas.append(
                    ViagemAtiva(
                        viagem_id=str(viagem.id),
                        usuario_id=viagem.usuario_id,
                        numero_linha=viagem.numero_linha,
                        parada_destino_codigo=parada.codigo,
                        parada_destino_lat=parada.lat,
                        parada_destino_lng=parada.lng,
                        parada_destino_nome=parada.nome or "",
                    )
                )
            return ativas
        except Exception:
            logger.warning("Falha ao listar viagens ativas", exc_info=True)
            return []
        finally:
            db.close()
