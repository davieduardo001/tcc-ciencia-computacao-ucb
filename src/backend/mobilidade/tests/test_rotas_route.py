"""US #20 — rotas HTTP de planejamento de viagem. US #159 — ETA real."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from mobilidade.geocode_service import Lugar
from mobilidade.main import app
from mobilidade.models.rota import Rota, RotaCelula
from mobilidade.posicao_service import PosicaoVeiculo
from mobilidade.tests.test_rota_service import (
    LESTE,
    OESTE,
    PREFIXO,
    _semear,
    _trajeto,
)
from shared.database import SessionLocal

client = TestClient(app)


def _mockar_posicoes(posicoes_por_linha: dict):
    """
    `/rotas` agora busca posição ao vivo das linhas envolvidas (US
    #159). Sem mockar isso, o teste faria uma chamada de rede real ao
    SEMOB a cada request — aqui controlamos exatamente o que o motor de
    ETA enxerga, igual a `test_posicoes_route.py`.
    """
    return patch(
        "mobilidade.routes._posicao_service.posicoes_das_linhas",
        AsyncMock(return_value=posicoes_por_linha),
    )


def _veiculo_no_trajeto(indice, sentido="IDA", velocidade=30.0, prefixo="440001"):
    lat, lng = _trajeto()[indice]
    return PosicaoVeiculo(
        prefixo=prefixo,
        lat=lat,
        lng=lng,
        sentido=sentido,
        velocidade=velocidade,
        direcao=0.0,
        atualizado_em=datetime.now(timezone.utc),
        operadora="VIAÇÃO TESTE",
    )


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
    with _mockar_posicoes({}):
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
    # Sem veículo ao vivo: cai para a estimativa teórica de sempre.
    assert opcao["tipo_estimativa"] == "teorica"
    assert opcao["duracao_real_min"] is None

    perna = opcao["pernas"][0]
    assert perna["numero"] == f"{PREFIXO}100"
    assert perna["sentido"] == "IDA"
    assert perna["embarque"]["parada_nome"]
    assert perna["desembarque"]["parada_nome"]
    assert len(perna["trajeto"]) > 1
    assert perna["fonte_espera"] == "teorica"
    assert perna["espera_min"] is None


def test_calcular_rotas_com_onibus_real_traz_eta_ao_vivo(rota_semeada):
    # Embarque no índice 20 do trajeto (onde há uma parada cadastrada —
    # ver _paradas_padrao), com um veículo no índice 5: antes da
    # parada, no mesmo sentido. O motor de ETA (US #19/#159) deve achá-lo
    # e usar o tempo dele até lá, não a velocidade média.
    origem = _trajeto()[20]
    posicoes = {f"{PREFIXO}100": [_veiculo_no_trajeto(indice=5)]}

    with _mockar_posicoes(posicoes):
        response = client.get(
            "/mobilidade/rotas",
            params={
                "origem_lat": origem[0],
                "origem_lng": origem[1],
                "destino_lat": LESTE[0],
                "destino_lng": LESTE[1],
            },
        )

    assert response.status_code == 200
    opcoes = response.json()
    assert len(opcoes) == 1
    opcao = opcoes[0]

    assert opcao["tipo_estimativa"] == "tempo_real"
    assert opcao["duracao_real_min"] is not None
    assert opcao["calculado_em"] is not None

    perna = opcao["pernas"][0]
    assert perna["fonte_espera"] == "tempo_real"
    assert perna["espera_min"] is not None
    assert perna["prefixo_veiculo"] == "440001"


def test_coordenada_fora_de_faixa_e_erro_de_validacao():
    response = client.get(
        "/mobilidade/rotas",
        params={
            "origem_lat": 200.0,  # fora de -90..90
            "origem_lng": 0.0,
            "destino_lat": 0.0,
            "destino_lng": 0.0,
        },
    )

    assert response.status_code == 422


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
