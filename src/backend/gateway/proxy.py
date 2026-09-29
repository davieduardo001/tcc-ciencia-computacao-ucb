import httpx
from fastapi import Request, Response


async def proxy_request(service_url: str, path: str, request: Request, extra_headers: dict = None) -> Response:
    """Proxy genérico para serviços backend.

    Recebe a request do frontend, encaminha para o serviço backend
    e retorna a response para o frontend.

    extra_headers: headers internos adicionais (ex.: X-User-Id derivado
    da identidade autenticada pelo gateway middleware). Usado pelo
    gateway para encaminhar a identidade do usuário aos serviços de
    domínio. Esse header NÃO deve ser enviado diretamente pelo cliente.
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

    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("accept-encoding", None)

    if extra_headers:
        headers.update(extra_headers)

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
