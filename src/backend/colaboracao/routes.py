import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from shared.database import get_db
from colaboracao.deduplicador import Deduplicador
from colaboracao.eta_service import ETAService
from colaboracao.monitoring_worker import MonitoramentoWorker
from colaboracao.providers.eta_mock import ETAMockProvider
from colaboracao.providers.favoritos_mock import FavoritosMockProvider
from colaboracao.push_service import PushService
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
# Estado compartilhado da demonstração da US #22
#
# Instâncias mantidas em memória durante a vida do processo para que o
# Deduplicador e o PushService preservem estado entre chamadas à rota.
# Em produção, esses objetos serão substituídos pelas implementações reais
# (US #25, #29, #19) sem alterar esta rota.
# ---------------------------------------------------------------------------
_demo_push      = PushService()
_demo_dedup     = Deduplicador()
_demo_eta       = ETAService(ETAMockProvider())
_demo_favoritos = FavoritosMockProvider()

_demo_worker = MonitoramentoWorker(
    favoritos_provider=_demo_favoritos,
    eta_service=_demo_eta,
    push_sender=_demo_push,
    deduplicador=_demo_dedup,
)


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
# US #22 — Rota de demonstração / teste do Worker de monitoramento
# ---------------------------------------------------------------------------

@router.post("/notificacoes/processar")
def processar_ciclo_notificacoes():
    """
    Executa exatamente UM ciclo do MonitoramentoWorker.

    Utiliza mocks de favoritos e ETA enquanto as US #25, #29 e #19
    não estiverem implementadas. Não cria loop infinito, não agenda
    tarefas em background.

    Retorna um resumo do ciclo: quantos favoritos foram processados,
    quantas notificações foram enviadas e o detalhe de cada item.
    """
    resultados = _demo_worker.executar_ciclo()

    itens = [
        {
            "usuario_id":   r.usuario_id,
            "numero_linha": r.numero_linha,
            "eta_minutos":  r.eta_minutos,
            "tipo_disparo": r.tipo_disparo.value if r.tipo_disparo else None,
            "enviado":      r.enviado,
            "motivo_skip":  r.motivo_skip,
        }
        for r in resultados
    ]

    return {
        "status":       "ciclo_processado",
        "processados":  len(itens),
        "enviados":     sum(1 for i in itens if i["enviado"]),
        "itens":        itens,
    }


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
