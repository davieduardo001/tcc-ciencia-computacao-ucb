import json
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from starlette.responses import Response

from gateway.main import app

client = TestClient(app)


def _proxy_response_ok():
    """Simula o Response que proxy_request devolve num login bem-sucedido.

    Regressão: proxy_request devolve um starlette.Response (não um
    httpx.Response), então response.json() quebra com AttributeError.
    O gateway deve ler o corpo com json.loads(response.body).
    """
    corpo = json.dumps(
        {
            "access_token": "token-fake-access",
            "refresh_token": "token-fake-refresh",
            "token_type": "bearer",
        }
    ).encode()
    return Response(content=corpo, status_code=200, media_type="application/json")


def test_login_seta_cookies_sem_quebrar_no_json_do_proxy():
    with patch(
        "gateway.routes.proxy_request",
        AsyncMock(return_value=_proxy_response_ok()),
    ):
        response = client.post(
            "/api/auth/login",
            json={"email": "teste@example.com", "senha": "senha123"},
        )

    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_refresh_seta_cookies_sem_quebrar_no_json_do_proxy():
    with patch(
        "gateway.routes.proxy_request",
        AsyncMock(return_value=_proxy_response_ok()),
    ):
        response = client.post(
            "/api/auth/refresh",
            cookies={"access_token": "qualquer", "refresh_token": "qualquer"},
        )

    assert response.status_code == 200
    assert "access_token" in response.cookies
