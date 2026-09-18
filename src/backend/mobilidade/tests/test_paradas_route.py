import pytest
from fastapi.testclient import TestClient

from mobilidade.main import app
from mobilidade.models.linha import Linha
from shared.database import SessionLocal

client = TestClient(app)

# Mesmo abrigo físico (mesmíssima coordenada), servido por duas linhas —
# é o caso central da US #18: "quais linhas passam por aqui".
PARADA_LAT = -15.7998
PARADA_LNG = -47.8919

LINHA_A = "9.980"
LINHA_B = "9.981"
LINHA_SEM_HORARIO = "9.982"


@pytest.fixture
def parada_com_duas_linhas():
    db = SessionLocal()
    db.query(Linha).filter(Linha.numero.in_([LINHA_A, LINHA_B])).delete(
        synchronize_session=False
    )
    db.add(
        Linha(
            numero=LINHA_A,
            nome="9.980 — Teste A",
            sentido="Circular",
            paradas=[{"nome": "Parada Teste US18", "lat": PARADA_LAT, "lng": PARADA_LNG}],
            trajeto=[[PARADA_LAT, PARADA_LNG]],
            horarios_previstos=["06:00", "12:00"],
        )
    )
    db.add(
        Linha(
            numero=LINHA_B,
            nome="9.981 — Teste B",
            sentido="Circular",
            paradas=[{"nome": "Parada Teste US18", "lat": PARADA_LAT, "lng": PARADA_LNG}],
            trajeto=[[PARADA_LAT, PARADA_LNG]],
            horarios_previstos=["07:30"],
        )
    )
    db.commit()
    db.close()
    yield
    db2 = SessionLocal()
    db2.query(Linha).filter(Linha.numero.in_([LINHA_A, LINHA_B])).delete(
        synchronize_session=False
    )
    db2.commit()
    db2.close()


@pytest.fixture
def parada_sem_horario():
    db = SessionLocal()
    db.query(Linha).filter(Linha.numero == LINHA_SEM_HORARIO).delete(
        synchronize_session=False
    )
    db.add(
        Linha(
            numero=LINHA_SEM_HORARIO,
            nome="9.982 — Sem horário",
            sentido="Circular",
            paradas=[{"nome": "Parada Sem Horário", "lat": -15.75, "lng": -47.85}],
            trajeto=[[-15.75, -47.85]],
            horarios_previstos=[],
        )
    )
    db.commit()
    db.close()
    yield
    db2 = SessionLocal()
    db2.query(Linha).filter(Linha.numero == LINHA_SEM_HORARIO).delete(
        synchronize_session=False
    )
    db2.commit()
    db2.close()


def test_obter_parada_lista_as_linhas_que_passam_por_ela(parada_com_duas_linhas):
    response = client.get(
        "/mobilidade/paradas", params={"lat": PARADA_LAT, "lng": PARADA_LNG}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Parada Teste US18"
    assert data["codigo"]
    numeros = {l["numero"] for l in data["linhas"]}
    assert numeros == {LINHA_A, LINHA_B}


def test_obter_parada_traz_ate_tres_horarios(parada_com_duas_linhas):
    response = client.get(
        "/mobilidade/paradas", params={"lat": PARADA_LAT, "lng": PARADA_LNG}
    )

    assert response.status_code == 200
    horarios = response.json()["proximos_horarios"]
    assert len(horarios) <= 3
    assert set(horarios).issubset({"06:00", "07:30", "12:00"})


def test_obter_parada_mesma_coordenada_gera_o_mesmo_codigo(parada_com_duas_linhas):
    primeira = client.get(
        "/mobilidade/paradas", params={"lat": PARADA_LAT, "lng": PARADA_LNG}
    )
    segunda = client.get(
        "/mobilidade/paradas", params={"lat": PARADA_LAT, "lng": PARADA_LNG}
    )

    assert primeira.json()["codigo"] == segunda.json()["codigo"]


def test_obter_parada_sem_horario_previsto_retorna_lista_vazia(parada_sem_horario):
    # Cenário 2: tratamento para paradas sem informações de horário — o
    # front decide o que exibir, mas a API não pode inventar horário.
    response = client.get("/mobilidade/paradas", params={"lat": -15.75, "lng": -47.85})

    assert response.status_code == 200
    assert response.json()["proximos_horarios"] == []


def test_obter_parada_nao_encontrada():
    # Bem longe de qualquer parada cacheada no banco de teste.
    response = client.get("/mobilidade/paradas", params={"lat": 1.0, "lng": 1.0})

    assert response.status_code == 404
    assert response.json()["detail"] == "Parada não encontrada."
