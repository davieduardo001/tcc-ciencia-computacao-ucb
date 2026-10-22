import httpx
from fastapi import Request, Response

# Headers que só o Gateway pode definir. A identidade do usuário chega aos
# serviços de domínio por aqui, então o valor que o cliente mandar NUNCA pode
# passar — nem quando o Gateway não tem identidade a acrescentar (rota
# pública). Comparação sem diferenciar maiúsculas: HTTP não diferencia, e o
# Starlette lê o primeiro header que casar.
HEADERS_SO_DO_GATEWAY = frozenset({"x-user-id"})


async def proxy_request(service_url: str, path: str, request: Request, extra_headers: dict = None) -> Response:
    """Proxy genérico para serviços backend.

    Recebe a request do frontend, encaminha para o serviço backend
    e retorna a response para o frontend.

    extra_headers: headers internos adicionais (ex.: X-User-Id derivado
    da identidade autenticada pelo gateway middleware). Usado pelo
    gateway para encaminhar a identidade do usuário aos serviços de
    domínio. Esse header NÃO deve ser enviado diretamente pelo cliente:
    se vier, é descartado (HEADERS_SO_DO_GATEWAY).
    """
    body = await request.body()

    # A query string precisa ser repassada explicitamente: o `{path:path}`
    # das rotas de proxy captura só o caminho, e montar a URL de destino
    # sem ela descartava todo parâmetro silenciosamente. Onde o parâmetro
    # tem default o estrago era invisível (o autocomplete de linhas
    # chegava como `q=""` e devolvia as 923 linhas do DF em vez do
    # filtro); onde é obrigatório, virava 422 (a rota origem→destino da
    # US #20). Repassada já codificada, sem decodificar e recodificar,
    # pra não corromper acento nem espaço.
    url = f"{service_url}{path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"

    headers = {
        nome.lower(): valor
        for nome, valor in request.headers.items()
        if nome.lower() not in HEADERS_SO_DO_GATEWAY
    }
    headers.pop("host", None)
    headers.pop("accept-encoding", None)

    if extra_headers:
        # Chaves em minúsculas, como as de cima: com "X-User-Id" e
        # "x-user-id" no mesmo dict, os dois iam ao serviço (issue #188).
        headers.update({nome.lower(): valor for nome, valor in extra_headers.items()})

    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body if body else None,
                timeout=30.0,
            )
    except httpx.TimeoutException:
        return Response(
            content='{"detail": "Serviço demorou demais para responder."}',
            status_code=504,
            media_type="application/json",
        )
    except httpx.ConnectError:
        return Response(
            content='{"detail": "Serviço indisponível no momento."}',
            status_code=502,
            media_type="application/json",
        )

    excluded_headers = {
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    }
    response_headers = {
        k: v
        for k, v in response.headers.items()
        if k.lower() not in excluded_headers
    }

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=response_headers,
        media_type="application/json",
    )
