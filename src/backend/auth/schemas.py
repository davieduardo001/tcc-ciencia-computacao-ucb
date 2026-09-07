from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginInput(BaseModel):
    email: str
    senha: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class GoogleLoginInput(BaseModel):
    id_token: str


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


class GoogleLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    mensagem: str = "Login via Google realizado com sucesso."
    account_linking_pending: bool = False
    account_linking_required: bool = False


class GoogleConfirmLinkInput(BaseModel):
    id_token: str
    email: str
    google_id: str


class UsuarioResponse(BaseModel):
    id: str
    nome: str
    email: str
    status: str
    account_linking_pending: bool = False


class SolicitacaoResetSenha(BaseModel):
    email: EmailStr


class RedefinirSenha(BaseModel):
    token: str
    nova_senha: str
    confirmacao_senha: str


class RespostaGenerica(BaseModel):
    mensagem: str