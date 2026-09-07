# Mock de ETAProvider — US #22
#
# Implementa o contrato ETAProvider com uma contagem regressiva previsível
# por linha. Não acessa banco de dados, não faz chamadas HTTP, não depende
# da API SEMOB/GDF.
#
# Substituto temporário até que US #19 (ETA real) esteja implementada.
# A troca ocorre em um único ponto (main.py), sem modificar o Worker.
#
# Comportamento da contagem regressiva:
#   - Cada linha começa em ETA_INICIAL_MINUTOS (35 min por padrão)
#   - A cada chamada a obter_eta(), o ETA decrementa 1 minuto
#   - Quando atinge 0, reseta para ETA_INICIAL_MINUTOS automaticamente
#   - O ciclo completo tem 35 passos, cobrindo todos os limiares:
#       passo  5 → ETA 30 min → deve disparar slot ANTECEDÊNCIA (30 min)
#       passo 30 → ETA  5 min → deve disparar slot PROXIMIDADE  (5 min)
#       passo 35 → ETA  0 min → reseta para 35, nova corrida começa
#
# Isso permite testar o Deduplicador (Etapa 2) de forma determinística:
# sabe-se exatamente em qual chamada cada disparo deve ocorrer.
#
# Thread-safety: o estado (_contadores) é um dict em memória. O Worker
# asyncio roda em uma única thread de evento, então não há condição de
# corrida. Se isso mudar, adicionar asyncio.Lock.

from colaboracao.providers.contratos import ETAProvider, ETAResultado

# ETA inicial para todas as linhas. Escolhido como 35 para cobrir:
#   - o limiar de antecedência padrão (30 min) antes do final da corrida
#   - o limiar de proximidade (5 min) perto do final
#   - uma margem acima do limiar de reset (antecedencia + 5 = 35)
ETA_INICIAL_MINUTOS: int = 35


class ETAMockProvider:
    """
    Provider mock de ETA para desenvolvimento da US #22.

    Mantém um contador regressivo por número de linha. Cada chamada
    a obter_eta() decrementa o contador da linha solicitada em 1 minuto.
    Quando o contador chega a 0, reseta para ETA_INICIAL_MINUTOS.

    Isso produz uma sequência previsível e repetível:
        chamada 1  → ETA 35 (acima de qualquer limiar — sem disparo)
        chamada 2  → ETA 34
        ...
        chamada 6  → ETA 30 (cruza limiar de antecedência — disparo esperado)
        chamada 7  → ETA 29 (dentro do cooldown — sem disparo)
        ...
        chamada 31 → ETA  5 (cruza limiar de proximidade — disparo esperado)
        chamada 32 → ETA  4 (dentro do cooldown — sem disparo)
        ...
        chamada 35 → ETA  1
        chamada 36 → ETA  0 → reseta; próxima chamada retorna 35 novamente
    """

    def __init__(self) -> None:
        # Mapa de numero_linha → ETA atual em minutos
        # Inicializado sob demanda na primeira chamada por linha
        self._contadores: dict[str, int] = {}

    def obter_eta(self, numero_linha: str) -> ETAResultado:
        """
        Retorna o ETA atual para a linha e avança a contagem regressiva.

        Nunca lança exceção — disponivel é sempre True neste mock, pois
        o objetivo é testar a lógica de deduplicação, não falhas de rede.
        """
        # Inicializa o contador da linha se ainda não existe
        if numero_linha not in self._contadores:
            self._contadores[numero_linha] = ETA_INICIAL_MINUTOS

        eta_atual = self._contadores[numero_linha]

        # Decrementa para a próxima chamada; reseta ao chegar em 0
        proximo = eta_atual - 1
        self._contadores[numero_linha] = proximo if proximo > 0 else ETA_INICIAL_MINUTOS

        return ETAResultado(
            numero_linha=numero_linha,
            eta_minutos=eta_atual,
            disponivel=True,
        )

    def resetar(self, numero_linha: str | None = None) -> None:
        """
        Reseta o contador de uma linha específica ou de todas as linhas.

        Útil em testes unitários para garantir estado inicial conhecido
        antes de cada caso de teste.

        Args:
            numero_linha: se informado, reseta apenas essa linha;
                          se None, reseta todas as linhas conhecidas.
        """
        if numero_linha is not None:
            self._contadores[numero_linha] = ETA_INICIAL_MINUTOS
        else:
            self._contadores = {}

    def eta_atual(self, numero_linha: str) -> int:
        """
        Retorna o ETA que será retornado na PRÓXIMA chamada a obter_eta(),
        sem avançar o contador. Útil para asserções em testes.
        """
        return self._contadores.get(numero_linha, ETA_INICIAL_MINUTOS)


# Verificação estática: garante que ETAMockProvider satisfaz o contrato
# em tempo de importação, antes de qualquer execução do Worker.
assert isinstance(ETAMockProvider(), ETAProvider), (
    "ETAMockProvider não satisfaz o contrato ETAProvider. "
    "Verifique se o método obter_eta está correto."
)
