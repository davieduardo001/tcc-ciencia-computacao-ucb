import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from jose import jwt
from starlette.responses import Response

from gateway.main import app
from shared.config import get_settings

client = TestClient(app)
settings = get_settings()


def _token_valido() -> str:
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "exp": datetime.utcnow() + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _proxy_response_me():
    corpo = json.dumps(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "nome": "Usuária de Teste",
            "email": "teste@example.com",
            "avatar_url": None,
        }
    ).encode()
    return Response(content=corpo, status_code=200, media_type="application/json")


def test_me_proxyado_com_sessao_valida():
    with patch(
        "gateway.routes.proxy_request",
        AsyncMock(return_value=_proxy_response_me()),
    ):
        response = client.get(
            "/api/auth/me",
            cookies={"access_token": _token_valido()},
        )

    assert response.status_code == 200
    assert response.json()["email"] == "teste@example.com"


def test_me_sem_sessao_retorna_401_sem_chamar_o_proxy():
    with patch(
        "gateway.routes.proxy_request",
        AsyncMock(return_value=_proxy_response_me()),
    ) as proxy_mock:
        response = client.get("/api/auth/me")

    assert response.status_code == 401
    proxy_mock.assert_not_called()


def _proxy_response_first_access(valor: bool):
    corpo = json.dumps(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "nome": "Usuária de Teste",
            "email": "teste@example.com",
            "avatar_url": None,
            "first_access": valor,
        }
    ).encode()
    return Response(content=corpo, status_code=200, media_type="application/json")


def test_first_access_proxyado_com_sessao_valida():
    """Regressão: PUT /auth/me/first-access não tinha rota no Gateway (só
    GET /auth/me existia) — caia em 404 antes de chegar no Auth Service,
    e o tutorial nunca persistia ter sido concluído/pulado."""
    with patch(
        "gateway.routes.proxy_request",
        AsyncMock(return_value=_proxy_response_first_access(False)),
    ) as proxy_mock:
        response = client.put(
            "/api/auth/me/first-access",
            json={"first_access": False},
            cookies={"access_token": _token_valido()},
        )

    assert response.status_code == 200
    assert response.json()["first_access"] is False
    proxy_mock.assert_called_once()


def test_first_access_sem_sessao_retorna_401_sem_chamar_o_proxy():
    with patch(
        "gateway.routes.proxy_request",
        AsyncMock(return_value=_proxy_response_first_access(False)),
    ) as proxy_mock:
        response = client.put(
            "/api/auth/me/first-access",
            json={"first_access": False},
        )

    assert response.status_code == 401
    proxy_mock.assert_not_called()
