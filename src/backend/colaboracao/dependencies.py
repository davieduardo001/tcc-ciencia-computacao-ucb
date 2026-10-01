import uuid

from fastapi import HTTPException, Request, status


def get_usuario_atual_id(request: Request) -> uuid.UUID:
    """
    Lê o X-User-Id encaminhado pelo Gateway (identidade já validada via
    JWT — nenhum token é lido aqui). Mesmo contrato do `get_usuario_atual`
    do gateway, mas do lado do serviço de domínio.
    """
    usuario_id = request.headers.get("X-User-Id")
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
        )
    try:
        return uuid.UUID(usuario_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identidade de usuário inválida",
        )
