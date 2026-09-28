from fastapi import Response


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    """Setar cookies httpOnly de autenticação.

    - access_token: 60 min, path=/api, SameSite=None
    - refresh_token: 7 dias, path=/api/auth, SameSite=None

    SameSite=None (não Lax/Strict): o frontend (movecity-frontend.vercel.app)
    e o Gateway (movecity-gateway.fly.dev) são domínios diferentes — é
    cross-site de verdade, não só cross-origin de porta local. Com
    Lax/Strict, o navegador não envia o cookie em fetch() cross-site (só
    em navegação de topo), então qualquer chamada que dependesse só do
    cookie (ex: GET /auth/me) chegava sem cookie e caía em 401, mesmo
    logo após um login bem-sucedido. secure=True é obrigatório junto com
    SameSite=None (senão o navegador ignora o cookie).
    """
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/api",
        max_age=3600,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/api/auth",
        max_age=604800,
    )


def clear_auth_cookies(response: Response) -> None:
    """Limpar cookies de autenticação."""
    response.delete_cookie(key="access_token", path="/api")
    response.delete_cookie(key="refresh_token", path="/api/auth")
