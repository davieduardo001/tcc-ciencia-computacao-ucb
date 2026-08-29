from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth.database import get_db
from auth.service import decodificar_token
from auth.models.usuario import Usuario


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Usuario:
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
        )

    payload = decodificar_token(access_token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    usuario = db.query(Usuario).filter(Usuario.id == payload.get("sub")).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )

    if usuario.status != "ativo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta inativa ou suspensa",
        )

    return usuario
