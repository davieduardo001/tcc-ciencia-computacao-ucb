"""US #115 — GET /mobilidade/planejar."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from mobilidade.main import app
from mobilidade.models.rota import Rota, RotaCelula
from mobilidade.tests.test_rota_service import LESTE, OESTE, _semear, _trajeto
from shared.database import SessionLocal

client = TestClient(app)

PREFIXO = "T115."
SEGUNDA = "2026-11-02"
DOMINGO = "2026-11-01"


def _limpar(db) -> None:
    for modelo in (RotaCelula, Rota):
        db.query(modelo).filter(
            text("numero LIKE :p").bindparams(p=f"{PREFIXO}%")
        ).delete(synchronize_session=False)
    db.commit()


@pytest.fixture
def rota_com_horarios():
    db = SessionLocal()
    _limpar(db)
    _semear(db, f"{PREFIXO}100", "IDA", _trajeto())
    db.flush()
    rota = db.query(Rota).filter(Rota.numero == f"{PREFIXO}100").one()
    rota.horarios_por_dia = {"0": ["07:00", "08:00", "09:00"], "5": ["09:00"]}
    rota.tempo_percurso_min = 40
    db.commit()
    yield
    _limpar(db)
    db.close()


@pytest.fixture
def rota_sem_horarios():
    db = SessionLocal()
    _limpar(db)
    _semear(db, f"{PREFIXO}200", "IDA", _trajeto())
    db.commit()
    yield
    _limpar(db)
    db.close()


def _planejar(**extra):
    params = {
        "origem_lat": OESTE[0],
        "origem_lng": OESTE[1],
        "destino_lat": LESTE[0],
        "destino_lng": LESTE[1],
        **extra,
    }
    return client.get("/mobilidade/planejar", params=params)


def test_sair_as_devolve_horarios_de_cada_perna(rota_com_horarios):
    resposta = _planejar(tipo="saida", horario="07:10", data=SEGUNDA)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["tipo"] == "saida"
    assert corpo["motivo"] is None
    assert corpo["estimado"] is True
    opcao = corpo["opcoes"][0]
    perna = opcao["pernas"][0]
    assert perna["numero"] == f"{PREFIXO}100"
    # Perdeu o das 07:00: o próximo é às 08:00 (a parada é a do início do traçado).
    assert perna["embarca_em"].startswith(f"{SEGUNDA}T08:")
    assert perna["espera_min"] >= 40
    assert opcao["chegada_destino"] > perna["embarca_em"]
    assert opcao["duracao_total_min"] > 0


def test_chegar_ate_devolve_a_saida_necessaria(rota_com_horarios):
    resposta = _planejar(tipo="chegada", horario="09:00", data=SEGUNDA)

    assert resposta.status_code == 200
    opcao = resposta.json()["opcoes"][0]
    assert opcao["chegada_destino"] <= f"{SEGUNDA}T09:00:00-03:00"
    assert opcao["saida_casa"] < opcao["pernas"][0]["embarca_em"] or (
        opcao["saida_casa"][:16] == opcao["pernas"][0]["embarca_em"][:16]
    )


def test_fora_do_horario_de_operacao_explica_em_vez_de_lista_vazia(rota_com_horarios):
    resposta = _planejar(tipo="saida", horario="23:30", data=SEGUNDA)

    corpo = resposta.json()
    assert corpo["opcoes"] == []
    assert corpo["motivo"] == "fora_do_horario"
    assert "neste horário" in corpo["mensagem"]


def test_dia_sem_tabela_respeita_o_dia_da_semana(rota_com_horarios):
    # Há saídas na segunda e no sábado; domingo não opera.
    resposta = _planejar(tipo="saida", horario="08:00", data=DOMINGO)

    assert resposta.json()["motivo"] == "fora_do_horario"


def test_linha_sem_tabela_de_horarios_diz_que_nao_ha_tabela(rota_sem_horarios):
    resposta = _planejar(tipo="saida", horario="08:00", data=SEGUNDA)

    corpo = resposta.json()
    assert corpo["opcoes"] == []
    assert corpo["motivo"] == "sem_tabela_de_horarios"


def test_sem_linha_para_o_trajeto_diz_que_nao_ha_opcao():
    resposta = client.get(
        "/mobilidade/planejar",
        params={
            "origem_lat": -10.0,
            "origem_lng": -40.0,
            "destino_lat": -10.1,
            "destino_lng": -40.1,
            "tipo": "saida",
            "horario": "08:00",
            "data": SEGUNDA,
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["motivo"] == "sem_opcoes"


@pytest.mark.parametrize("horario", ["8:00", "24:00", "07:60", "abc"])
def test_horario_invalido_e_recusado(horario):
    assert _planejar(tipo="saida", horario=horario).status_code == 422


def test_tipo_invalido_e_recusado():
    assert _planejar(tipo="agora", horario="08:00").status_code == 422
