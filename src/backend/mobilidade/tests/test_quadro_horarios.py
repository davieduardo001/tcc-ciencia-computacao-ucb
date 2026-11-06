"""US #118 — quadro de horários da linha."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from mobilidade.main import app
from mobilidade.models.linha import Linha
from mobilidade.models.rota import Rota
from mobilidade.posicao_service import FUSO_SEMOB
from mobilidade.quadro_horarios import montar_quadro
from shared.database import SessionLocal

UTIL = ["05:00", "12:00", "20:00"]
POR_DIA = {
    **{str(d): UTIL for d in range(5)},
    "5": ["07:00", "13:00"],
    # domingo sem partidas
}


def _rota(por_dia=POR_DIA, percurso=60):
    return Rota(horarios_por_dia=por_dia, tempo_percurso_min=percurso)


def _agora(dia: int, hhmm: str) -> datetime:
    # 2026-11-02 é segunda-feira.
    h, m = hhmm.split(":")
    return datetime(2026, 11, 2 + dia, int(h), int(m), tzinfo=FUSO_SEMOB)


def test_agrupa_dia_util_e_sabado_e_marca_o_de_hoje():
    quadro = montar_quadro(_rota(), _agora(1, "10:00"))

    assert [g.rotulo for g in quadro.grupos] == ["Segunda a sexta", "Sábado"]
    assert [g.hoje for g in quadro.grupos] == [True, False]
    assert quadro.grupos[0].horarios == UTIL
    assert quadro.tempo_percurso_min == 60


def test_proxima_partida_considera_o_dia_atual():
    util = montar_quadro(_rota(), _agora(1, "10:00")).proxima_partida
    sabado = montar_quadro(_rota(), _agora(5, "08:00")).proxima_partida

    assert (util.horario, util.quando, util.em_minutos) == ("12:00", "hoje", 120)
    assert (sabado.horario, sabado.quando) == ("13:00", "hoje")


def test_operando_ate_a_ultima_viagem_terminar():
    # Última saída 20:00 + 60 min de percurso.
    assert montar_quadro(_rota(), _agora(1, "20:30")).estado == "operando"
    assert montar_quadro(_rota(), _agora(1, "21:01")).estado == "fora_do_horario"


def test_fora_do_horario_aponta_a_proxima_partida_de_amanha():
    quadro = montar_quadro(_rota(), _agora(1, "23:00"))

    assert quadro.estado == "fora_do_horario"
    assert (quadro.proxima_partida.horario, quadro.proxima_partida.quando) == ("05:00", "amanhã")


def test_antes_da_primeira_saida_tambem_e_fora_do_horario():
    quadro = montar_quadro(_rota(), _agora(1, "03:00"))

    assert quadro.estado == "fora_do_horario"
    assert quadro.proxima_partida.quando == "hoje"


def test_domingo_sem_partida_diz_que_nao_opera_hoje():
    quadro = montar_quadro(_rota(), _agora(6, "10:00"))

    assert quadro.estado == "nao_opera_hoje"
    assert (quadro.proxima_partida.horario, quadro.proxima_partida.quando) == ("05:00", "amanhã")


@pytest.mark.parametrize("rota", [None, Rota(horarios_por_dia=None), Rota(horarios_por_dia={})])
def test_sem_horario_publicado(rota):
    quadro = montar_quadro(rota, _agora(0, "10:00"))

    assert quadro.estado == "sem_horario"
    assert quadro.grupos == []
    assert quadro.proxima_partida is None


def test_rotulo_de_dias_avulsos():
    por_dia = {"2": ["06:00"], "3": ["06:00"]}

    assert montar_quadro(_rota(por_dia), _agora(0, "10:00")).grupos[0].rotulo == "Quarta e quinta"


# --- rota HTTP ---------------------------------------------------------------

client = TestClient(app)
NUMERO = "T118.001"


def _limpar(db):
    db.query(Rota).filter(Rota.numero == NUMERO).delete()
    db.query(Linha).filter(Linha.numero == NUMERO).delete()
    db.commit()


def _linha(db, horarios_previstos):
    db.add(
        Linha(
            numero=NUMERO, nome="Teste 118", sentido="A → B", paradas=[],
            trajeto=[[-15.8, -48.1], [-15.81, -48.1]], horarios_previstos=horarios_previstos,
        )
    )


@pytest.fixture
def db():
    sessao = SessionLocal()
    _limpar(sessao)
    yield sessao
    _limpar(sessao)
    sessao.close()


def test_rota_http_traz_o_quadro_de_horarios(db):
    _linha(db, ["05:00"])
    db.add(
        Rota(
            numero=NUMERO, sentido="IDA", nome="Teste 118", trajeto=[], paradas=[],
            horarios_por_dia={str(d): ["05:00", "18:00"] for d in range(7)},
            tempo_percurso_min=45,
        )
    )
    db.commit()

    quadro = client.get(f"/mobilidade/linhas/{NUMERO}").json()["quadro_horarios"]

    assert quadro["tempo_percurso_min"] == 45
    assert quadro["grupos"][0]["rotulo"] == "Segunda a domingo"
    assert quadro["estado"] in {"operando", "fora_do_horario"}


def test_rota_http_linha_sem_rota_ingerida_nao_tem_horario(db):
    _linha(db, [])
    db.commit()

    quadro = client.get(f"/mobilidade/linhas/{NUMERO}").json()["quadro_horarios"]

    assert quadro["estado"] == "sem_horario"
