# Tempo do ônibus nas paradas de subir e descer de uma rota — issue #190.
#
# O planejador monta cada trecho (perna) a partir de `Rota.paradas`, uma lista
# JSON de abrigos, e não da tabela `parada`. Este módulo faz duas coisas que
# ligam os dois mundos:
#
#  • `codigo_da_parada`: dá o `parada.codigo` do ponto de embarque/desembarque
#    de um trecho, pela proximidade com as paradas vinculadas à MESMA rota;
#  • `chegadas_das_pernas`: para cada trecho, quando o ônibus chega à parada de
#    subir e à de descer — em lote, uma leitura do feed para a rota inteira.
#
# Mesmas regras do `chegada_service` (#185): ao vivo (posição real, ao longo do
# trajeto, no sentido do trecho) → previsto (saída + tempo de percurso) →
# sem dado (`None`; RN-09, não inventa). Sem linha reta.
#
# Desembarque ao vivo é o do MESMO ônibus que o passageiro pegaria (o de menor
# ETA até a parada de subir): "daqui a quanto tempo desço" não é o ETA de
# qualquer ônibus da linha até a parada de descer. Sem ônibus a caminho, o
# previsto do desembarque é a passagem prevista no embarque + o trecho do
# tempo de percurso entre as duas paradas — nunca a passagem prevista isolada
# na parada de descer, que poderia ser a de um ônibus que o passageiro já
# perdeu.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy.orm import Session

from mobilidade.chegada_service import passagem_prevista
from mobilidade.eta_service import eta_ate_indice
from mobilidade.geometria import distancia_metros
from mobilidade.models.parada import Parada, RotaParada
from mobilidade.models.rota import Rota
from mobilidade.parada_service import RAIO_MESMA_PARADA_METROS
from mobilidade.posicao_service import FUSO_SEMOB, PosicaoService, PosicaoVeiculo
from mobilidade.rota_service import RotaService

Fonte = Literal["ao_vivo", "previsto"]

_Vinculos = list[tuple[Parada, RotaParada]]


@dataclass(frozen=True)
class PedidoDePerna:
    numero: str
    sentido: str
    embarque_codigo: str | None
    desembarque_codigo: str | None


@dataclass(frozen=True)
class ChegadaNoPonto:
    parada_codigo: str | None = None
    eta_minutos: float | None = None
    fonte: Fonte | None = None
    prefixo: str | None = None
    horario_previsto: str | None = None


@dataclass(frozen=True)
class ChegadasDaPerna:
    numero: str
    sentido: str
    embarque: ChegadaNoPonto
    desembarque: ChegadaNoPonto


# ---------------------------------------------------------------------------
# Código da parada de um ponto do trecho
# ---------------------------------------------------------------------------


def vinculos_da_rota(db: Session, numero: str, sentido: str) -> _Vinculos:
    """As paradas físicas vinculadas à rota (numero, sentido)."""
    return (
        db.query(Parada, RotaParada)
        .join(RotaParada, RotaParada.parada_id == Parada.id)
        .filter(RotaParada.numero == numero, RotaParada.sentido == sentido)
        .all()
    )


def codigo_da_parada(
    vinculos: _Vinculos,
    lat: float,
    lng: float,
    raio_m: float = RAIO_MESMA_PARADA_METROS,
) -> str | None:
    """
    `parada.codigo` da parada da rota mais próxima de (lat, lng), a até
    `raio_m` (padrão: o mesmo "é a mesma parada" do `ParadaService`, 40 m).

    `None` quando a rota não tem parada ingerida por perto — o ponto fica sem
    código e, portanto, sem tempo (RN-09). Só olha paradas DESTA rota: uma
    parada de outra linha a poucos metros não serve de embarque aqui.
    """
    melhor: tuple[float, str] | None = None
    for parada, _vinculo in vinculos:
        d = distancia_metros(lat, lng, parada.lat, parada.lng)
        if d <= raio_m and (melhor is None or d < melhor[0]):
            melhor = (d, parada.codigo)
    return melhor[1] if melhor else None


# ---------------------------------------------------------------------------
# Chegadas por trecho
# ---------------------------------------------------------------------------


def _hhmm(instante: datetime) -> str:
    return instante.astimezone(FUSO_SEMOB).strftime("%H:%M")


def _vinculo_da_parada(
    db: Session, numero: str, sentido: str, codigo: str | None
) -> RotaParada | None:
    if not codigo:
        return None
    return (
        db.query(RotaParada)
        .join(Parada, RotaParada.parada_id == Parada.id)
        .filter(
            Parada.codigo == codigo,
            RotaParada.numero == numero,
            RotaParada.sentido == sentido,
        )
        .one_or_none()
    )


def _percurso_entre(rota: Rota, de: RotaParada, ate: RotaParada, comprimento_m: float) -> timedelta | None:
    """Tempo de percurso proporcional ao trecho entre duas paradas da mesma rota."""
    if rota.tempo_percurso_min is None or not comprimento_m or comprimento_m <= 0:
        return None
    metros = ate.distancia_acumulada_m - de.distancia_acumulada_m
    if metros <= 0:
        return None
    return timedelta(minutes=rota.tempo_percurso_min * metros / comprimento_m)


def _chegada_da_perna(
    db: Session,
    pedido: PedidoDePerna,
    veiculos: list[PosicaoVeiculo],
    rota_service: RotaService,
    agora: datetime,
) -> ChegadasDaPerna:
    vazio = ChegadasDaPerna(
        numero=pedido.numero,
        sentido=pedido.sentido,
        embarque=ChegadaNoPonto(parada_codigo=pedido.embarque_codigo),
        desembarque=ChegadaNoPonto(parada_codigo=pedido.desembarque_codigo),
    )

    vinc_emb = _vinculo_da_parada(db, pedido.numero, pedido.sentido, pedido.embarque_codigo)
    vinc_des = _vinculo_da_parada(db, pedido.numero, pedido.sentido, pedido.desembarque_codigo)
    if vinc_emb is None and vinc_des is None:
        return vazio

    rota = (
        db.query(Rota)
        .filter(Rota.numero == pedido.numero, Rota.sentido == pedido.sentido)
        .one_or_none()
    )
    medido = rota_service.trajeto_medido(db, pedido.numero, pedido.sentido)
    trajeto = medido[0] if medido else None

    # Descer antes de subir (ou na mesma parada) não é uma viagem: não
    # inventa tempo de descida para um par fora de ordem.
    descida_valida = (
        vinc_emb is not None
        and vinc_des is not None
        and vinc_des.indice_trajeto > vinc_emb.indice_trajeto
    )

    # -- embarque ------------------------------------------------------
    onibus: PosicaoVeiculo | None = None
    embarque = ChegadaNoPonto(parada_codigo=pedido.embarque_codigo)
    previsto_emb: tuple[datetime, float] | None = None

    if vinc_emb is not None:
        if trajeto is not None:
            etas = [
                (eta, v)
                for v in veiculos
                if (eta := eta_ate_indice(v, trajeto, vinc_emb.indice_trajeto, pedido.sentido, agora))
                is not None
            ]
            if etas:
                eta, onibus = min(etas, key=lambda par: par[0])
                embarque = ChegadaNoPonto(
                    parada_codigo=pedido.embarque_codigo,
                    eta_minutos=round(eta, 1),
                    fonte="ao_vivo",
                    prefixo=onibus.prefixo,
                )
        if onibus is None and rota is not None:
            previsto_emb = passagem_prevista(
                rota, vinc_emb, trajeto.comprimento_m if trajeto else None, agora
            )
            if previsto_emb is not None:
                instante, minutos = previsto_emb
                embarque = ChegadaNoPonto(
                    parada_codigo=pedido.embarque_codigo,
                    eta_minutos=round(minutos, 1),
                    fonte="previsto",
                    horario_previsto=_hhmm(instante),
                )

    # -- desembarque ---------------------------------------------------
    desembarque = ChegadaNoPonto(parada_codigo=pedido.desembarque_codigo)

    if vinc_des is not None and trajeto is not None and onibus is not None and descida_valida:
        # O mesmo ônibus que o passageiro pega, até a parada de descer.
        eta_desce = eta_ate_indice(onibus, trajeto, vinc_des.indice_trajeto, pedido.sentido, agora)
        if eta_desce is not None:
            desembarque = ChegadaNoPonto(
                parada_codigo=pedido.desembarque_codigo,
                eta_minutos=round(eta_desce, 1),
                fonte="ao_vivo",
                prefixo=onibus.prefixo,
            )
    elif (
        vinc_des is not None
        and trajeto is not None
        and rota is not None
        and previsto_emb is not None
        and descida_valida
    ):
        percurso = _percurso_entre(rota, vinc_emb, vinc_des, trajeto.comprimento_m)
        if percurso is not None:
            instante = previsto_emb[0] + percurso
            minutos = (instante - agora.astimezone(FUSO_SEMOB)).total_seconds() / 60
            desembarque = ChegadaNoPonto(
                parada_codigo=pedido.desembarque_codigo,
                eta_minutos=round(minutos, 1),
                fonte="previsto",
                horario_previsto=_hhmm(instante),
            )

    return ChegadasDaPerna(
        numero=pedido.numero, sentido=pedido.sentido, embarque=embarque, desembarque=desembarque
    )


async def chegadas_das_pernas(
    db: Session,
    pedidos: list[PedidoDePerna],
    posicao_service: PosicaoService,
    rota_service: RotaService,
    agora: datetime | None = None,
) -> list[ChegadasDaPerna]:
    """
    Chegadas de cada trecho, na ordem pedida. Uma leitura do feed para todas
    as linhas (o `PosicaoService` já cacheia 20 s).
    """
    agora = agora or datetime.now(timezone.utc)
    posicoes = await posicao_service.posicoes_das_linhas({p.numero for p in pedidos})
    return [
        _chegada_da_perna(db, pedido, posicoes.get(pedido.numero, []), rota_service, agora)
        for pedido in pedidos
    ]
