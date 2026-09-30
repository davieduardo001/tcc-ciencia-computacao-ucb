# Geometria de trajeto compartilhada entre rota_service (US #20) e
# eta_service (US #19/#159).
#
# `TrajetoMedido` pré-calcula a distância acumulada ao longo de um
# trajeto para responder em O(1) "quantos metros há entre estes dois
# pontos do traçado" — é o que permite ao motor de ETA saber se um
# veículo já passou de uma parada (índice do veículo > índice da
# parada) e quanto falta até lá, sem refazer a soma a cada consulta.

from __future__ import annotations

from dataclasses import dataclass

from mobilidade.semob_source import _distancia_metros as distancia_metros

__all__ = ["distancia_metros", "mais_proximo", "TrajetoMedido"]


def mais_proximo(
    trajeto: list[tuple[float, float]],
    alvo: tuple[float, float],
    inicio: int = 0,
) -> tuple[int | None, float]:
    """Índice do ponto do trajeto mais próximo de `alvo`, a partir de `inicio`."""
    melhor_i, melhor_d = None, float("inf")
    for i in range(inicio, len(trajeto)):
        d = distancia_metros(*trajeto[i], *alvo)
        if d < melhor_d:
            melhor_i, melhor_d = i, d
    return melhor_i, melhor_d


class TrajetoMedido:
    """
    Um trajeto (lista de lat/lng em ordem) com distância acumulada
    pré-calculada, para medir "metros entre o ponto i e o ponto j" sem
    somar segmento a segmento a cada chamada.
    """

    def __init__(self, pontos: list[tuple[float, float]]) -> None:
        self.pontos = pontos
        acumulado = [0.0]
        for i in range(1, len(pontos)):
            acumulado.append(
                acumulado[-1] + distancia_metros(*pontos[i - 1], *pontos[i])
            )
        self.acumulado = acumulado
        self.comprimento_m = acumulado[-1] if acumulado else 0.0

    def indice_mais_proximo(
        self, ponto: tuple[float, float], tolerancia_m: float
    ) -> int | None:
        """Índice do vértice mais próximo de `ponto`, ou None se nenhum
        estiver dentro de `tolerancia_m` (ponto fora deste trajeto)."""
        i, d = mais_proximo(self.pontos, ponto)
        if i is None or d > tolerancia_m:
            return None
        return i

    def metros_entre(self, i: int, j: int) -> float:
        """Distância ao longo do trajeto de i até j. Negativa quando j
        vem antes de i (o alvo já ficou para trás)."""
        return self.acumulado[j] - self.acumulado[i]
