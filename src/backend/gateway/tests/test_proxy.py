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


# ---------------------------------------------------------------------------
# Issue #188 — o X-User-Id que chega ao serviço é SEMPRE o do Gateway
# ---------------------------------------------------------------------------


def _headers_enviados_ao_servico(headers_do_cliente: dict, extra_headers: dict | None):
    """Roda o proxy e devolve os headers que ele mandou ao serviço de destino."""
    request = _fake_request(headers_do_cliente, metodo="GET", path="/mobilidade/viagens/ativa")

    resposta_mock = AsyncMock()
    resposta_mock.status_code = 200
    resposta_mock.content = b"{}"
    resposta_mock.headers = {}

    with patch(
        "httpx.AsyncClient.request", AsyncMock(return_value=resposta_mock)
    ) as mock_request:
        asyncio.run(
            proxy_request(
                "https://exemplo.com",
                "/mobilidade/viagens/ativa",
                request,
                extra_headers=extra_headers,
            )
        )

    return mock_request.call_args.kwargs["headers"]


def _valores(headers: dict, nome: str) -> list[str]:
    """Todos os valores de um header, sem depender de capitalização."""
    import httpx

    return httpx.Headers(headers).get_list(nome)


def test_x_user_id_do_cliente_nao_chega_ao_servico_quando_o_gateway_tem_identidade():
    """
    O dict de saída tinha as chaves do cliente em minúsculas ("x-user-id") e
    o Gateway acrescentava "X-User-Id": as duas sobreviviam, o serviço
    recebia DOIS headers e lia o primeiro — o do cliente.
    """
    enviados = _headers_enviados_ao_servico(
        {"x-user-id": "ATACANTE", "cookie": "a=b"},
        {"X-User-Id": "SESSAO-REAL"},
    )

    assert _valores(enviados, "x-user-id") == ["SESSAO-REAL"]


def test_x_user_id_do_cliente_e_descartado_em_qualquer_capitalizacao():
    for variante in ("X-User-Id", "X-USER-ID", "x-User-ID"):
        enviados = _headers_enviados_ao_servico(
            {variante: "ATACANTE"}, {"X-User-Id": "SESSAO-REAL"}
        )
        assert _valores(enviados, "x-user-id") == ["SESSAO-REAL"], variante


def test_sem_identidade_no_gateway_o_x_user_id_do_cliente_tambem_nao_passa():
    """Rota pública: o Gateway não tem identidade, e o cliente não pode fornecer uma."""
    enviados = _headers_enviados_ao_servico({"x-user-id": "ATACANTE"}, None)

    assert _valores(enviados, "x-user-id") == []


def test_extra_headers_em_qualquer_capitalizacao_substituem_o_do_cliente():
    enviados = _headers_enviados_ao_servico(
        {"x-user-id": "ATACANTE"}, {"x-user-id": "SESSAO-REAL"}
    )

    assert _valores(enviados, "x-user-id") == ["SESSAO-REAL"]


def test_os_demais_headers_do_cliente_continuam_sendo_repassados():
    enviados = _headers_enviados_ao_servico(
        {
            "x-user-id": "ATACANTE",
            "cookie": "access_token=abc",
            "authorization": "Bearer xyz",
            "content-type": "application/json",
            "host": "gateway.exemplo.com",
        },
        {"X-User-Id": "SESSAO-REAL"},
    )

    assert _valores(enviados, "cookie") == ["access_token=abc"]
    assert _valores(enviados, "authorization") == ["Bearer xyz"]
    assert _valores(enviados, "content-type") == ["application/json"]
    # o `host` do Gateway não pode vazar para o serviço
    assert _valores(enviados, "host") == []


def test_o_servico_de_dominio_le_a_identidade_da_sessao_e_nao_a_do_cliente():
    """
    Ponta a ponta no limite do serviço: o app de domínio (ASGI de verdade)
    lê o `X-User-Id` do jeito que `colaboracao/dependencies.py` lê.
    """
    import httpx
    from fastapi import FastAPI, Request

    servico = FastAPI()

    @servico.get("/quem-sou-eu")
    def quem_sou_eu(request: Request):
        return {"id": request.headers.get("X-User-Id")}

    enviados = _headers_enviados_ao_servico(
        {"x-user-id": "ATACANTE"}, {"X-User-Id": "SESSAO-REAL"}
    )

    async def chamar():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=servico), base_url="http://servico"
        ) as cliente:
            return await cliente.get("/quem-sou-eu", headers=enviados)

    assert asyncio.run(chamar()).json() == {"id": "SESSAO-REAL"}
