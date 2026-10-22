# Rotas do Web Push do alerta de proximidade — US #172, continuação.
#
#   GET    /push/chave       a chave pública VAPID (applicationServerKey) e se
#                            o push está disponível neste ambiente
#   PUT    /push/inscricao   registra (ou atualiza) a inscrição deste aparelho
#   DELETE /push/inscricao   remove a inscrição deste aparelho (idempotente)
#
# O dono da inscrição vem do X-User-Id que o Gateway escreve a partir da
# sessão (mobilidade/dependencies.py), nunca do corpo. O corpo de PUT é o
# `PushSubscription.toJSON()` do navegador, sem adaptação.
#
# Sem as três variáveis VAPID o push fica indisponível: GET responde
# `disponivel: false` (a tela esconde o controle) e PUT responde 503. Nada
# aqui levanta erro por falta de configuração.

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from mobilidade import web_push
from mobilidade.dependencies import get_usuario_atual_id
from shared.database import get_db

router = APIRouter()

MENSAGEM_INDISPONIVEL = "Avisos com a tela bloqueada não estão disponíveis no momento."
MENSAGEM_SERVICO_NAO_ACEITO = (
    "Este navegador usa um serviço de notificações que o Movecity não aceita."
)
MENSAGEM_CHAVES_INVALIDAS = "Os dados da inscrição deste aparelho são inválidos."


class ChavePushResponse(BaseModel):
    disponivel: bool
    chave_publica: str | None = None


class ChavesInscricao(BaseModel):
    p256dh: str = Field(min_length=1, max_length=255)
    auth: str = Field(min_length=1, max_length=64)


class InscricaoRequest(BaseModel):
    endpoint: str = Field(min_length=1, max_length=1024)
    keys: ChavesInscricao


class RemocaoRequest(BaseModel):
    endpoint: str = Field(min_length=1, max_length=1024)


class InscricaoResponse(BaseModel):
    ativa: bool = True


@router.get("/push/chave", response_model=ChavePushResponse)
def chave_publica(_usuario_id: uuid.UUID = Depends(get_usuario_atual_id)):
    """Autenticada como as demais: só quem está logado precisa da chave."""
    config = web_push.configuracao_vapid_do_ambiente()
    if not config.disponivel:
        return ChavePushResponse(disponivel=False)
    return ChavePushResponse(disponivel=True, chave_publica=config.chave_publica)


@router.put("/push/inscricao", response_model=InscricaoResponse)
def registrar(
    corpo: InscricaoRequest,
    usuario_id: uuid.UUID = Depends(get_usuario_atual_id),
    db: Session = Depends(get_db),
):
    if not web_push.configuracao_vapid_do_ambiente().disponivel:
        raise HTTPException(status_code=503, detail=MENSAGEM_INDISPONIVEL)
    # Antes de qualquer gravação: este endereço será alvo de um POST do
    # servidor (ver web_push.endpoint_permitido).
    if not web_push.endpoint_permitido(corpo.endpoint):
        raise HTTPException(status_code=422, detail=MENSAGEM_SERVICO_NAO_ACEITO)
    if not web_push.chaves_validas(corpo.keys.p256dh, corpo.keys.auth):
        raise HTTPException(status_code=422, detail=MENSAGEM_CHAVES_INVALIDAS)

    web_push.registrar_inscricao(
        db, usuario_id, corpo.endpoint, corpo.keys.p256dh, corpo.keys.auth
    )
    return InscricaoResponse()


@router.delete("/push/inscricao", status_code=204)
def remover(
    corpo: RemocaoRequest,
    usuario_id: uuid.UUID = Depends(get_usuario_atual_id),
    db: Session = Depends(get_db),
):
    """Sempre 204: repetir não dá erro e quem não é dono não descobre nada."""
    web_push.remover_inscricao(db, usuario_id, corpo.endpoint)
    return Response(status_code=204)
