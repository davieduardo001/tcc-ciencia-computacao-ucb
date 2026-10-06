import uuid
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.database import get_db
from colaboracao.dependencies import get_usuario_atual_id
from colaboracao.deduplicador import Deduplicador
from colaboracao.eta_service import ETAService
from colaboracao.monitoring_worker import MonitoramentoWorker
from colaboracao.providers.eta_mock import ETAMockProvider
from colaboracao.providers.favoritos_mock import FavoritosMockProvider
from colaboracao.push_service import PushService
from colaboracao.models import PreferenciaNotificacao, Ocorrencia, RotaFavorita
from colaboracao.schemas import (
    PreferenciaNotificacaoResponse,
    AntecedenciaInput,
    TipoNotificacaoInput,
    ToggleNotificacoesInput,
    RespostaGenerica,
    OcorrenciaInput,
    OcorrenciaResponse,
    RotaFavoritaInput,
    RotaFavoritaResponse,
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


# ---------------------------------------------------------------------------
# US #23 — Reportar Ocorrência em uma Linha
# ---------------------------------------------------------------------------


@router.post("/ocorrencias", response_model=OcorrenciaResponse, status_code=201)
def reportar_ocorrencia(
    dados: OcorrenciaInput,
    usuario_id: uuid.UUID = Depends(get_usuario_atual_id),
    db: Session = Depends(get_db),
):
    if dados.tipo not in Ocorrencia.TIPOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo inválido. Valores permitidos: {Ocorrencia.TIPOS_VALIDOS}",
        )

    uma_hora_atras = datetime.utcnow() - timedelta(hours=1)
    reportes_na_janela = (
        db.query(Ocorrencia)
        .filter(
            Ocorrencia.usuario_id == usuario_id,
            Ocorrencia.criado_em >= uma_hora_atras,
        )
        .order_by(Ocorrencia.criado_em.asc())
        .all()
    )

    if len(reportes_na_janela) >= Ocorrencia.LIMITE_REPORTES_POR_HORA:
        reset_em = reportes_na_janela[0].criado_em + timedelta(hours=1)
        raise HTTPException(
            status_code=429,
            detail={
                "detail": "limite_reportes_excedido",
                "reset_em": reset_em.isoformat(),
            },
        )

    criado_em = datetime.utcnow()
    ocorrencia = Ocorrencia(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        linha_numero=dados.linha_numero,
        tipo=dados.tipo,
        descricao=dados.descricao,
        local=dados.local,
        lat=dados.lat,
        lng=dados.lng,
        contador_confirmacoes=0,
        criado_em=criado_em,
        expira_em=Ocorrencia.calcular_expiracao(dados.tipo, criado_em),
    )
    ocorrencia.status = ocorrencia.status_inicial

    db.add(ocorrencia)
    db.commit()
    db.refresh(ocorrencia)

    return OcorrenciaResponse(
        id=str(ocorrencia.id),
        linha_numero=ocorrencia.linha_numero,
        tipo=ocorrencia.tipo,
        status=ocorrencia.status,
        contador_confirmacoes=ocorrencia.contador_confirmacoes,
        criado_em=ocorrencia.criado_em,
        expira_em=ocorrencia.expira_em,
    )


# ---------------------------------------------------------------------------
# US #25 — Salvar e Visualizar Rota Favorita
# ---------------------------------------------------------------------------


@router.post("/favoritos", response_model=RotaFavoritaResponse, status_code=201)
def salvar_favorito(
    dados: RotaFavoritaInput,
    usuario_id: uuid.UUID = Depends(get_usuario_atual_id),
    db: Session = Depends(get_db),
):
    """
    Salva uma rota calculada como favorita do usuário autenticado.

    Regras:
    - `usuario_id` vem do `X-User-Id` injetado pelo Gateway — nunca do body.
    - Máximo de 20 favoritos por usuário (LIMITE_FAVORITOS).
    - Duplicata (mesma origem+destino+linha para o mesmo usuário) retorna 409.
    """
    # Regra: máximo de 20 favoritos por usuário.
    total = (
        db.query(func.count(RotaFavorita.id))
        .filter(RotaFavorita.usuario_id == usuario_id)
        .scalar()
    )
    if total >= RotaFavorita.LIMITE_FAVORITOS:
        raise HTTPException(
            status_code=422,
            detail="limite_favoritos_atingido",
        )

    # Regra: impedir duplicata (mesma origem+destino+linha para o usuário).
    # Comparação com tolerância de 4 casas decimais (~11 metros) — suficiente
    # para detectar cliques no mesmo ponto (as coordenadas vêm do mesmo
    # geocoder e serão idênticas na prática). Buscamos todos os favoritos do
    # usuário para a mesma linha e comparamos as coordenadas no Python — o
    # volume por usuário é pequeno (máx. 20) então não há custo relevante.
    candidatos = (
        db.query(RotaFavorita)
        .filter(
            RotaFavorita.usuario_id == usuario_id,
            RotaFavorita.numero_linha == dados.numero_linha,
        )
        .all()
    )
    for c in candidatos:
        if (
            round(c.origem_lat, 4) == round(dados.origem_lat, 4)
            and round(c.origem_lng, 4) == round(dados.origem_lng, 4)
            and round(c.destino_lat, 4) == round(dados.destino_lat, 4)
            and round(c.destino_lng, 4) == round(dados.destino_lng, 4)
        ):
            raise HTTPException(
                status_code=409,
                detail="rota_ja_favoritada",
            )

    favorito = RotaFavorita(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        numero_linha=dados.numero_linha,
        nome_linha=dados.nome_linha,
        label=dados.label,
        origem_lat=dados.origem_lat,
        origem_lng=dados.origem_lng,
        destino_lat=dados.destino_lat,
        destino_lng=dados.destino_lng,
        criado_em=datetime.utcnow(),
        atualizado_em=datetime.utcnow(),
    )
    db.add(favorito)
    db.commit()
    db.refresh(favorito)

    return RotaFavoritaResponse(
        id=str(favorito.id),
        usuario_id=str(favorito.usuario_id),
        numero_linha=favorito.numero_linha,
        nome_linha=favorito.nome_linha,
        label=favorito.label,
        origem_lat=favorito.origem_lat,
        origem_lng=favorito.origem_lng,
        destino_lat=favorito.destino_lat,
        destino_lng=favorito.destino_lng,
        criado_em=favorito.criado_em,
    )


@router.get("/favoritos", response_model=list[RotaFavoritaResponse])
def listar_favoritos(
    usuario_id: uuid.UUID = Depends(get_usuario_atual_id),
    db: Session = Depends(get_db),
):
    """
    Lista todas as rotas favoritas do usuário autenticado.

    Retorna somente os registros cujo `usuario_id` corresponde ao usuário
    identificado pelo Gateway via `X-User-Id`. Nunca retorna favoritos de
    outros usuários.
    """
    favoritos = (
        db.query(RotaFavorita)
        .filter(RotaFavorita.usuario_id == usuario_id)
        .order_by(RotaFavorita.criado_em.desc())
        .all()
    )
    return [
        RotaFavoritaResponse(
            id=str(f.id),
            usuario_id=str(f.usuario_id),
            numero_linha=f.numero_linha,
            nome_linha=f.nome_linha,
            label=f.label,
            origem_lat=f.origem_lat,
            origem_lng=f.origem_lng,
            destino_lat=f.destino_lat,
            destino_lng=f.destino_lng,
            criado_em=f.criado_em,
        )
        for f in favoritos
    ]


@router.delete("/favoritos/{favorito_id}", status_code=204)
def remover_favorito(
    favorito_id: uuid.UUID,
    usuario_id: uuid.UUID = Depends(get_usuario_atual_id),
    db: Session = Depends(get_db),
):
    """
    Remove uma rota favorita do usuário autenticado.

    - 404: favorito não encontrado.
    - 403: favorito existe mas pertence a outro usuário.
    - 204: removido com sucesso (sem corpo na resposta).

    A distinção entre 403 e 404 é intencional: retornar 404 para um favorito
    alheio esconderia a regra de negócio; 403 torna explícito que o acesso
    foi negado. Seguindo a diretriz da análise técnica aprovada.
    """
    favorito = db.query(RotaFavorita).filter(RotaFavorita.id == favorito_id).first()

    if favorito is None:
        raise HTTPException(status_code=404, detail="Favorito não encontrado.")

    if favorito.usuario_id != usuario_id:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: este favorito pertence a outro usuário.",
        )

    db.delete(favorito)
    db.commit()
