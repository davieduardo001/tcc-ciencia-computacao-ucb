import re

from pydantic import BaseModel, EmailStr, field_validator

_SENHA_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


class RegistroRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    termos_aceitos: bool

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Campo obrigatório")
        return v

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, v: str) -> str:
        if not _SENHA_REGEX.match(v):
            raise ValueError("A senha deve ter ao menos 8 caracteres, incluindo letras e números")
        return v

    @field_validator("termos_aceitos")
    @classmethod
    def validar_termos_aceitos(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Você deve aceitar os termos de uso")
        return v


class RegistroResponse(BaseModel):
    id: str
    nome: str
    email: str
    mensagem: str
