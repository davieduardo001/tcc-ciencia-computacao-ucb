import uuid
import logging
from datetime import datetime, timedelta

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from shared.database import get_db
from colaboracao.dependencies import get_usuario_atual_id
from colaboracao.deduplicador import Deduplicador
from colaboracao.eta_service import ETAService
from colaboracao.monitoring_worker import MonitoramentoWorker
from colaboracao.providers.eta_mock import ETAMockProvider
from colaboracao.providers.favoritos_mock import FavoritosMockProvider
from colaboracao.push_service import PushService
from colaboracao.models import PreferenciaNotificacao, Ocorrencia, RotaFavorita, ConfirmacaoOcorrencia
from colaboracao.schemas import (
    PreferenciaNotificacaoResponse,
    AntecedenciaInput,
    TipoNotificacaoInput,
    ToggleNotificacoesInput,
    RespostaGenerica,
    OcorrenciaInput,
    OcorrenciaResponse,
    OcorrenciaListaResponse,
    RotaFavoritaInput,
    RotaFavoritaResponse,
    ConfirmacaoOcorrenciaResponse,
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

def _usuario_dono_das_preferencias(
    usuario_id: uuid.UUID,
    usuario_autenticado: uuid.UUID = Depends(get_usuario_atual_id),
) -> uuid.UUID:
    """
    O `usuario_id` da URL precisa ser o do usuário autenticado (X-User-Id,
    injetado pelo Gateway). Impede ler ou alterar preferências alheias.
    """
    if usuario_id != usuario_autenticado:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: as preferências pertencem a outro usuário.",
        )
    return usuario_id


def _obter_ou_criar_preferencias(usuario_id, db: Session) -> PreferenciaNotificacao:
    preferencia = (
        db.query(PreferenciaNotificacao)
        .filter(PreferenciaNotificacao.usuario_id == usuario_id)
        .first()
    )
    if not preferencia:
        preferencia = PreferenciaNotificacao(
            id=uuid.uuid4(),
            usuario_id=usuario_id,
            antecedencia_minutos=30,
            notificacoes_ativas=True,
            alerta_chegada=True,
            alerta_cancelamento=True,
            criado_em=datetime.utcnow(),
            atualizado_em=datetime.utcnow(),
        )
        db.add(preferencia)
        try:
            db.commit()
        except IntegrityError:
            # A FK para usuarios.id existe só no banco (migration), não no
            # ORM: um usuario_id sem registro em usuarios viola a constraint
            # no commit e vira 404 em vez de 500.
            db.rollback()
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        db.refresh(preferencia)
    return preferencia


@router.get("/preferencias/{usuario_id}", response_model=PreferenciaNotificacaoResponse)
def carregar_preferencias(
    usuario_id: uuid.UUID = Depends(_usuario_dono_das_preferencias),
    db: Session = Depends(get_db),
):
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
def salvar_antecedencia(
    dados: AntecedenciaInput,
    usuario_id: uuid.UUID = Depends(_usuario_dono_das_preferencias),
    db: Session = Depends(get_db),
):
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
def atualizar_tipo_notificacao(
    tipo: str,
    dados: TipoNotificacaoInput,
    usuario_id: uuid.UUID = Depends(_usuario_dono_das_preferencias),
    db: Session = Depends(get_db),
):
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
def desativar_todas_notificacoes(
    dados: ToggleNotificacoesInput,
    usuario_id: uuid.UUID = Depends(_usuario_dono_das_preferencias),
    db: Session = Depends(get_db),
):
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
# US #24 — Visualizar Ocorrências Reportadas por Outros Passageiros
# ---------------------------------------------------------------------------

LIMITE_LISTAGEM_OCORRENCIAS = 100


@router.get("/ocorrencias", response_model=list[OcorrenciaListaResponse])
def listar_ocorrencias(
    linha: Optional[str] = Query(None, min_length=1, max_length=20),
    _usuario_id: uuid.UUID = Depends(get_usuario_atual_id),
    db: Session = Depends(get_db),
):
    """Ocorrências ativas (não expiradas), da mais recente pra mais antiga.

    Exige sessão (o Gateway já validou o JWT) mas não filtra por usuário —
    a ideia é justamente ver o que *outros* passageiros reportaram.

    Expiração resolvida na leitura, não por job agendado: os serviços do
    Fly escalam a zero (`min_machines_running = 0`), então um job em
    processo não rodaria de forma confiável. Quem passou de `expira_em`
    nunca aparece e é marcado `expirada` aqui mesmo (o registro não é
    apagado — a retenção é de 30 dias).
    """
    agora = datetime.utcnow()

    db.query(Ocorrencia).filter(
        Ocorrencia.expira_em <= agora,
        Ocorrencia.status != "expirada",
    ).update({"status": "expirada"}, synchronize_session=False)
    db.commit()

    consulta = db.query(Ocorrencia).filter(
        Ocorrencia.expira_em > agora,
        Ocorrencia.status != "expirada",
    )
    if linha:
        consulta = consulta.filter(Ocorrencia.linha_numero == linha)

    ocorrencias = (
        consulta.order_by(Ocorrencia.criado_em.desc())
        .limit(LIMITE_LISTAGEM_OCORRENCIAS)
        .all()
    )

    return [
        OcorrenciaListaResponse(
            id=str(o.id),
            linha_numero=o.linha_numero,
            tipo=o.tipo,
            descricao=o.descricao,
            local=o.local,
            lat=o.lat,
            lng=o.lng,
            status=o.status,
            contador_confirmacoes=o.contador_confirmacoes,
            criado_em=o.criado_em,
            expira_em=o.expira_em,
            eh_autor=(o.usuario_id == _usuario_id),
        )
        for o in ocorrencias
    ]


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


# ---------------------------------------------------------------------------
# US #26 — Confirmar Ocorrência Reportada por Outro Passageiro
# ---------------------------------------------------------------------------


@router.post(
    "/ocorrencias/{ocorrencia_id}/confirmar",
    response_model=ConfirmacaoOcorrenciaResponse,
    status_code=200,
)
def confirmar_ocorrencia(
    ocorrencia_id: uuid.UUID,
    usuario_id: uuid.UUID = Depends(get_usuario_atual_id),
    db: Session = Depends(get_db),
):
    """
    Confirma uma ocorrência reportada por outro passageiro (US #26).

    Regras:
    - Requer autenticação (X-User-Id validado pelo Gateway).
    - O autor original não pode confirmar a própria ocorrência (403).
    - Cada usuário confirma uma ocorrência no máximo uma vez (409).
      A UNIQUE constraint do banco garante isso mesmo sob concorrência.
    - Ocorrências inexistentes retornam 404.
    - Ocorrências expiradas ou inativas retornam 422.
    - Ao atingir Ocorrencia.LIMITE_CONFIRMACOES (3), o status muda para
      "confirmada". A transição é atômica (mesma transação do INSERT).

    O caminho externo é:
      POST /api/colaboracao/ocorrencias/{ocorrencia_id}/confirmar
    (o Gateway proxy /colaboracao/* já encaminha com X-User-Id injetado)
    """
    agora = datetime.utcnow()

    # 1. Verifica existência.
    ocorrencia = db.query(Ocorrencia).filter(Ocorrencia.id == ocorrencia_id).first()
    if ocorrencia is None:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada.")

    # 2. Verifica se ainda está ativa.
    if ocorrencia.status == "expirada" or ocorrencia.expira_em <= agora:
        raise HTTPException(
            status_code=422,
            detail="ocorrencia_inativa",
        )

    # 3. Impede que o autor confirme a própria ocorrência.
    if ocorrencia.usuario_id == usuario_id:
        raise HTTPException(
            status_code=403,
            detail="autor_nao_pode_confirmar",
        )

    # 4. Tenta inserir a confirmação. A UNIQUE constraint (ocorrencia_id,
    #    usuario_id) garante que confirmações duplicadas — mesmo concorrentes
    #    — sejam rejeitadas pelo banco antes de qualquer incremento.
    confirmacao = ConfirmacaoOcorrencia(
        id=uuid.uuid4(),
        ocorrencia_id=ocorrencia_id,
        usuario_id=usuario_id,
        criado_em=agora,
    )
    db.add(confirmacao)

    try:
        db.flush()  # dispara a constraint sem commitar — detecta duplicata cedo
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="confirmacao_duplicada",
        )

    # 5. Incrementa o contador direto no banco (UPDATE ... SET c = c + 1), sem
    #    ler-e-somar em Python: duas confirmações simultâneas de usuários
    #    diferentes não perdem incremento, porque o UPDATE trava a linha.
    #    O valor novo é relido na mesma transação e capturado em variáveis
    #    Python antes do commit (StaticPool do SQLite desvincula instâncias
    #    após commit).
    filtro = Ocorrencia.id == ocorrencia_id
    db.query(Ocorrencia).filter(filtro).update(
        {Ocorrencia.contador_confirmacoes: Ocorrencia.contador_confirmacoes + 1},
        synchronize_session=False,
    )
    novo_contador = db.query(Ocorrencia.contador_confirmacoes).filter(filtro).scalar()
    novo_status = ocorrencia.status
    if novo_contador >= Ocorrencia.LIMITE_CONFIRMACOES:
        novo_status = "confirmada"
        db.query(Ocorrencia).filter(filtro).update(
            {Ocorrencia.status: novo_status}, synchronize_session=False
        )
    ocorrencia_id_str = str(ocorrencia_id)

    db.commit()

    return ConfirmacaoOcorrenciaResponse(
        ocorrencia_id=ocorrencia_id_str,
        status=novo_status,
        contador_confirmacoes=novo_contador,
        mensagem=(
            "Ocorrência confirmada pela comunidade."
            if novo_status == "confirmada"
            else "Confirmação registrada."
        ),
    )
