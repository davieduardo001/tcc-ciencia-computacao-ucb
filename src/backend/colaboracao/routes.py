import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from shared.database import get_db
from colaboracao.models import PreferenciaNotificacao
from colaboracao.schemas import (
    PreferenciaNotificacaoResponse,
    AntecedenciaInput,
    TipoNotificacaoInput,
    ToggleNotificacoesInput,
    RespostaGenerica,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# US #22 — Rota de demonstração / teste do Worker de monitoramento
# ---------------------------------------------------------------------------

@router.get("/hello")
def hello():
    return {"service": "colaboracao", "status": "ok"}


@router.get("/teste-vitoria")
def teste_vitoria():
    return {"service": "colaboracao", "autor": "Vitoria-Albuquerque", "mensagem": "hello world"}


@router.get("/teste-gualberto")
def teste_gualberto():
    return {"service": "colaboracao", "autor": "gualbertonathalia", "mensagem": "hello world"}


# ---------------------------------------------------------------------------
# US #29 — Preferências de Notificação
# ---------------------------------------------------------------------------

def _obter_ou_criar_preferencias(usuario_id: str, db: Session) -> PreferenciaNotificacao:
    preferencia = (
        db.query(PreferenciaNotificacao)
        .filter(PreferenciaNotificacao.usuario_id == usuario_id)
        .first()
    )
    if not preferencia:
        preferencia = PreferenciaNotificacao(
            id=uuid.uuid4(),
            usuario_id=uuid.UUID(usuario_id) if isinstance(usuario_id, str) else usuario_id,
            antecedencia_minutos=30,
            notificacoes_ativas=True,
            alerta_chegada=True,
            alerta_cancelamento=True,
            criado_em=datetime.utcnow(),
            atualizado_em=datetime.utcnow(),
        )
        db.add(preferencia)
        db.commit()
        db.refresh(preferencia)
    return preferencia


@router.get("/preferencias/{usuario_id}", response_model=PreferenciaNotificacaoResponse)
def carregar_preferencias(usuario_id: str, db: Session = Depends(get_db)):
    preferencia = _obter_ou_criar_preferencias(usuario_id, db)
    return PreferenciaNotificacaoResponse(
        id=str(preferencia.id),
        usuario_id=str(preferencia.usuario_id),
        antecedencia_minutos=preferencia.antecedencia_minutos,
        notificacoes_ativas=preferencia.notificacoes_ativas,
        alerta_chegada=preferencia.alerta_chegada,
        alerta_cancelamento=preferencia.alerta_cancelamento,
    )


@router.put("/preferencias/{usuario_id}/antecedencia", response_model=PreferenciaNotificacaoResponse)
def salvar_antecedencia(usuario_id: str, dados: AntecedenciaInput, db: Session = Depends(get_db)):
    if dados.antecedencia_minutos not in PreferenciaNotificacao.ANTECEDENCIAS_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail=f"Antecedência inválida. Valores permitidos: {PreferenciaNotificacao.ANTECEDENCIAS_PERMITIDAS}",
        )

    preferencia = _obter_ou_criar_preferencias(usuario_id, db)
    preferencia.antecedencia_minutos = dados.antecedencia_minutos
    preferencia.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(preferencia)

    return PreferenciaNotificacaoResponse(
        id=str(preferencia.id),
        usuario_id=str(preferencia.usuario_id),
        antecedencia_minutos=preferencia.antecedencia_minutos,
        notificacoes_ativas=preferencia.notificacoes_ativas,
        alerta_chegada=preferencia.alerta_chegada,
        alerta_cancelamento=preferencia.alerta_cancelamento,
    )


@router.put("/preferencias/{usuario_id}/tipo/{tipo}", response_model=PreferenciaNotificacaoResponse)
def atualizar_tipo_notificacao(usuario_id: str, tipo: str, dados: TipoNotificacaoInput, db: Session = Depends(get_db)):
    if tipo not in ("chegada", "cancelamento"):
        raise HTTPException(
            status_code=400,
            detail="Tipo inválido. Valores permitidos: chegada, cancelamento",
        )

    preferencia = _obter_ou_criar_preferencias(usuario_id, db)

    if tipo == "chegada":
        preferencia.alerta_chegada = dados.ativo
    elif tipo == "cancelamento":
        preferencia.alerta_cancelamento = dados.ativo

    preferencia.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(preferencia)

    return PreferenciaNotificacaoResponse(
        id=str(preferencia.id),
        usuario_id=str(preferencia.usuario_id),
        antecedencia_minutos=preferencia.antecedencia_minutos,
        notificacoes_ativas=preferencia.notificacoes_ativas,
        alerta_chegada=preferencia.alerta_chegada,
        alerta_cancelamento=preferencia.alerta_cancelamento,
    )


@router.put("/preferencias/{usuario_id}/desativar-todas", response_model=PreferenciaNotificacaoResponse)
def desativar_todas_notificacoes(usuario_id: str, dados: ToggleNotificacoesInput, db: Session = Depends(get_db)):
    preferencia = _obter_ou_criar_preferencias(usuario_id, db)
    preferencia.notificacoes_ativas = dados.ativas
    preferencia.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(preferencia)

    return PreferenciaNotificacaoResponse(
        id=str(preferencia.id),
        usuario_id=str(preferencia.usuario_id),
        antecedencia_minutos=preferencia.antecedencia_minutos,
        notificacoes_ativas=preferencia.notificacoes_ativas,
        alerta_chegada=preferencia.alerta_chegada,
        alerta_cancelamento=preferencia.alerta_cancelamento,
    )
