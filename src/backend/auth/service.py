from datetime import datetime, timedelta
from typing import Optional
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from shared.config import get_settings
from auth.models.usuario import Usuario
from auth.models.sessao import Sessao

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)


def verificar_senha(senha: str, hash_senha_db: str) -> bool:
    return pwd_context.verify(senha, hash_senha_db)


def criar_access_token(usuario_id: str) -> str:
    expira = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    payload = {
        "sub": usuario_id,
        "exp": expira,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def criar_refresh_token(usuario_id: str) -> str:
    expira = datetime.utcnow() + timedelta(days=7)
    payload = {
        "sub": usuario_id,
        "exp": expira,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decodificar_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def registrar_usuario(db: Session, nome: str, email: str, senha: str) -> Usuario:
    usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario_existente:
        raise ValueError("Email já cadastrado")

    novo_usuario = Usuario(
        nome=nome,
        email=email,
        hash_senha=hash_senha(senha),
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario


def autenticar_usuario(db: Session, email: str, senha: str) -> Optional[Usuario]:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        return None
    if not verificar_senha(senha, usuario.hash_senha):
        return None
    if usuario.status != "ativo":
        return None
    return usuario


def criar_sessao(
    db: Session,
    usuario_id: uuid.UUID,
    refresh_token: str,
    user_agent: str = None,
) -> Sessao:
    expira_em = datetime.utcnow() + timedelta(days=7)

    sessao = Sessao(
        usuario_id=usuario_id,
        refresh_token_hash=hash_senha(refresh_token),
        expira_em=expira_em,
        user_agent=user_agent,
    )
    db.add(sessao)
    db.commit()
    db.refresh(sessao)
    return sessao


def validar_refresh_token(db: Session, refresh_token: str) -> Optional[Sessao]:
    payload = decodificar_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None

    usuario_id = payload.get("sub")
    sessoes = (
        db.query(Sessao)
        .filter(
            Sessao.usuario_id == usuario_id,
            Sessao.revogado == False,
            Sessao.expira_em > datetime.utcnow(),
        )
        .all()
    )

    for sessao in sessoes:
        if verificar_senha(refresh_token, sessao.refresh_token_hash):
            return sessao

    return None


def revogar_sessao(db: Session, sessao_id: uuid.UUID) -> bool:
    sessao = db.query(Sessao).filter(Sessao.id == sessao_id).first()
    if not sessao:
        return False
    sessao.revogado = True
    db.commit()
    return True


def revogar_todas_sessoes_usuario(db: Session, usuario_id: uuid.UUID) -> int:
    resultado = (
        db.query(Sessao)
        .filter(Sessao.usuario_id == usuario_id, Sessao.revogado == False)
        .update({"revogado": True})
    )
    db.commit()
    return resultado
