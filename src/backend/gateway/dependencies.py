from fastapi import Depends, HTTPException, Request, status


def get_usuario_atual(request: Request) -> str:
    usuario_id = getattr(request.state, "usuario_id", None)
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
        )
    return usuario_id
