import asyncio
from unittest.mock import AsyncMock, patch

from starlette.requests import Request

from gateway.proxy import proxy_request


def _fake_request(
    headers: dict,
    *,
    metodo: str = "POST",
    path: str = "/auth/login",
    query_string: bytes = b"",
) -> Request:
    raw_headers = [
        (k.lower().encode(), v.encode()) for k, v in headers.items()
    ]
    scope = {
        "type": "http",
        "method": metodo,
        "headers": raw_headers,
        "path": path,
        "query_string": query_string,
    }

    async def receive():
        return {"type": "http.request", "body": b"{}", "more_body": False}

    return Request(scope, receive)


def _proxiar(request: Request, destino: str):
    """Roda o proxy com o httpx mockado e devolve a URL que ele chamou."""
    resposta_mock = AsyncMock()
    resposta_mock.status_code = 200
    resposta_mock.content = b"[]"
    resposta_mock.headers = {}

    with patch(
        "httpx.AsyncClient.request", AsyncMock(return_value=resposta_mock)
    ) as mock_request:
        asyncio.run(proxy_request("https://exemplo.com", destino, request))

    return mock_request.call_args.kwargs["url"]


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


def test_repassa_a_query_string_para_o_servico():
    """
    Regressão séria: a URL de destino era montada só com o path, e toda
    query string era descartada silenciosamente.

    O estrago era invisível onde o parâmetro tem default — o autocomplete
    de linhas (`?q=`) chegava no serviço como `q=""` e devolvia as 923
    linhas do DF em vez do filtro, o que aparecia pro usuário como "a
    busca não filtra nada". E era um erro visível onde o parâmetro é
    obrigatório: a rota origem→destino (US #20) recebia zero coordenadas
    e respondia 422.
    """
    request = _fake_request(
        {"content-type": "application/json"},
        metodo="GET",
        path="/mobilidade/rotas",
        query_string=b"origem_lat=-15.86&origem_lng=-48.03&destino_lat=-15.83",
    )

    url = _proxiar(request, "/mobilidade/rotas")

    assert url == (
        "https://exemplo.com/mobilidade/rotas"
        "?origem_lat=-15.86&origem_lng=-48.03&destino_lat=-15.83"
    )


def test_sem_query_string_a_url_nao_ganha_interrogacao():
    request = _fake_request(
        {"content-type": "application/json"},
        metodo="GET",
        path="/mobilidade/linhas/0.110",
    )

    url = _proxiar(request, "/mobilidade/linhas/0.110")

    assert url == "https://exemplo.com/mobilidade/linhas/0.110"


def test_preserva_caracteres_codificados_na_query():
    """
    Buscar "Ceilândia" chega como `q=Ceil%C3%A2ndia`. Repassar a query
    já codificada, sem decodificar e recodificar, evita corromper acento
    e espaço no caminho.
    """
    request = _fake_request(
        {"content-type": "application/json"},
        metodo="GET",
        path="/mobilidade/lugares",
        query_string=b"q=Terminal%20Ceil%C3%A2ndia",
    )

    url = _proxiar(request, "/mobilidade/lugares")

    assert url == "https://exemplo.com/mobilidade/lugares?q=Terminal%20Ceil%C3%A2ndia"
