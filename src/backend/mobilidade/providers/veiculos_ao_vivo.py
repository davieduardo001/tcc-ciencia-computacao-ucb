# Posição dos veículos para o alerta de proximidade — US #172
#
# VeiculosProvider real: envolve o PosicaoService (US #16), cujo cache tem
# validade de 20 s — o ciclo do worker é de 5 min, então cada ciclo baixa
# o feed do SEMOB uma vez (uma chamada serve todas as viagens ativas de
# todas as linhas do ciclo).
#
# O PosicaoService é async e o worker da US #27 roda numa thread do
# APScheduler (sem event loop): aqui o loop é criado e fechado por ciclo
# (asyncio.run). Por isso o serviço é instanciado a cada ciclo quando não
# há injeção: reutilizar uma instância entre loops fechados deixa a task
# de renovação do cache congelada (referência a task de um loop já morto
# nunca fica "done") e o feed envelhece até ser filtrado pelo SEMOB —
# sem veículos, sem alerta, para sempre.
#
# Tudo que dá errado vira lista vazia — e sem posição não há alerta
# (Cenário 4 da #172: nenhum alerta impreciso quando não há GPS).

from __future__ import annotations

import asyncio
import logging

from mobilidade.posicao_service import PosicaoService, PosicaoVeiculo

logger = logging.getLogger(__name__)


class VeiculosAoVivo:
    """
    VeiculosProvider baseado no feed ao vivo do SEMOB (US #16).

    Nunca lança exceção: falha de rede, timeout ou ciclo de vida do loop
    retornam `{}` — o ServicoProximidade trata como "sem veículo" e não
    dispara nada.

    `posicao_service` existe só para teste (injetar um stub); em produção
    fica None e cada ciclo cria o seu, como explicado no cabeçalho.
    """

    def __init__(self, posicao_service: PosicaoService | None = None) -> None:
        self._posicao = posicao_service

    def obter_das_linhas(self, numeros_linha: set[str]) -> dict[str, list[PosicaoVeiculo]]:
        if not numeros_linha:
            return {}

        servico = self._posicao or PosicaoService()
        try:
            return asyncio.run(servico.posicoes_das_linhas(numeros_linha))
        except Exception:
            logger.warning(
                "Falha ao ler posicao dos veiculos | linhas=%s",
                ",".join(sorted(numeros_linha)),
                exc_info=True,
            )
            return {}
