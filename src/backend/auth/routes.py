import logging
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.models import Usuario
from auth.schemas import RegistroRequest, RegistroResponse
from auth.security import hash_senha
from shared.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/hello")
def hello():
    return {"service": "auth", "status": "ok"}


@router.post("/registro", response_model=RegistroResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(dados: RegistroRequest, db: Session = Depends(get_db)):
    email_existente = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if email_existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este e-mail já está em uso.")

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        lgpd_accepted_at=datetime.now(timezone.utc),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    # TODO(debito-tecnico): nenhum provedor de e-mail configurado ainda — token so logado, nao enviado.
    token_confirmacao = secrets.token_urlsafe(32)
    logger.info("Email de confirmacao (stub) para %s: %s", usuario.email, token_confirmacao)

    return RegistroResponse(
        id=str(usuario.id),
        nome=usuario.nome,
        email=usuario.email,
        mensagem="Verifique seu e-mail para confirmar a conta.",
    )
