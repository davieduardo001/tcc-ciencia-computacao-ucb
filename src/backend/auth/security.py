from typing import Optional

import bcrypt
from jose import JWTError, jwt
from shared.config import get_settings

settings = get_settings()


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, hash_senha: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), hash_senha.encode("utf-8"))


def criar_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire_minutes = settings.JWT_EXPIRATION_MINUTES
    from datetime import datetime, timedelta
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def criar_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire_days = 7
    from datetime import datetime, timedelta
    expire = datetime.utcnow() + timedelta(days=expire_days)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decodificar_access_token(token: str) -> Optional[dict]:
    """
    Decodifica e valida a assinatura de um access token.

    Usado pelo endpoint GET /auth/me: como o Auth Service é acessado
    pelo Gateway via URL publica do Fly.io (nao rede privada), nao da
    pra confiar num header repassado pelo Gateway sem verificacao —
    o Auth Service precisa validar a assinatura do token ele mesmo.

    Retorna None para token ausente, expirado ou invalido.
    """
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None