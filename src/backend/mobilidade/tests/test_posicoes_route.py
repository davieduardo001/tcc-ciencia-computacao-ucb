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
from mobilidade.posicao_service import PosicaoVeiculo
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
