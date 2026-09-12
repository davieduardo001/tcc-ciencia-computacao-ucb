# Mock de LinhaProvider — US #15
#
# Implementa o contrato LinhaProvider com dados fixos, sem rede, sem
# dependência de API key do Google Maps. Usado como provider padrão até
# que GOOGLE_MAPS_API_KEY esteja configurada (ver mobilidade/routes.py).
#
# Coordenadas são aproximadas (região piloto Taguatinga/Ceilândia-DF,
# em torno do ponto -15.8305, -48.0425 já usado em MapaInterativo.tsx) —
# NÃO são dados reais levantados em campo. Servem para desenvolvimento
# e testes até a integração real com o Google Maps ser validada.
#
# Números de linha reutilizados de colaboracao/providers/favoritos_mock.py
# (0.110 e 0.108) para manter consistência entre os mocks do projeto.

from __future__ import annotations

from mobilidade.providers.contratos import LinhaEncontrada, LinhaProvider, ParadaLinha

_LINHAS_MOCK: dict[str, LinhaEncontrada] = {
    "0.110": LinhaEncontrada(
        numero="0.110",
        nome="0.110 — Taguatinga / Rodoviária",
        sentido="Taguatinga → Rodoviária do Plano Piloto",
        paradas=[
            ParadaLinha(nome="Terminal Taguatinga Centro", lat=-15.8305, lng=-48.0425),
            ParadaLinha(nome="Praça do Relógio", lat=-15.8321, lng=-48.0398),
            ParadaLinha(nome="QNL 10 — Taguatinga Norte", lat=-15.8256, lng=-48.0472),
            ParadaLinha(nome="Rodoviária do Plano Piloto", lat=-15.7939, lng=-47.8828),
        ],
        trajeto=[
            (-15.8305, -48.0425),
            (-15.8321, -48.0398),
            (-15.8256, -48.0472),
            (-15.7939, -47.8828),
        ],
        horarios_previstos=["06:00", "06:20", "06:40", "07:00", "07:20"],
    ),
    "0.108": LinhaEncontrada(
        numero="0.108",
        nome="0.108 — Ceilândia / Plano Piloto",
        sentido="Ceilândia → Plano Piloto",
        paradas=[
            ParadaLinha(nome="Terminal Ceilândia Centro", lat=-15.8151, lng=-48.1074),
            ParadaLinha(nome="Setor O — Ceilândia", lat=-15.8098, lng=-48.0951),
            ParadaLinha(nome="Rodoviária do Plano Piloto", lat=-15.7939, lng=-47.8828),
        ],
        trajeto=[
            (-15.8151, -48.1074),
            (-15.8098, -48.0951),
            (-15.7939, -47.8828),
        ],
        horarios_previstos=["05:50", "06:10", "06:30", "06:50"],
    ),
}


class LinhaMockProvider:
    """
    Provider mock de linhas para desenvolvimento e testes da US #15.

    Conhece apenas os números de linha em _LINHAS_MOCK; qualquer outro
    número resulta em None (Cenário 2: linha não encontrada).
    """

    async def buscar_linha(self, numero_linha: str) -> LinhaEncontrada | None:
        return _LINHAS_MOCK.get(numero_linha)


# Verificação estática: garante que LinhaMockProvider satisfaz o contrato
# em tempo de importação, antes de qualquer execução da rota.
assert isinstance(LinhaMockProvider(), LinhaProvider), (
    "LinhaMockProvider não satisfaz o contrato LinhaProvider. "
    "Verifique se o método buscar_linha está correto."
)
