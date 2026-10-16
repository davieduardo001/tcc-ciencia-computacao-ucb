# Rotas da US #171 — Pegar o ônibus.
#
#   POST /viagens                  embarca (valida por proximidade, RN-16)
#   PUT  /viagens/{id}/destino     escolhe/troca/remove a parada de destino
#   POST /viagens/{id}/encerrar    desce / "Cheguei" (idempotente)
#   GET  /viagens/ativa            estado + progresso ao vivo (+ aviso de
#                                  proximidade pendente, US #172)
#   POST /viagens/{id}/alerta-proximidade/visto
#                                  o app confirma que mostrou o aviso (#172)
#
# Fica em arquivo próprio para não crescer o routes.py. O PosicaoService é o
# MESMO do routes.py (um por processo: o cache do feed é compartilhado), por
# isso é buscado lá, na hora do uso, e não instanciado aqui.

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from mobilidade import alerta_proximidade_entrega as entrega_alerta
from mobilidade import routes as _base
from mobilidade import viagem_service as servico
from mobilidade.dependencies import get_usuario_atual_id
from mobilidade.models.viagem import Viagem
from mobilidade.schemas_viagem import (
    AlertaProximidadeResponse,
    DestinoRequest,
    DestinoViagemResponse,
    EmbarqueRequest,
    ParadaViagemResponse,
    VeiculoViagemResponse,
    ViagemAtivaResponse,
    ViagemResponse,
)
from shared.database import get_db

router = APIRouter()

MENSAGEM_SEM_VEICULO = (
    "Não conseguimos confirmar seu embarque: nenhum ônibus desta linha está "
    "perto de você agora. Tente de novo quando o ônibus estiver na parada."
)


def _viagem_response(viagem: Viagem) -> ViagemResponse:
    return ViagemResponse(
        id=str(viagem.id),
        numero_linha=viagem.numero_linha,
        sentido=viagem.sentido,
        veiculo_prefixo=viagem.veiculo_prefixo,
        parada_destino_codigo=viagem.parada_destino_codigo,
        embarcou_em=viagem.embarcou_em,
        encerrada_em=viagem.encerrada_em,
        motivo_encerramento=viagem.motivo_encerramento,
    )


@router.post("/viagens", response_model=ViagemResponse, status_code=201)
async def pegar_onibus(
    corpo: EmbarqueRequest,
    usuario_id: uuid.UUID = Depends(get_usuario_atual_id),
    db: Session = Depends(get_db),
):
    """
    Cenário 1 — veículo da linha perto: registra a viagem (201).
    Cenário 4 — nenhum veículo perto: 422, sem registrar nada.
    Já em viagem: 409 (a atual não muda).

    A latitude/longitude do corpo só confirma o embarque; não é gravada.
    """
    veiculos = await _base._posicao_service.posicoes_da_linha(corpo.numero_linha)
    try:
        viagem = servico.embarcar(
            db,
            usuario_id=usuario_id,
            numero_linha=corpo.numero_linha,
            lat=corpo.lat,
            lng=corpo.lng,
            parada_destino_codigo=corpo.parada_destino_codigo,
            veiculos=veiculos,
            agora=servico.agora_utc(),
        )
    except servico.JaEmViagem:
        raise HTTPException(status_code=409, detail="Você já está em uma viagem.")
    except servico.SemVeiculoProximo:
        raise HTTPException(status_code=422, detail=MENSAGEM_SEM_VEICULO)
    except servico.ParadaDesconhecida:
        raise HTTPException(status_code=422, detail="Parada de destino não encontrada.")
    except servico.ParadaForaDaLinha:
        raise HTTPException(
            status_code=422, detail="A parada de destino não faz parte desta linha."
        )

    return _viagem_response(viagem)


@router.put("/viagens/{viagem_id}/destino", response_model=ViagemResponse)
def definir_destino_da_viagem(
    viagem_id: uuid.UUID,
    corpo: DestinoRequest,
    usuario_id: uuid.UUID = Depends(get_usuario_atual_id),
    db: Session = Depends(get_db),
):
    """
    Escolhe, troca ou remove (`null`) a parada de destino da viagem ativa.
    404 para viagem inexistente ou de outro usuário; 409 se já terminou;
    422 para parada desconhecida ou que não é da linha.
    """
    try:
        viagem = servico.definir_destino(
            db,
            usuario_id=usuario_id,
            viagem_id=viagem_id,
            parada_destino_codigo=corpo.parada_destino_codigo,
            agora=servico.agora_utc(),
        )
    except servico.ViagemJaEncerrada:
        raise HTTPException(status_code=409, detail="Esta viagem já foi encerrada.")
    except servico.ParadaDesconhecida:
        raise HTTPException(status_code=422, detail="Parada de destino não encontrada.")
    except servico.ParadaForaDaLinha:
        raise HTTPException(
            status_code=422, detail="A parada de destino não faz parte desta linha."
        )

    if viagem is None:
        raise HTTPException(status_code=404, detail="Viagem não encontrada.")
    return _viagem_response(viagem)


@router.post("/viagens/{viagem_id}/encerrar", response_model=ViagemResponse)
def encerrar_viagem(
    viagem_id: uuid.UUID,
    usuario_id: uuid.UUID = Depends(get_usuario_atual_id),
    db: Session = Depends(get_db),
):
    """
    Cenário 3 — "Cheguei". Idempotente. 404 tanto para viagem inexistente
    quanto para a de outro usuário: não revela que o id existe.
    """
    viagem = servico.encerrar(
        db, usuario_id=usuario_id, viagem_id=viagem_id, agora=servico.agora_utc()
    )
    if viagem is None:
        raise HTTPException(status_code=404, detail="Viagem não encontrada.")
    return _viagem_response(viagem)


@router.post("/viagens/{viagem_id}/alerta-proximidade/visto", status_code=204)
def alerta_de_proximidade_visto(
    viagem_id: uuid.UUID,
    usuario_id: uuid.UUID = Depends(get_usuario_atual_id),
    db: Session = Depends(get_db),
):
    """
    US #172 — o app mostrou o aviso de proximidade e a pessoa o dispensou:
    ele não volta nas próximas consultas.

    Sempre 204 e idempotente. Só mexe nos alertas do próprio usuário, então
    uma viagem alheia (ou inexistente) não muda nada nem revela que existe.
    """
    entrega_alerta.marcar_como_visto(db, usuario_id, viagem_id)
    return Response(status_code=204)


@router.get("/viagens/ativa", response_model=ViagemAtivaResponse)
async def viagem_em_andamento(
    usuario_id: uuid.UUID = Depends(get_usuario_atual_id),
    db: Session = Depends(get_db),
):
    """
    Cenário 2 — em viagem: veículo, próxima parada e paradas restantes até
    o destino. Sem viagem: `{ "ativa": false }` (200, não 404 — "não estar
    em viagem" é o estado normal, não um erro).
    """
    viagem = servico.viagem_ativa(db, usuario_id, servico.agora_utc())
    if viagem is None:
        return ViagemAtivaResponse(ativa=False)

    veiculos = await _base._posicao_service.posicoes_da_linha(viagem.numero_linha)
    progresso = servico.progresso_da_viagem(
        db, viagem, veiculos, _base._rota_service, datetime.now(timezone.utc)
    )

    def _parada(p) -> ParadaViagemResponse:
        return ParadaViagemResponse(codigo=p.codigo, nome=p.nome, lat=p.lat, lng=p.lng)

    alerta = entrega_alerta.alerta_pendente(db, usuario_id, viagem.id, servico.agora_utc())

    return ViagemAtivaResponse(
        ativa=True,
        alerta_proximidade=(
            AlertaProximidadeResponse(
                id=str(alerta.id),
                parada_codigo=alerta.parada_destino_codigo,
                parada_nome=alerta.parada_destino_nome,
                eta_minutos=alerta.eta_minutos,
                disparado_em=alerta.disparado_em,
            )
            if alerta
            else None
        ),
        viagem=_viagem_response(viagem),
        sinal=progresso.sinal,
        veiculo=(
            VeiculoViagemResponse(
                prefixo=progresso.veiculo.prefixo,
                lat=progresso.veiculo.lat,
                lng=progresso.veiculo.lng,
                direcao=progresso.veiculo.direcao,
                atualizado_em=progresso.veiculo.atualizado_em.isoformat(),
            )
            if progresso.veiculo
            else None
        ),
        destino=(
            DestinoViagemResponse(
                **_parada(progresso.destino.parada).model_dump(),
                ultrapassado=progresso.destino.ultrapassado,
            )
            if progresso.destino
            else None
        ),
        proxima_parada=_parada(progresso.proxima_parada) if progresso.proxima_parada else None,
        paradas_restantes=[_parada(p) for p in progresso.paradas_restantes],
    )
