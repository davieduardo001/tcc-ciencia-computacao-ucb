from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime


class RegistroRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: str
    status: str
    criado_em: datetime

    class Config:
        from_attributes = True


class MensagemResponse(BaseModel):
    mensagem: str
