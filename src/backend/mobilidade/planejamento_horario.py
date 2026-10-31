# Planejamento de viagem por horário — US #115.
#
# A US #20 responde "quais linhas, onde subir e onde descer". Esta camada
# acrescenta o TEMPO: "saia às 7h12, pegue a 0.110, baldeie às 7h48, chegue
# às 8h05" ou, ao contrário, "para chegar até 8h00 saia às 7h02".
#
# Sem motor GTFS: o espaço de busca é pequeno (a US #20 devolve poucas
# opções de uma ou duas pernas), então a camada de horário roda por cima
# delas. O horário de passagem do ônibus numa parada é ESTIMADO: saída do
# terminal (tabela do /horario, por dia da semana) + tempo de percurso
# repartido pela fração do traçado já percorrida — o mesmo princípio da
# previsão de chegada na parada (`chegada_service.passagem_prevista`).
# Feriado fica de fora: o SEMOB não traz esse dado (RN-08, nunca mistura
# dia útil com sábado/domingo).

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal

from sqlalchemy.orm import Session

from mobilidade.geometria import mais_proximo
from mobilidade.models.rota import Rota
from mobilidade.posicao_service import FUSO_SEMOB
from mobilidade.rota_service import OpcaoViagem, Perna, RotaService
from mobilidade.semob_source import horarios_do_dia

# Esperar mais que isto no ponto (ou chegar com tanta folga) não é uma
# viagem que alguém queira fazer; vira "fora do horário".
ESPERA_MAXIMA_MIN = 180.0

CAMINHADA_KMH = 5.0
MAXIMO_DE_OPCOES = 5

TipoPlano = Literal["saida", "chegada"]
MotivoSemPlano = Literal["sem_opcoes", "sem_tabela_de_horarios", "fora_do_horario"]


@dataclass(frozen=True)
class DadosPerna:
    """O que o cálculo de horário precisa saber de uma perna."""

    saidas_por_dia: dict[str, list[str]]
    percurso_min: float
    fracao_embarque: float
    fracao_desembarque: float
    caminhada_ate_embarque_min: float


@dataclass(frozen=True)
class HorarioPerna:
    embarca_em: datetime
    desembarca_em: datetime
    # Tempo parado no ponto antes do ônibus (na baldeação, é a espera
    # no ponto de troca — Cenário 3).
    espera_min: int


@dataclass(frozen=True)
class PlanoOpcao:
    saida_casa: datetime
    chegada_destino: datetime
    pernas: list[HorarioPerna]

    @property
    def duracao_total_min(self) -> int:
        return round((self.chegada_destino - self.saida_casa).total_seconds() / 60)


@dataclass(frozen=True)
class ResultadoPlano:
    opcoes: list[tuple[OpcaoViagem, PlanoOpcao]]
    motivo: MotivoSemPlano | None = None


def _minutos(minutos: float) -> timedelta:
    return timedelta(minutes=minutos)


def _hora_do_dia(dia: date, hhmm: str) -> datetime | None:
    try:
        horas, minutos = hhmm.split(":")
        return datetime(dia.year, dia.month, dia.day, int(horas), int(minutos), tzinfo=FUSO_SEMOB)
    except (ValueError, TypeError):
        return None


def _passagens(dados: DadosPerna, fracao: float, referencia: datetime) -> list[datetime]:
    """
    Instantes em que o ônibus passa num ponto do traçado (`fracao` do
    percurso), olhando o dia anterior, o do instante de referência e o
    seguinte: uma saída às 23:50 passa no meio do trajeto depois da
    meia-noite, e a primeira saída de amanhã pode ser a próxima para
    quem espera à noite.
    """
    ref = referencia.astimezone(FUSO_SEMOB)
    deslocamento = _minutos(dados.percurso_min * fracao)
    passagens: list[datetime] = []
    for dias in (-1, 0, 1):
        dia = (ref + timedelta(days=dias)).date()
        for hhmm in horarios_do_dia(dados.saidas_por_dia, dia.weekday()):
            saida = _hora_do_dia(dia, hhmm)
            if saida is not None:
                passagens.append(saida + deslocamento)
    return sorted(passagens)


def _trecho_min(dados: DadosPerna) -> float:
    return dados.percurso_min * (dados.fracao_desembarque - dados.fracao_embarque)


def planejar_saindo_as(
    pernas: list[DadosPerna], caminhada_final_min: float, partida: datetime
) -> PlanoOpcao | None:
    """Cenário 1 — "sair às X": pega o primeiro ônibus possível em cada perna."""
    horario = partida.astimezone(FUSO_SEMOB)
    atual = horario
    resultado: list[HorarioPerna] = []

    for dados in pernas:
        no_ponto = atual + _minutos(dados.caminhada_ate_embarque_min)
        embarque = next(
            (p for p in _passagens(dados, dados.fracao_embarque, no_ponto) if p >= no_ponto),
            None,
        )
        if embarque is None or (embarque - no_ponto) > _minutos(ESPERA_MAXIMA_MIN):
            return None
        desembarque = embarque + _minutos(_trecho_min(dados))
        resultado.append(
            HorarioPerna(
                embarca_em=embarque,
                desembarca_em=desembarque,
                espera_min=round((embarque - no_ponto).total_seconds() / 60),
            )
        )
        atual = desembarque

    return PlanoOpcao(
        saida_casa=horario,
        chegada_destino=atual + _minutos(caminhada_final_min),
        pernas=resultado,
    )


def planejar_chegando_ate(
    pernas: list[DadosPerna], caminhada_final_min: float, limite: datetime
) -> PlanoOpcao | None:
    """
    Cenário 2 — "chegar até X": de trás para frente, escolhe em cada perna
    o ônibus mais tardio que ainda chega a tempo; o horário de saída de
    casa é o que sobra no fim.
    """
    atual = limite.astimezone(FUSO_SEMOB) - _minutos(caminhada_final_min)
    chegada_destino_ate = limite.astimezone(FUSO_SEMOB)
    blocos: list[tuple[datetime, datetime]] = []

    for dados in reversed(pernas):
        desembarque = next(
            (
                p
                for p in reversed(_passagens(dados, dados.fracao_desembarque, atual))
                if p <= atual
            ),
            None,
        )
        if desembarque is None or (atual - desembarque) > _minutos(ESPERA_MAXIMA_MIN):
            return None
        embarque = desembarque - _minutos(_trecho_min(dados))
        blocos.insert(0, (embarque, desembarque))
        atual = embarque - _minutos(dados.caminhada_ate_embarque_min)

    horarios: list[HorarioPerna] = []
    chegada_no_ponto = atual  # saída de casa
    for dados, (embarque, desembarque) in zip(pernas, blocos):
        no_ponto = chegada_no_ponto + _minutos(dados.caminhada_ate_embarque_min)
        horarios.append(
            HorarioPerna(
                embarca_em=embarque,
                desembarca_em=desembarque,
                espera_min=max(0, round((embarque - no_ponto).total_seconds() / 60)),
            )
        )
        chegada_no_ponto = desembarque

    ultimo = blocos[-1][1]
    return PlanoOpcao(
        saida_casa=atual,
        chegada_destino=min(chegada_destino_ate, ultimo + _minutos(caminhada_final_min)),
        pernas=horarios,
    )


# ---------------------------------------------------------------------------
# Dados reais: da opção da US #20 para o que o cálculo de horário precisa
# ---------------------------------------------------------------------------


def _fracao_no_trajeto(trajeto, lat: float, lng: float) -> float | None:
    if not trajeto.comprimento_m:
        return None
    indice, _ = mais_proximo(trajeto.pontos, (lat, lng))
    if indice is None:
        return None
    return min(max(trajeto.acumulado[indice] / trajeto.comprimento_m, 0.0), 1.0)


def dados_da_perna(db: Session, rota_service: RotaService, perna: Perna) -> DadosPerna | None:
    """`None` quando falta tabela de horários, tempo de percurso ou traçado."""
    rota = (
        db.query(Rota)
        .filter(Rota.numero == perna.numero, Rota.sentido == perna.sentido)
        .one_or_none()
    )
    if rota is None or not rota.horarios_por_dia or not rota.tempo_percurso_min:
        return None

    medido = rota_service.trajeto_medido(db, perna.numero, perna.sentido)
    if medido is None:
        return None
    trajeto = medido[0]

    fracao_embarque = _fracao_no_trajeto(trajeto, perna.embarque.lat, perna.embarque.lng)
    fracao_desembarque = _fracao_no_trajeto(trajeto, perna.desembarque.lat, perna.desembarque.lng)
    if fracao_embarque is None or fracao_desembarque is None:
        return None
    if fracao_desembarque <= fracao_embarque:
        return None

    return DadosPerna(
        saidas_por_dia=rota.horarios_por_dia,
        percurso_min=float(rota.tempo_percurso_min),
        fracao_embarque=fracao_embarque,
        fracao_desembarque=fracao_desembarque,
        caminhada_ate_embarque_min=perna.embarque.caminhada_metros / 1000 / CAMINHADA_KMH * 60,
    )


def planejar(
    db: Session,
    rota_service: RotaService,
    opcoes: list[OpcaoViagem],
    tipo: TipoPlano,
    referencia: datetime,
) -> ResultadoPlano:
    """
    Aplica o horário às opções da US #20. Ordena do melhor para o pior:
    "sair às X" → chega mais cedo; "chegar até X" → sai mais tarde.

    Sem plano nenhum, diz por quê (Cenário 5), em vez de lista vazia
    muda: não há rota, não há tabela de horários, ou a tabela existe mas
    nenhum ônibus serve neste horário.
    """
    if not opcoes:
        return ResultadoPlano(opcoes=[], motivo="sem_opcoes")

    planos: list[tuple[OpcaoViagem, PlanoOpcao]] = []
    tinha_tabela = False

    for opcao in opcoes:
        dados = [dados_da_perna(db, rota_service, perna) for perna in opcao.pernas]
        if any(d is None for d in dados):
            continue
        tinha_tabela = True
        caminhada_final_min = opcao.pernas[-1].desembarque.caminhada_metros / 1000 / CAMINHADA_KMH * 60
        if tipo == "saida":
            plano = planejar_saindo_as(dados, caminhada_final_min, referencia)
        else:
            plano = planejar_chegando_ate(dados, caminhada_final_min, referencia)
        if plano is not None:
            planos.append((opcao, plano))

    if not planos:
        return ResultadoPlano(
            opcoes=[], motivo="fora_do_horario" if tinha_tabela else "sem_tabela_de_horarios"
        )

    if tipo == "saida":
        planos.sort(key=lambda par: (par[1].chegada_destino, par[0].baldeacoes))
    else:
        planos.sort(key=lambda par: (-par[1].saida_casa.timestamp(), par[0].baldeacoes))
    return ResultadoPlano(opcoes=planos[:MAXIMO_DE_OPCOES])
