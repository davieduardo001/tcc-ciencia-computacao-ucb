from fastapi import Response


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    """Setar cookies httpOnly de autenticação.

    - access_token: 60 min, path=/api, SameSite=Lax
    - refresh_token: 7 dias, path=/api/auth, SameSite=Strict
    """
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api",
        max_age=3600,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api/auth",
        max_age=604800,
    )


def clear_auth_cookies(response: Response) -> None:
    """Limpar cookies de autenticação."""
    response.delete_cookie(key="access_token", path="/api")
    response.delete_cookie(key="refresh_token", path="/api/auth")
