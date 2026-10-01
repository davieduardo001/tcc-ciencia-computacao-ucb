from datetime import datetime

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


# ---------------------------------------------------------------------------
# US #23 — Reportar Ocorrência em uma Linha
# ---------------------------------------------------------------------------


class OcorrenciaInput(BaseModel):
    linha_numero: str = Field(..., min_length=1, max_length=20)
    tipo: str = Field(..., description="atraso, nao_passou, lotacao, obra_via, onibus_quebrou, acidente ou seguranca")
    descricao: Optional[str] = Field(None, max_length=500)
    local: Optional[str] = Field(None, max_length=255, description="Texto livre — fallback de quem negou geolocalização")
    lat: Optional[float] = None
    lng: Optional[float] = None


class OcorrenciaResponse(BaseModel):
    id: str
    linha_numero: str
    tipo: str
    status: str
    contador_confirmacoes: int
    criado_em: datetime
    expira_em: datetime

    class Config:
        from_attributes = True
