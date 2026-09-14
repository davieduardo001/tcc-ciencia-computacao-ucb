"""
US #20 — geocodificação de origem/destino (OpenStreetMap/Nominatim).

Nenhum teste aqui toca a rede: o Nominatim é um serviço público de
terceiros com política de uso de 1 req/s, e depender dele deixaria o CI
lento e instável. O que é testado é o nosso contrato — cache, limite de
requisições, tolerância a falha e conversão da resposta.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from mobilidade.geocode_service import GeocodeService, Lugar

RESPOSTA_NOMINATIM = [
    {
        "lat": "-15.7933",
        "lon": "-47.8826",
        "name": "Rodoviaria do Plano Piloto",
        "display_name": "Rodoviaria do Plano Piloto, Eixo Rodoviário, Brasília",
    }
]


def _client_falso(resposta):
    """Substitui httpx.AsyncClient por um que devolve `resposta`."""
    contexto = AsyncMock()
    contexto.__aenter__.return_value.get.return_value = AsyncMock(
        raise_for_status=lambda: None, json=lambda: resposta
    )
    return contexto


def test_buscar_converte_resposta_em_lugar():
    servico = GeocodeService()
    with patch("httpx.AsyncClient", return_value=_client_falso(RESPOSTA_NOMINATIM)):
        lugares = asyncio.run(servico.buscar("rodoviaria"))

    assert lugares == [
        Lugar(
            nome="Rodoviaria do Plano Piloto",
            endereco="Rodoviaria do Plano Piloto, Eixo Rodoviário, Brasília",
            lat=-15.7933,
            lng=-47.8826,
        )
    ]


def test_termo_curto_nao_chama_o_servico_externo():
    """
    Autocomplete dispara a cada tecla. Sair pedindo "r" e "ro" ao
    Nominatim estouraria o limite de uso da política deles em segundos.
    """
    servico = GeocodeService()
    with patch("httpx.AsyncClient") as client:
        assert asyncio.run(servico.buscar("ro")) == []
        assert asyncio.run(servico.buscar("")) == []

    client.assert_not_called()


def test_segunda_busca_do_mesmo_termo_vem_do_cache():
    servico = GeocodeService()
    falso = _client_falso(RESPOSTA_NOMINATIM)

    with patch("httpx.AsyncClient", return_value=falso) as client:
        asyncio.run(servico.buscar("rodoviaria"))
        # Mesmo termo com caixa e acento diferentes: é a mesma busca.
        asyncio.run(servico.buscar("  RODOVIÁRIA "))

    assert client.call_count == 1


def test_falha_de_rede_devolve_lista_vazia_sem_lancar():
    """
    Geocodificação é auxílio de busca. Se o Nominatim cair, a tela de
    planejamento continua de pé — o usuário ainda tem "usar minha
    localização" e o clique no mapa.
    """
    servico = GeocodeService()
    with patch("httpx.AsyncClient", side_effect=OSError("rede fora")):
        assert asyncio.run(servico.buscar("rodoviaria")) == []


def test_resposta_sem_coordenada_e_descartada():
    servico = GeocodeService()
    resposta = [{"name": "Sem coordenada"}, *RESPOSTA_NOMINATIM]

    with patch("httpx.AsyncClient", return_value=_client_falso(resposta)):
        lugares = asyncio.run(servico.buscar("rodoviaria"))

    assert [l.nome for l in lugares] == ["Rodoviaria do Plano Piloto"]


def test_reverso_nomeia_um_ponto_do_mapa():
    servico = GeocodeService()
    with patch("httpx.AsyncClient", return_value=_client_falso(RESPOSTA_NOMINATIM[0])):
        lugar = asyncio.run(servico.reverso(-15.7933, -47.8826))

    assert lugar is not None
    assert lugar.nome == "Rodoviaria do Plano Piloto"


def test_chamadas_respeitam_o_intervalo_minimo_da_politica_de_uso():
    """
    A política do Nominatim é sobre a aplicação inteira, não por
    usuário — por isso o serviço serializa as chamadas.
    """
    servico = GeocodeService()
    esperas: list[float] = []

    async def dormir_falso(segundos):
        esperas.append(segundos)

    with patch("httpx.AsyncClient", return_value=_client_falso(RESPOSTA_NOMINATIM)):
        with patch("asyncio.sleep", side_effect=dormir_falso):
            asyncio.run(servico.buscar("rodoviaria"))
            asyncio.run(servico.buscar("universidade de brasilia"))

    assert len(esperas) == 1, "a segunda chamada deveria ter esperado"
    assert esperas[0] > 0
