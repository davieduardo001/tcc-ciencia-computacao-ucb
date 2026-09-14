"""US #20 — rotas HTTP de planejamento de viagem."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from mobilidade.geocode_service import Lugar
from mobilidade.main import app
from mobilidade.models.rota import Rota, RotaCelula
from mobilidade.tests.test_rota_service import (
    LESTE,
    OESTE,
    PREFIXO,
    _semear,
    _trajeto,
)
from shared.database import SessionLocal

client = TestClient(app)


@pytest.fixture
def rota_semeada():
    db = SessionLocal()
    _limpar(db)
    _semear(db, f"{PREFIXO}100", "IDA", _trajeto())
    db.commit()
    yield
    _limpar(db)
    db.close()


def _limpar(db) -> None:
    for modelo in (RotaCelula, Rota):
        db.query(modelo).filter(
            text("numero LIKE :p").bindparams(p=f"{PREFIXO}%")
        ).delete(synchronize_session=False)
    db.commit()


def test_calcular_rotas_devolve_opcao_com_embarque_e_desembarque(rota_semeada):
    response = client.get(
        "/mobilidade/rotas",
        params={
            "origem_lat": OESTE[0],
            "origem_lng": OESTE[1],
            "destino_lat": LESTE[0],
            "destino_lng": LESTE[1],
        },
    )

    assert response.status_code == 200
    opcoes = response.json()
    assert len(opcoes) == 1

    opcao = opcoes[0]
    assert opcao["baldeacoes"] == 0
    assert opcao["duracao_estimada_min"] > 0
    assert opcao["distancia_km"] > 10

    perna = opcao["pernas"][0]
    assert perna["numero"] == f"{PREFIXO}100"
    assert perna["sentido"] == "IDA"
    assert perna["embarque"]["parada_nome"]
    assert perna["desembarque"]["parada_nome"]
    assert len(perna["trajeto"]) > 1


def test_sem_rota_possivel_devolve_lista_vazia_e_nao_erro(rota_semeada):
    """
    Cenário 3 da US: "nenhuma rota disponível" é uma resposta válida,
    não uma falha. Devolver 404 faria o front tratar como erro.
    """
    response = client.get(
        "/mobilidade/rotas",
        params={
            # Sentido contrário ao da única linha cadastrada.
            "origem_lat": LESTE[0],
            "origem_lng": LESTE[1],
            "destino_lat": OESTE[0],
            "destino_lng": OESTE[1],
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_coordenada_faltando_e_erro_de_validacao():
    response = client.get("/mobilidade/rotas", params={"origem_lat": -15.8})

    assert response.status_code == 422


def test_buscar_lugares_devolve_coordenadas():
    lugares = [
        Lugar(
            nome="Rodoviaria do Plano Piloto",
            endereco="Rodoviaria do Plano Piloto, Brasília",
            lat=-15.7933,
            lng=-47.8826,
        )
    ]

    with patch(
        "mobilidade.routes._geocode_service.buscar",
        AsyncMock(return_value=lugares),
    ):
        response = client.get("/mobilidade/lugares", params={"q": "rodoviaria"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "nome": "Rodoviaria do Plano Piloto",
            "endereco": "Rodoviaria do Plano Piloto, Brasília",
            "lat": -15.7933,
            "lng": -47.8826,
        }
    ]


def test_buscar_lugares_sem_resultado_devolve_lista_vazia():
    with patch(
        "mobilidade.routes._geocode_service.buscar", AsyncMock(return_value=[])
    ):
        response = client.get("/mobilidade/lugares", params={"q": "zzzz"})

    assert response.status_code == 200
    assert response.json() == []


def test_lugar_reverso_sem_nome_conhecido_devolve_null():
    with patch(
        "mobilidade.routes._geocode_service.reverso", AsyncMock(return_value=None)
    ):
        response = client.get(
            "/mobilidade/lugares/reverso", params={"lat": -15.0, "lng": -47.0}
        )

    assert response.status_code == 200
    assert response.json() is None


def test_rota_de_lugares_nao_colide_com_a_busca_de_linha_por_numero(rota_semeada):
    """
    Regressão de ordem de rotas: /lugares e /rotas são declarados antes
    de /linhas/{numero_linha}. Se alguém reordenar, "lugares" passaria a
    ser lido como número de linha e devolveria 404.
    """
    with patch(
        "mobilidade.routes._geocode_service.buscar", AsyncMock(return_value=[])
    ):
        assert client.get("/mobilidade/lugares", params={"q": "teste"}).status_code == 200

    assert client.get("/mobilidade/linhas/0.110").status_code in (200, 404)
