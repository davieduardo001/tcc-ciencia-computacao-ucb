from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from gateway.jwt_validator import decodificar_token_jwt


class AutenticacaoMiddleware(BaseHTTPMiddleware):
    ROTAS_PUBLICAS = [
        "/gateway/hello",
        "/gateway/health",
        "/auth/login",
        "/auth/registrar",
        "/auth/refresh",
    ]

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.ROTAS_PUBLICAS:
            return await call_next(request)

        access_token = request.cookies.get("access_token")
        if not access_token:
            return Response(
                content='{"detail": "Não autenticado"}',
                status_code=401,
                media_type="application/json",
            )

        payload = decodificar_token_jwt(access_token)
        if not payload:
            return Response(
                content='{"detail": "Token inválido ou expirado"}',
                status_code=401,
                media_type="application/json",
            )

        request.state.usuario_id = payload.get("sub")

        response = await call_next(request)
        return response
