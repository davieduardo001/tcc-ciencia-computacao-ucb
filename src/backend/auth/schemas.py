from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginInput(BaseModel):
    email: str
    senha: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegistrarInput(BaseModel):
    nome: str
    email: str
    senha: str
    termos_aceitos: bool


class RegistrarResponse(BaseModel):
    id: str
    nome: str
    email: str
    mensagem: str


class UsuarioResponse(BaseModel):
    id: str
    nome: str
    email: str
    status: str


class SolicitacaoResetSenha(BaseModel):
    email: EmailStr


class RedefinirSenha(BaseModel):
    token: str
    nova_senha: str
    confirmacao_senha: str


class RespostaGenerica(BaseModel):
    mensagem: str