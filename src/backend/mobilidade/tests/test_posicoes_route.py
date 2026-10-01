"""US #19 — ETA na rota GET /mobilidade/linhas/{numero}/posicoes.

Mocka o PosicaoService (assim como o feed do SEMOB já é mockado em
test_posicao_service.py) pra controlar exatamente quantos veículos, com
que velocidade, a rota enxerga em cada cenário.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from mobilidade.main import app
from mobilidade.models.linha import Linha
from mobilidade.models.rota import Rota, RotaCelula
from mobilidade.posicao_service import PosicaoVeiculo
from mobilidade.tests.test_rota_service import PREFIXO, _semear, _trajeto
from shared.database import SessionLocal

client = TestClient(app)

NUMERO_LINHA = "9.980"

# Ponto a ~1.1 km do usuário — o suficiente pra um ETA não-zero e
# plausível com velocidades urbanas.
LAT_USUARIO, LNG_USUARIO = -15.8300, -48.0500
LAT_VEICULO, LNG_VEICULO = -15.8400, -48.0500


def _veiculo(velocidade):
    return PosicaoVeiculo(
        prefixo="440001",
        lat=LAT_VEICULO,
        lng=LNG_VEICULO,
        sentido="IDA",
        velocidade=velocidade,
        direcao=0.0,
        atualizado_em=datetime.now(timezone.utc),
        operadora="VIAÇÃO TESTE",
    )


def _mockar_posicoes(veiculos):
    return patch(
        "mobilidade.routes._posicao_service.posicoes_da_linha",
        AsyncMock(return_value=veiculos),
    )


def test_sem_lat_lng_nao_calcula_eta():
    # Compatibilidade com o front antes da US #19: sem coordenadas, o
    # comportamento da US #16 continua idêntico.
    with _mockar_posicoes([_veiculo(30.0)]):
        response = client.get(f"/mobilidade/linhas/{NUMERO_LINHA}/posicoes")

    assert response.status_code == 200
    data = response.json()
    assert data["veiculos"][0]["eta_minutos"] is None
    assert data["proximo_horario_previsto"] is None


def test_com_lat_lng_calcula_eta_do_veiculo_em_movimento():
    # Cenário 1/4 da US #19.
    with _mockar_posicoes([_veiculo(30.0)]):
        response = client.get(
            f"/mobilidade/linhas/{NUMERO_LINHA}/posicoes",
            params={"lat": LAT_USUARIO, "lng": LNG_USUARIO},
        )

    assert response.status_code == 200
    eta = response.json()["veiculos"][0]["eta_minutos"]
    assert eta is not None and eta > 0


def test_veiculo_parado_fica_sem_eta():
    # Cenário 5: pílula sem tempo pra veículo parado.
    with _mockar_posicoes([_veiculo(0.0)]):
        response = client.get(
            f"/mobilidade/linhas/{NUMERO_LINHA}/posicoes",
            params={"lat": LAT_USUARIO, "lng": LNG_USUARIO},
        )

    assert response.status_code == 200
    assert response.json()["veiculos"][0]["eta_minutos"] is None


@pytest.fixture
def linha_com_horario_cacheado():
    db = SessionLocal()
    db.query(Linha).filter(Linha.numero == NUMERO_LINHA).delete()
    db.add(
        Linha(
            numero=NUMERO_LINHA,
            nome=f"{NUMERO_LINHA} — Linha de teste",
            sentido="Circular",
            paradas=[{"nome": "Terminal Teste", "lat": LAT_USUARIO, "lng": LNG_USUARIO}],
            trajeto=[[LAT_USUARIO, LNG_USUARIO]],
            horarios_previstos=["06:00", "23:59"],
        )
    )
    db.commit()
    yield
    db.query(Linha).filter(Linha.numero == NUMERO_LINHA).delete()
    db.commit()
    db.close()


def test_sem_veiculo_cai_pro_horario_previsto(linha_com_horario_cacheado):
    # Cenário 3: nenhum veículo com GPS reportando.
    with _mockar_posicoes([]):
        response = client.get(
            f"/mobilidade/linhas/{NUMERO_LINHA}/posicoes",
            params={"lat": LAT_USUARIO, "lng": LNG_USUARIO},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["veiculos"] == []
    assert data["proximo_horario_previsto"] in ("06:00", "23:59")


def test_sem_veiculo_e_sem_lat_lng_nao_busca_horario_previsto(linha_com_horario_cacheado):
    with _mockar_posicoes([]):
        response = client.get(f"/mobilidade/linhas/{NUMERO_LINHA}/posicoes")

    assert response.status_code == 200
    assert response.json()["proximo_horario_previsto"] is None


# --------------------------------------------------------------------------
# US #159 — quando a linha tem rota ingerida, o ETA passa a ser medido
# ao longo do trajeto real, não em linha reta. Usa o mesmo trajeto
# sintético de test_rota_service.py para poder colocar o veículo "antes"
# e "depois" do ponto informado.
# --------------------------------------------------------------------------

NUMERO_COM_ROTA = f"{PREFIXO}200"


@pytest.fixture
def rota_ingerida():
    db = SessionLocal()
    db.query(RotaCelula).filter(RotaCelula.numero == NUMERO_COM_ROTA).delete()
    db.query(Rota).filter(Rota.numero == NUMERO_COM_ROTA).delete()
    _semear(db, NUMERO_COM_ROTA, "IDA", _trajeto())
    db.commit()
    yield
    db.query(RotaCelula).filter(RotaCelula.numero == NUMERO_COM_ROTA).delete()
    db.query(Rota).filter(Rota.numero == NUMERO_COM_ROTA).delete()
    db.commit()
    db.close()


def _veiculo_no_indice(indice, sentido="IDA"):
    lat, lng = _trajeto()[indice]
    return PosicaoVeiculo(
        prefixo="440001",
        lat=lat,
        lng=lng,
        sentido=sentido,
        velocidade=30.0,
        direcao=0.0,
        atualizado_em=datetime.now(timezone.utc),
        operadora="VIAÇÃO TESTE",
    )


def test_com_rota_ingerida_eta_e_medido_ao_longo_do_trajeto(rota_ingerida):
    alvo_lat, alvo_lng = _trajeto()[20]
    # Veículo antes do alvo (índice 5): está chegando.
    with _mockar_posicoes([_veiculo_no_indice(5)]):
        response = client.get(
            f"/mobilidade/linhas/{NUMERO_COM_ROTA}/posicoes",
            params={"lat": alvo_lat, "lng": alvo_lng},
        )

    assert response.status_code == 200
    assert response.json()["veiculos"][0]["eta_minutos"] is not None


def test_com_rota_ingerida_veiculo_que_ja_passou_fica_sem_eta(rota_ingerida):
    """
    A diferença central desta melhoria: em linha reta, um ônibus logo
    depois do alvo mede "perto" do mesmo jeito que um que está
    chegando. Com o trajeto conhecido, dá para saber que ele já passou.
    """
    alvo_lat, alvo_lng = _trajeto()[20]
    # Veículo depois do alvo (índice 25): já passou, mesmo sentido.
    with _mockar_posicoes([_veiculo_no_indice(25)]):
        response = client.get(
            f"/mobilidade/linhas/{NUMERO_COM_ROTA}/posicoes",
            params={"lat": alvo_lat, "lng": alvo_lng},
        )

    assert response.status_code == 200
    assert response.json()["veiculos"][0]["eta_minutos"] is None


def test_com_rota_ingerida_sentido_errado_fica_sem_eta(rota_ingerida):
    alvo_lat, alvo_lng = _trajeto()[20]
    with _mockar_posicoes([_veiculo_no_indice(5, sentido="VOLTA")]):
        response = client.get(
            f"/mobilidade/linhas/{NUMERO_COM_ROTA}/posicoes",
            params={"lat": alvo_lat, "lng": alvo_lng},
        )

    assert response.status_code == 200
    assert response.json()["veiculos"][0]["eta_minutos"] is None
