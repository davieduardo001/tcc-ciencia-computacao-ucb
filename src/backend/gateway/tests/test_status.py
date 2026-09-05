from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from gateway.main import app

client = TestClient(app)


def _resposta_mock(status_code: int):
    resposta = AsyncMock()
    resposta.status_code = status_code
    return resposta


def test_status_agrega_servicos_ok():
    with patch("httpx.AsyncClient.get", AsyncMock(return_value=_resposta_mock(200))):
        response = client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "gateway"
    nomes = {s["service"] for s in data["servicos"]}
    assert nomes == {"gateway", "auth", "mobilidade", "colaboracao"}
    assert all(s["status"] == "ok" for s in data["servicos"])


def test_status_marca_servico_indisponivel_como_error():
    import httpx

    with patch(
        "httpx.AsyncClient.get",
        AsyncMock(side_effect=httpx.ConnectError("falhou")),
    ):
        response = client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    servicos_com_erro = [s for s in data["servicos"] if s["service"] != "gateway"]
    assert all(s["status"] == "error" for s in servicos_com_erro)


def test_status_e_rota_publica_sem_autenticacao():
    response = client.get("/api/status")
    assert response.status_code != 401
