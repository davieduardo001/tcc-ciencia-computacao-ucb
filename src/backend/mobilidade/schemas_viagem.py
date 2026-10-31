from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from mobilidade.eta_service import TOLERANCIA_TRAJETO_M


class EmbarqueRequest(BaseModel):
    """
    Corpo do POST /viagens.

    `lat`/`lng` são a posição do usuário **só para confirmar o embarque**
    (RN-16) — o servidor não guarda (RN-06). `usuario_id` não vem aqui: é o
    do X-User-Id que o Gateway injeta.

    US #199 — `compartilha_posicao` é o consentimento LGPD do fallback
    colaborativo, desligado por padrão e SEPARADO do aceite dos Termos.
    Aceitar exige a versão do texto consentido, que fica guardada como
    prova (art. 8º). Nenhuma coordenada é persistida.
    """

    numero_linha: str = Field(min_length=1, max_length=20)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    parada_destino_codigo: str | None = Field(default=None, min_length=1, max_length=12)
    # Issue #216 — o popup de um ônibus específico manda o prefixo dele: o
    # embarque só vale se ESSE veículo estiver perto. Sem prefixo (embarque
    # pela rota), vale qualquer ônibus da linha, como antes.
    veiculo_prefixo: str | None = Field(default=None, min_length=1, max_length=20)
    compartilha_posicao: bool = False
    consentimento_versao: str | None = Field(default=None, max_length=40)

    @field_validator("numero_linha")
    @classmethod
    def _sem_espacos_nas_pontas(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("numero_linha não pode ser vazio")
        return valor

    @model_validator(mode="after")
    def _consentimento_exige_versao(self) -> "EmbarqueRequest":
        if self.compartilha_posicao and not (
            self.consentimento_versao and self.consentimento_versao.strip()
        ):
            raise ValueError(
                "consentimento_versao é obrigatório quando compartilha_posicao"
            )
        return self


class PosicaoColaborativaRequest(BaseModel):
    """
    Corpo do POST /viagens/{id}/posicao (US #199) — posição do ÔNIBUS,
    informada por passageiro com consentimento vigente.

    `lat`/`lng` nunca são persistidos: entram no armazenamento efêmero
    (memória, ~120 s) e só alimentam o ETA de outros passageiros.
    `precisao_m` acima da tolerância do traçado não dá para validar
    encaixe (RN-C4), então não é aceita.
    """

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    precisao_m: float | None = Field(default=None, ge=0, le=TOLERANCIA_TRAJETO_M)


class PosicaoColaborativaResponse(BaseModel):
    """
    Resultado da leitura: `aceita` entra no armazenamento efêmero;
    `descartada` não guarda nada e devolve o motivo (observabilidade sem
    dado pessoal).
    """

    aceita: bool
    motivo: str | None = None


class DestinoRequest(BaseModel):
    """Corpo do PUT /viagens/{id}/destino. `null` tira o destino."""

    parada_destino_codigo: str | None = Field(default=None, min_length=1, max_length=12)


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
    # US #199 — o próprio dono vê se o compartilhamento está ativo
    # (consentimento vigente). Sem coordenada nenhuma na resposta.
    compartilha_posicao: bool = False

    @field_validator("embarcou_em", "encerrada_em")
    @classmethod
    def _marca_como_utc(cls, valor: datetime | None) -> datetime | None:
        # As colunas guardam UTC sem fuso. Sem marcar, o JSON sairia sem
        # "Z" e o navegador leria como horário local.
        if valor is not None and valor.tzinfo is None:
            return valor.replace(tzinfo=timezone.utc)
        return valor


class AlertaProximidadeResponse(BaseModel):
    """
    Aviso "o ônibus está chegando na sua parada" (US #172), ainda não visto.

    Sem `usuario_id` nem `viagem_id`: o app já sabe de quem e de qual viagem.
    """

    id: str
    parada_codigo: str
    parada_nome: str | None = None
    eta_minutos: float | None = None
    disparado_em: datetime

    @field_validator("disparado_em")
    @classmethod
    def _marca_como_utc(cls, valor: datetime) -> datetime:
        # Coluna em UTC sem fuso; sem marcar, o navegador leria como local.
        return valor.replace(tzinfo=timezone.utc) if valor.tzinfo is None else valor


class ViagemAtivaResponse(BaseModel):
    ativa: bool
    viagem: ViagemResponse | None = None
    sinal: Literal["ao_vivo", "sem_sinal"] | None = None
    veiculo: VeiculoViagemResponse | None = None
    destino: DestinoViagemResponse | None = None
    proxima_parada: ParadaViagemResponse | None = None
    paradas_restantes: list[ParadaViagemResponse] = []
    # US #172 — o aviso de proximidade pendente (ou None).
    alerta_proximidade: AlertaProximidadeResponse | None = None
