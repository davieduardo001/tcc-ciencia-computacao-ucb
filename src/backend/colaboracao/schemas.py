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


# ---------------------------------------------------------------------------
# US #25 — Salvar e Visualizar Rota Favorita
# ---------------------------------------------------------------------------


class RotaFavoritaInput(BaseModel):
    """Dados enviados pelo frontend ao criar uma rota favorita.

    `usuario_id` NÃO é aceito aqui — o usuário é obtido exclusivamente
    do header `X-User-Id` injetado pelo Gateway após validação do JWT.
    Coordenadas como float separados, sem GeoPoint (tipo inexistente no projeto).
    """

    numero_linha: str = Field(..., min_length=1, max_length=20)
    nome_linha: str = Field(..., min_length=1, max_length=255)
    label: str = Field(..., min_length=1, max_length=100)
    origem_lat: float = Field(..., ge=-90.0, le=90.0)
    origem_lng: float = Field(..., ge=-180.0, le=180.0)
    destino_lat: float = Field(..., ge=-90.0, le=90.0)
    destino_lng: float = Field(..., ge=-180.0, le=180.0)


class RotaFavoritaResponse(BaseModel):
    """Resposta retornada após criar ou listar uma rota favorita."""

    id: str
    usuario_id: str
    numero_linha: str
    nome_linha: str
    label: str
    origem_lat: float
    origem_lng: float
    destino_lat: float
    destino_lng: float
    criado_em: datetime

    class Config:
        from_attributes = True
