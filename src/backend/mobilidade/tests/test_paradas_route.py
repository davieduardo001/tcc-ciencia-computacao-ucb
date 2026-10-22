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


# ---------------------------------------------------------------------------
# US #173 — parada resolvida pela tabela `parada` (identidade única)
# ---------------------------------------------------------------------------

from datetime import datetime  # noqa: E402

from mobilidade.models.parada import Parada, RotaParada  # noqa: E402
from mobilidade.models.rota import Rota  # noqa: E402
from mobilidade.posicao_service import FUSO_SEMOB  # noqa: E402

FISICA_LAT = -15.8100
FISICA_LNG = -47.9100
LINHA_X = "9.970"
LINHA_Y = "9.971"


@pytest.fixture
def parada_fisica():
    db = SessionLocal()

    def limpar(s):
        s.query(RotaParada).filter(RotaParada.numero.in_([LINHA_X, LINHA_Y])).delete(
            synchronize_session=False
        )
        s.query(Parada).filter(Parada.codigo == "PR-99999").delete(synchronize_session=False)
        s.query(Rota).filter(Rota.numero.in_([LINHA_X, LINHA_Y])).delete(
            synchronize_session=False
        )
        s.commit()

    limpar(db)
    parada = Parada(codigo="PR-99999", nome="Parada Física Teste", lat=FISICA_LAT, lng=FISICA_LNG)
    db.add(parada)
    db.flush()

    pontas = [
        {"nome": "Terminal X", "lat": -15.80, "lng": -47.90},
        {"nome": "Destino X", "lat": -15.82, "lng": -47.92},
    ]
    # Linha X: ida e volta passam pela parada (via estreita); a IDA é o
    # lado dela (distância menor). Linha Y: só circular.
    db.add_all(
        [
            Rota(numero=LINHA_X, sentido="IDA", nome=f"{LINHA_X} — Linha X", trajeto=[], paradas=pontas,
                 horarios_por_dia={"0": ["06:00", "12:00"], "6": ["09:00"]}),
            Rota(numero=LINHA_X, sentido="VOLTA", nome=f"{LINHA_X} — Linha X", trajeto=[], paradas=pontas[::-1],
                 horarios_por_dia={"0": ["07:00"]}),
            Rota(numero=LINHA_Y, sentido="CIRCULAR", nome=f"{LINHA_Y} — Linha Y", trajeto=[], paradas=pontas,
                 horarios_por_dia={"0": ["08:00"]}),
        ]
    )
    db.add_all(
        [
            RotaParada(numero=LINHA_X, sentido="IDA", parada_id=parada.id, ordem=4,
                       indice_trajeto=10, distancia_acumulada_m=500.0, distancia_ao_trajeto_m=3.0),
            RotaParada(numero=LINHA_X, sentido="VOLTA", parada_id=parada.id, ordem=7,
                       indice_trajeto=40, distancia_acumulada_m=900.0, distancia_ao_trajeto_m=28.0),
            RotaParada(numero=LINHA_Y, sentido="CIRCULAR", parada_id=parada.id, ordem=1,
                       indice_trajeto=2, distancia_acumulada_m=80.0, distancia_ao_trajeto_m=5.0),
        ]
    )
    db.commit()
    db.close()
    yield
    db2 = SessionLocal()
    limpar(db2)
    db2.close()


def _fingir_agora(monkeypatch, quando: datetime):
    class Falso(datetime):
        @classmethod
        def now(cls, tz=None):
            return quando.replace(tzinfo=tz)

    monkeypatch.setattr("mobilidade.parada_service.datetime", Falso)


def test_parada_fisica_devolve_codigo_da_tabela_e_uma_entrada_por_linha(parada_fisica):
    response = client.get(
        "/mobilidade/paradas", params={"lat": FISICA_LAT, "lng": FISICA_LNG}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["codigo"] == "PR-99999"
    assert data["nome"] == "Parada Física Teste"
    por_numero = {l["numero"]: l for l in data["linhas"]}
    assert set(por_numero) == {LINHA_X, LINHA_Y}  # X aparece uma vez, não duas


def test_parada_em_ida_e_volta_fica_com_a_rota_mais_proxima_do_tracado(parada_fisica):
    data = client.get(
        "/mobilidade/paradas", params={"lat": FISICA_LAT, "lng": FISICA_LNG}
    ).json()

    linha_x = next(l for l in data["linhas"] if l["numero"] == LINHA_X)
    assert linha_x["rota_sentido"] == "IDA"
    assert linha_x["ordem"] == 4
    assert linha_x["sentido"] == "Terminal X → Destino X"


def test_mesma_parada_por_coordenadas_levemente_diferentes_tem_o_mesmo_codigo(parada_fisica):
    # Cenário 4: o usuário clica no marcador de uma ou de outra linha, a
    # alguns metros de distância — o código não pode mudar.
    a = client.get("/mobilidade/paradas", params={"lat": FISICA_LAT, "lng": FISICA_LNG}).json()
    b = client.get(
        "/mobilidade/paradas",
        params={"lat": FISICA_LAT + 0.00005, "lng": FISICA_LNG + 0.00003},
    ).json()

    assert a["codigo"] == b["codigo"] == "PR-99999"


def test_horarios_sao_os_do_dia_da_semana_corrente(parada_fisica, monkeypatch):
    # 2026-10-05 é segunda-feira: saídas de segunda das duas linhas, não as de domingo.
    _fingir_agora(monkeypatch, datetime(2026, 10, 5, 5, 0))
    segunda = client.get(
        "/mobilidade/paradas", params={"lat": FISICA_LAT, "lng": FISICA_LNG}
    ).json()
    assert segunda["proximos_horarios"] == ["06:00", "08:00", "12:00"]

    # 2026-10-11 é domingo: só a saída de domingo da linha X.
    _fingir_agora(monkeypatch, datetime(2026, 10, 11, 5, 0))
    domingo = client.get(
        "/mobilidade/paradas", params={"lat": FISICA_LAT, "lng": FISICA_LNG}
    ).json()
    assert domingo["proximos_horarios"] == ["09:00"]


def test_sem_parada_fisica_perto_cai_no_caminho_antigo(parada_fisica, parada_com_duas_linhas):
    # Coordenada fora do raio da parada física: o serviço não responde 404,
    # usa as linhas cacheadas — o que garante /paradas entre o deploy e a
    # primeira reingestão.
    response = client.get(
        "/mobilidade/paradas", params={"lat": PARADA_LAT, "lng": PARADA_LNG}
    )

    assert response.status_code == 200
    assert response.json()["nome"] == "Parada Teste US18"
    assert response.json()["linhas"][0]["rota_sentido"] is None
