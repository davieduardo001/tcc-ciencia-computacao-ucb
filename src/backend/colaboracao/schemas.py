from pydantic import BaseModel, Field
from typing import Optional


class PreferenciaNotificacaoResponse(BaseModel):
    id: str
    usuario_id: str
    antecedencia_minutos: int
    notificacoes_ativas: bool
    alerta_chegada: bool
    alerta_cancelamento: bool

    class Config:
        from_attributes = True


class AntecedenciaInput(BaseModel):
    antecedencia_minutos: int = Field(..., description="5, 10, 30 ou 60 minutos")


class TipoNotificacaoInput(BaseModel):
    ativo: bool


class ToggleNotificacoesInput(BaseModel):
    ativas: bool


class RespostaGenerica(BaseModel):
    mensagem: str
