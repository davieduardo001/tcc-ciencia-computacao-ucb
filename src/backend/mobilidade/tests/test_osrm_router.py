import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from mobilidade.providers import osrm_router


def _resposta_osrm_ok():
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(
        return_value={
            "routes": [
                {
                    "geometry": {
                        "coordinates": [
                            [-48.0425, -15.8305],  # OSRM devolve [lng, lat]
                            [-48.0398, -15.8321],
                            [-47.8828, -15.7939],
                        ]
                    }
                }
            ]
        }
    )
    return resp


def test_rotear_devolve_pontos_na_ordem_lat_lng():
    pontos = [(-15.8305, -48.0425), (-15.7939, -47.8828)]

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_resposta_osrm_ok())):
        resultado = asyncio.run(osrm_router.rotear(pontos))

    assert resultado == [
        (-15.8305, -48.0425),
        (-15.8321, -48.0398),
        (-15.7939, -47.8828),
    ]


def test_rotear_com_menos_de_dois_pontos_retorna_none():
    resultado = asyncio.run(osrm_router.rotear([(-15.83, -48.04)]))

    assert resultado is None


def test_rotear_sem_rotas_na_resposta_retorna_none():
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value={"routes": []})

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=resp)):
        resultado = asyncio.run(
            osrm_router.rotear([(-15.83, -48.04), (-15.79, -47.88)])
        )

    assert resultado is None


def test_rotear_falha_de_rede_retorna_none_sem_lancar_excecao():
    import httpx

    with patch(
        "httpx.AsyncClient.get",
        new=AsyncMock(side_effect=httpx.ConnectError("fora do ar")),
    ):
        resultado = asyncio.run(
            osrm_router.rotear([(-15.83, -48.04), (-15.79, -47.88)])
        )

    assert resultado is None
