# Serviço de consulta de ETA — US #22
#
# Camada fina que o Worker usa para consultar o tempo estimado de chegada
# de uma linha. Desacopla o Worker da implementação concreta do ETAProvider.
#
# O serviço não conhece ETAMockProvider nem qualquer outra implementação
# concreta — recebe apenas o contrato ETAProvider por injeção de dependência.
# A substituição do mock pela implementação real da US #19 ocorre em
# main.py, sem modificar este arquivo.
#
# Validações:
#   - numero_linha não pode ser string vazia (erro de programação)
#   - Falhas do provider são capturadas e devolvidas como ETAResultado
#     com disponivel=False (o Worker nunca recebe exceção deste serviço)

from __future__ import annotations

import logging

from colaboracao.providers.contratos import ETAProvider, ETAResultado

logger = logging.getLogger(__name__)


class ETAService:
    """
    Serviço de consulta de ETA para o Worker de monitoramento da US #22.

    Recebe qualquer implementação de ETAProvider — mock para desenvolvimento,
    implementação real (US #19) em produção. A troca é feita em main.py.

    Uso:
        provider = ETAMockProvider()          # ou ETARealProvider(...)
        service  = ETAService(provider)
        resultado = service.consultar("0.110")
        if resultado.disponivel:
            print(resultado.eta_minutos)
    """

    def __init__(self, provider: ETAProvider) -> None:
        """
        Args:
            provider: qualquer objeto que satisfaça o contrato ETAProvider.
                      Verificado em tempo de instanciação via isinstance().
        """
        if not isinstance(provider, ETAProvider):
            raise TypeError(
                f"provider deve satisfazer o contrato ETAProvider, "
                f"recebido: {type(provider).__name__}"
            )
        self._provider = provider

    def consultar(self, numero_linha: str) -> ETAResultado:
        """
        Consulta o tempo estimado de chegada para a linha informada.

        Sempre retorna um ETAResultado válido — nunca lança exceção.
        Quando o provider falha ou a linha está indisponível, retorna
        ETAResultado com disponivel=False e eta_minutos=0.

        Args:
            numero_linha: identificador textual da linha (ex: "0.110").
                          Não pode ser string vazia.

        Returns:
            ETAResultado com os campos:
                numero_linha  → espelha a entrada
                eta_minutos   → tempo estimado (irrelevante se disponivel=False)
                disponivel    → False quando dado não está disponível

        Raises:
            ValueError: se numero_linha for string vazia. Isso indica erro
                        de programação no Worker, não falha de runtime.
        """
        if not numero_linha or not numero_linha.strip():
            raise ValueError(
                "numero_linha não pode ser vazio. "
                "Verifique os dados de RotaFavorita antes de consultar o ETA."
            )

        try:
            resultado = self._provider.obter_eta(numero_linha)
        except Exception as exc:
            # Isola o Worker de falhas inesperadas do provider (ex: timeout
            # HTTP na implementação real da US #19, erro de banco, etc.)
            logger.warning(
                "ETAProvider falhou para linha %r: %s — retornando indisponivel",
                numero_linha,
                exc,
            )
            return ETAResultado(
                numero_linha=numero_linha,
                eta_minutos=0,
                disponivel=False,
            )

        return resultado
