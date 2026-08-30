from fastapi import APIRouter, Request, Response

from gateway.config import get_gateway_settings
from gateway.cookies import clear_auth_cookies, set_auth_cookies
from gateway.proxy import proxy_request

router = APIRouter()
settings = get_gateway_settings()


@router.get("/hello")
def hello():
    return {"service": "gateway", "status": "ok"}


# ============================================
# AUTH (proxy para Auth Service)
# ============================================


@router.post("/auth/login")
async def login(request: Request):
    """Login: proxy + setar cookies httpOnly."""
    response = await proxy_request(
        settings.AUTH_SERVICE_URL,
        "/auth/login",
        request,
    )

    if response.status_code == 200:
        data = response.json()
        set_auth_cookies(
            response,
            data.get("access_token", ""),
            data.get("refresh_token", ""),
        )

    return response


@router.post("/auth/registrar")
async def registrar(request: Request):
    """Registro de novo usuário: proxy para Auth Service."""
    return await proxy_request(
        settings.AUTH_SERVICE_URL,
        "/auth/registrar",
        request,
    )


@router.post("/auth/refresh")
async def refresh(request: Request):
    """Refresh token: proxy + atualizar cookies."""
    response = await proxy_request(
        settings.AUTH_SERVICE_URL,
        "/auth/refresh",
        request,
    )

    if response.status_code == 200:
        data = response.json()
        set_auth_cookies(
            response,
            data.get("access_token", ""),
            data.get("refresh_token", ""),
        )

    return response


@router.post("/auth/logout")
async def logout(request: Request):
    """Logout: proxy + limpar cookies."""
    response = await proxy_request(
        settings.AUTH_SERVICE_URL,
        "/auth/logout",
        request,
    )

    clear_auth_cookies(response)

    return response


# ============================================
# MOBILIDADE (proxy para Mobilidade Service)
# ============================================


@router.api_route(
    "/mobilidade/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
)
async def mobilidade_proxy(path: str, request: Request):
    """Proxy para Mobilidade Service."""
    return await proxy_request(
        settings.MOBILIDADE_SERVICE_URL,
        f"/mobilidade/{path}",
        request,
    )


# ============================================
# COLABORACAO (proxy para Colaboracao Service)
# ============================================


@router.api_route(
    "/colaboracao/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
)
async def colaboracao_proxy(path: str, request: Request):
    """Proxy para Colaboracao Service."""
    return await proxy_request(
        settings.COLABORACAO_SERVICE_URL,
        f"/colaboracao/{path}",
        request,
    )
