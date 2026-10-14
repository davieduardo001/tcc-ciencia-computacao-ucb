from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EmbarqueRequest(BaseModel):
    """
    Corpo do POST /viagens.

    `lat`/`lng` são a posição do usuário **só para confirmar o embarque**
    (RN-16) — o servidor não guarda (RN-06). `usuario_id` não vem aqui: é o
    do X-User-Id que o Gateway injeta.
    """

    numero_linha: str = Field(min_length=1, max_length=20)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    parada_destino_codigo: str | None = Field(default=None, min_length=1, max_length=12)

    @field_validator("numero_linha")
    @classmethod
    def _sem_espacos_nas_pontas(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("numero_linha não pode ser vazio")
        return valor


class ParadaViagemResponse(BaseModel):
    codigo: str
    nome: str
    lat: float
    lng: float


class DestinoViagemResponse(ParadaViagemResponse):
    # O ônibus já passou da parada de destino: o app avisa em vez de seguir
    # mostrando "faltam N paradas".
    ultrapassado: bool = False


class VeiculoViagemResponse(BaseModel):
    prefixo: str
    lat: float
    lng: float
    direcao: float | None = None
    atualizado_em: str


class ViagemResponse(BaseModel):
    id: str
    numero_linha: str
    sentido: str | None = None
    veiculo_prefixo: str
    parada_destino_codigo: str | None = None
    embarcou_em: datetime
    encerrada_em: datetime | None = None
    motivo_encerramento: str | None = None

    @field_validator("embarcou_em", "encerrada_em")
    @classmethod
    def _marca_como_utc(cls, valor: datetime | None) -> datetime | None:
        # As colunas guardam UTC sem fuso. Sem marcar, o JSON sairia sem
        # "Z" e o navegador leria como horário local.
        if valor is not None and valor.tzinfo is None:
            return valor.replace(tzinfo=timezone.utc)
        return valor


class ViagemAtivaResponse(BaseModel):
    ativa: bool
    viagem: ViagemResponse | None = None
    sinal: Literal["ao_vivo", "sem_sinal"] | None = None
    veiculo: VeiculoViagemResponse | None = None
    destino: DestinoViagemResponse | None = None
    proxima_parada: ParadaViagemResponse | None = None
    paradas_restantes: list[ParadaViagemResponse] = []
