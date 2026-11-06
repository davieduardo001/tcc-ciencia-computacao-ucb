# Quadro de horários da linha — US #118.
#
# Só EXIBE o horário publicado pelo SEMOB (`rota.horarios_por_dia`, guardado
# pela ingestão da US #173): não roteia sobre ele (isso é a #115). Reaproveita
# o que já está no banco, então não exige nova ingestão nem migration.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal

from mobilidade.models.rota import Rota
from mobilidade.semob_source import horarios_do_dia

NOMES_DOS_DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]

Estado = Literal["operando", "fora_do_horario", "nao_opera_hoje", "sem_horario"]


@dataclass(frozen=True)
class GrupoDeDias:
    rotulo: str
    dias: list[int]
    horarios: list[str]
    hoje: bool


@dataclass(frozen=True)
class ProximaPartida:
    horario: str
    # "hoje", "amanhã" ou o nome do dia ("segunda", "sábado"...).
    quando: str
    em_minutos: int


@dataclass(frozen=True)
class QuadroDeHorarios:
    estado: Estado
    tempo_percurso_min: int | None = None
    proxima_partida: ProximaPartida | None = None
    grupos: list[GrupoDeDias] = field(default_factory=list)


def _rotulo(dias: list[int]) -> str:
    """'Segunda a sexta', 'Sábado', 'Quarta e quinta'..."""
    if len(dias) == 1:
        nome = NOMES_DOS_DIAS[dias[0]]
    elif len(dias) > 2 and dias == list(range(dias[0], dias[-1] + 1)):
        nome = f"{NOMES_DOS_DIAS[dias[0]]} a {NOMES_DOS_DIAS[dias[-1]]}"
    else:
        nomes = [NOMES_DOS_DIAS[d] for d in dias]
        nome = ", ".join(nomes[:-1]) + f" e {nomes[-1]}"
    return nome[0].upper() + nome[1:]


def _agrupar(por_dia: dict[str, list[str]], hoje: int) -> list[GrupoDeDias]:
    """Dias com a mesma tabela viram um quadro só (seg-sex costuma ser um)."""
    por_tabela: dict[tuple[str, ...], list[int]] = {}
    for dia in range(7):
        horarios = horarios_do_dia(por_dia, dia)
        if horarios:
            por_tabela.setdefault(tuple(horarios), []).append(dia)
    grupos = [
        GrupoDeDias(_rotulo(dias), dias, list(horarios), hoje in dias)
        for horarios, dias in por_tabela.items()
    ]
    return sorted(grupos, key=lambda g: g.dias[0])


def _minutos(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def montar_quadro(rota: Rota | None, agora: datetime) -> QuadroDeHorarios:
    """
    `agora` deve estar no fuso do SEMOB (a tabela é em horário de Brasília).

    - operando: há partida hoje e a linha ainda circula (até a última saída
      + o tempo de percurso);
    - fora_do_horario: opera hoje, mas é antes da primeira ou depois da
      última viagem;
    - nao_opera_hoje: nenhuma partida hoje (ex: linha só de dia útil num
      domingo);
    - sem_horario: o SEMOB não publicou tabela para a linha.
    """
    if rota is None or not rota.horarios_por_dia:
        return QuadroDeHorarios(estado="sem_horario")

    por_dia = rota.horarios_por_dia
    grupos = _agrupar(por_dia, agora.weekday())
    if not grupos:
        return QuadroDeHorarios(estado="sem_horario")

    percurso = rota.tempo_percurso_min
    hoje = horarios_do_dia(por_dia, agora.weekday())
    minuto_atual = agora.hour * 60 + agora.minute

    estado: Estado = "nao_opera_hoje"
    if hoje:
        fim = _minutos(hoje[-1]) + (percurso or 0)
        operando = _minutos(hoje[0]) <= minuto_atual <= fim
        estado = "operando" if operando else "fora_do_horario"

    return QuadroDeHorarios(
        estado=estado,
        tempo_percurso_min=percurso,
        proxima_partida=_proxima(por_dia, agora),
        grupos=grupos,
    )


def _proxima(por_dia: dict[str, list[str]], agora: datetime) -> ProximaPartida | None:
    """Próxima saída a partir de agora, hoje ou no primeiro dia que tiver."""
    base = agora.replace(second=0, microsecond=0)
    for deslocamento in range(8):
        dia = base + timedelta(days=deslocamento)
        for hhmm in horarios_do_dia(por_dia, dia.weekday()):
            saida = dia.replace(hour=_minutos(hhmm) // 60, minute=_minutos(hhmm) % 60)
            if saida < base:
                continue
            if deslocamento == 0:
                quando = "hoje"
            elif deslocamento == 1:
                quando = "amanhã"
            else:
                quando = NOMES_DOS_DIAS[dia.weekday()]
            return ProximaPartida(
                horario=hhmm,
                quando=quando,
                em_minutos=int((saida - base).total_seconds() // 60),
            )
    return None
