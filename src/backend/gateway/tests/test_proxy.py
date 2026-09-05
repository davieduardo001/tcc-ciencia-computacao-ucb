import asyncio
from unittest.mock import AsyncMock, patch

from starlette.requests import Request

from gateway.proxy import proxy_request


def _fake_request(headers: dict) -> Request:
    raw_headers = [
        (k.lower().encode(), v.encode()) for k, v in headers.items()
    ]
    scope = {
        "type": "http",
        "method": "POST",
        "headers": raw_headers,
        "path": "/auth/login",
        "query_string": b"",
    }

    async def receive():
        return {"type": "http.request", "body": b"{}", "more_body": False}

    return Request(scope, receive)


def test_nao_repassa_accept_encoding_do_cliente():
    """Regressão: repassar o Accept-Encoding do navegador (que anuncia
    zstd/br) fazia o httpx do Gateway receber respostas comprimidas
    que ele não sabe decodificar, corrompendo o JSON."""
    request = _fake_request(
        {"accept-encoding": "gzip, deflate, br, zstd", "content-type": "application/json"}
    )

    resposta_mock = AsyncMock()
    resposta_mock.status_code = 200
    resposta_mock.content = b'{"ok": true}'
    resposta_mock.headers = {}

    with patch(
        "httpx.AsyncClient.request", AsyncMock(return_value=resposta_mock)
    ) as mock_request:
        asyncio.run(proxy_request("https://exemplo.com", "/auth/login", request))

    headers_enviados = mock_request.call_args.kwargs["headers"]
    assert "accept-encoding" not in headers_enviados
