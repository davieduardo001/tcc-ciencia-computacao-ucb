from pydantic import BaseModel, EmailStr


class SolicitacaoResetSenha(BaseModel):
    email: EmailStr


class RedefinirSenha(BaseModel):
    token: str
    nova_senha: str
    confirmacao_senha: str


class RespostaGenerica(BaseModel):
    mensagem: str
