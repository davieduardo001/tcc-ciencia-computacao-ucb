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
# Números de linha 0.110 e 0.108 reutilizados de
# colaboracao/providers/favoritos_mock.py para manter consistência
# entre os mocks do projeto. As demais (0.120, 0.130, 0.140) foram
# adicionadas só pra dar mais opções pro autocomplete da US #17 — não
# reutilizam número de nenhum outro mock.
#
# Os pontos aqui embaixo são só waypoints aproximados — o trajeto de
# verdade (seguindo rua) é montado pelo LinhaService via road-snapping
# no OSRM (ver linha_service.py e providers/osrm_router.py), não
# direto a partir desses pontos.

from __future__ import annotations

from mobilidade.providers.contratos import (
    LinhaEncontrada,
    LinhaProvider,
    LinhaResumo,
    ParadaLinha,
)

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
    "0.120": LinhaEncontrada(
        numero="0.120",
        nome="0.120 — Samambaia / Plano Piloto",
        sentido="Samambaia → Rodoviária do Plano Piloto",
        paradas=[
            ParadaLinha(nome="Terminal Samambaia", lat=-15.8740, lng=-48.0899),
            ParadaLinha(nome="Águas Claras — Estação", lat=-15.8375, lng=-48.0186),
            ParadaLinha(nome="Rodoviária do Plano Piloto", lat=-15.7939, lng=-47.8828),
        ],
        trajeto=[
            (-15.8740, -48.0899),
            (-15.8375, -48.0186),
            (-15.7939, -47.8828),
        ],
        horarios_previstos=["05:40", "06:00", "06:20", "06:40"],
    ),
    "0.130": LinhaEncontrada(
        numero="0.130",
        nome="0.130 — Gama / Plano Piloto",
        sentido="Gama → Rodoviária do Plano Piloto",
        paradas=[
            ParadaLinha(nome="Terminal do Gama", lat=-16.0180, lng=-48.0630),
            ParadaLinha(nome="Núcleo Bandeirante", lat=-15.8697, lng=-47.9678),
            ParadaLinha(nome="Rodoviária do Plano Piloto", lat=-15.7939, lng=-47.8828),
        ],
        trajeto=[
            (-16.0180, -48.0630),
            (-15.8697, -47.9678),
            (-15.7939, -47.8828),
        ],
        horarios_previstos=["05:30", "06:00", "06:30", "07:00"],
    ),
    "0.140": LinhaEncontrada(
        numero="0.140",
        nome="0.140 — Sobradinho / Plano Piloto",
        sentido="Sobradinho → Rodoviária do Plano Piloto",
        paradas=[
            ParadaLinha(nome="Terminal Sobradinho", lat=-15.6524, lng=-47.7936),
            ParadaLinha(nome="Rodoviária do Plano Piloto", lat=-15.7939, lng=-47.8828),
        ],
        trajeto=[
            (-15.6524, -47.7936),
            (-15.7939, -47.8828),
        ],
        horarios_previstos=["06:10", "06:40", "07:10"],
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

    async def listar_resumo(self) -> list[LinhaResumo]:
        return [
            LinhaResumo(
                numero=linha.numero,
                nome=linha.nome,
                sentido=linha.sentido,
                paradas_nomes=[parada.nome for parada in linha.paradas],
            )
            for linha in _LINHAS_MOCK.values()
        ]


# Verificação estática: garante que LinhaMockProvider satisfaz o contrato
# em tempo de importação, antes de qualquer execução da rota.
assert isinstance(LinhaMockProvider(), LinhaProvider), (
    "LinhaMockProvider não satisfaz o contrato LinhaProvider. "
    "Verifique se o método buscar_linha está correto."
)
