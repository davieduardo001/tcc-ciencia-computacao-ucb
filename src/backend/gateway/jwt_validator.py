from typing import Optional
from jose import JWTError, jwt
from shared.config import get_settings

settings = get_settings()


def decodificar_token_jwt(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None
