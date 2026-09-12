# Contratos da US #15 — Buscar Linha por Número
#
# Define a interface (typing.Protocol) que o LinhaService consome para
# obter dados de uma linha (paradas, trajeto, horários) quando ela ainda
# não está cacheada no nosso banco (ou está desatualizada).
#
# Implementação mock: linha_mock.py — dados fixos, sem rede, para
# desenvolvimento e testes.
# Implementação real: linha_google_maps.py — usa a Routes API do Google
# Maps (mode=TRANSIT) para obter paradas e trajeto entre os terminais
# conhecidos da linha.
#
# A troca entre mock e real ocorre em um único ponto (routes.py, via
# LinhaService), sem reescrever o service nem a rota HTTP.

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ParadaLinha:
    """Uma parada ao longo do trajeto de uma linha."""

    nome: str
    lat: float
    lng: float


@dataclass(frozen=True)
class LinhaEncontrada:
    """
    Resultado de uma busca de linha bem-sucedida.

    Campos:
        numero               → espelha a entrada, ex: "0.110"
        nome                 → nome legível, ex: "0.110 — Taguatinga / Rodoviária"
        sentido               → ex: "Taguatinga → Rodoviária do Plano Piloto"
        paradas               → lista ordenada de ParadaLinha ao longo do trajeto
        trajeto               → lista de pontos [lat, lng] (geometria da rota)
        horarios_previstos    → lista de horários previstos, ex: ["06:00", "06:20"]
    """

    numero: str
    nome: str
    sentido: str
    paradas: list[ParadaLinha]
    trajeto: list[tuple[float, float]]
    horarios_previstos: list[str]


@runtime_checkable
class LinhaProvider(Protocol):
    """
    Contrato para buscar os detalhes de uma linha de ônibus.

    Implementação real: consulta a Routes API do Google Maps entre os
    terminais conhecidos da linha (cadastrados manualmente para as
    linhas piloto de Taguatinga/Ceilândia).

    Implementação mock: dados fixos em linha_mock.py.
    """

    async def buscar_linha(self, numero_linha: str) -> LinhaEncontrada | None:
        """
        Busca os detalhes da linha informada.

        Retorna None quando a linha não é conhecida pela fonte de dados
        (Cenário 2 da US #15: linha não encontrada) — nunca lança exceção
        para esse caso. Falhas de rede/timeout devem ser deixadas subir
        como exceção, para que o LinhaService decida como tratar.
        """
        ...
