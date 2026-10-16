# US #21 — Buscar Parada por Nome ou Endereço.

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from mobilidade.geocode_service import Lugar
from mobilidade.main import app
from mobilidade.models.parada import Parada, RotaParada
from shared.database import SessionLocal

client = TestClient(app)

# Coordenadas longe das usadas pelos outros testes de parada, pra que a
# busca por raio não esbarre em dados semeados por eles.
CENTRO_LAT = -15.9000
CENTRO_LNG = -48.1000

# ~0,0009° de latitude ≈ 100 m; ~0,0063° ≈ 700 m.
CODIGOS = ["PR-T21-PERTO", "PR-T21-MEIO", "PR-T21-LONGE", "PR-T21-SEMLN"]
LINHAS = ["9.210", "9.211", "9.212"]


@pytest.fixture
def paradas_da_busca():
    db = SessionLocal()

    def limpar(s):
        s.query(RotaParada).filter(RotaParada.numero.in_(LINHAS)).delete(
            synchronize_session=False
        )
        s.query(Parada).filter(Parada.codigo.in_(CODIGOS)).delete(synchronize_session=False)
        s.commit()

    limpar(db)
    perto = Parada(codigo="PR-T21-PERTO", nome="Estação Ceilândia Teste US21",
                   lat=CENTRO_LAT + 0.0009, lng=CENTRO_LNG)
    meio = Parada(codigo="PR-T21-MEIO", nome="Avenida Hélio Prates Teste US21",
                  lat=CENTRO_LAT + 0.0030, lng=CENTRO_LNG)
    longe = Parada(codigo="PR-T21-LONGE", nome="Quadra Longe Teste US21",
                   lat=CENTRO_LAT + 0.0063, lng=CENTRO_LNG)
    # Sem nenhuma linha vinculada: não responde "quais linhas passam por aqui".
    sem_linha = Parada(codigo="PR-T21-SEMLN", nome="Abrigo Sem Linha Teste US21",
                       lat=CENTRO_LAT, lng=CENTRO_LNG)
    db.add_all([perto, meio, longe, sem_linha])
    db.flush()

    def vinculo(numero, parada, ordem):
        return RotaParada(numero=numero, sentido="IDA", parada_id=parada.id, ordem=ordem,
                          indice_trajeto=ordem, distancia_acumulada_m=0.0,
                          distancia_ao_trajeto_m=1.0)

    db.add_all(
        [
            # A parada "perto" tem duas linhas — e a 9.210 duas vezes (IDA e
            # VOLTA), que deve contar como uma linha só.
            vinculo(LINHAS[0], perto, 1),
            RotaParada(numero=LINHAS[0], sentido="VOLTA", parada_id=perto.id, ordem=9,
                       indice_trajeto=9, distancia_acumulada_m=0.0, distancia_ao_trajeto_m=8.0),
            vinculo(LINHAS[1], perto, 2),
            vinculo(LINHAS[1], meio, 3),
            vinculo(LINHAS[2], longe, 4),
        ]
    )
    db.commit()
    db.close()
    yield
    db2 = SessionLocal()
    limpar(db2)
    db2.close()


def _geocodificador(lugares):
    return patch("mobilidade.routes._geocode_service.buscar", AsyncMock(return_value=lugares))


# -- Cenário 1: busca por nome ------------------------------------------------


def test_busca_por_nome_ignora_acento_e_caixa(paradas_da_busca):
    with _geocodificador([]) as geocode:
        response = client.get("/mobilidade/paradas/busca", params={"q": "ESTACAO ceilandia teste us21"})

    assert response.status_code == 200
    data = response.json()
    assert data["tipo"] == "nome"
    assert [p["codigo"] for p in data["paradas"]] == ["PR-T21-PERTO"]
    assert data["referencia"] is None
    # Achou pelo nome: não gasta chamada no Nominatim.
    geocode.assert_not_called()


def test_busca_por_nome_aceita_palavras_em_qualquer_ordem(paradas_da_busca):
    with _geocodificador([]):
        data = client.get("/mobilidade/paradas/busca", params={"q": "prates us21 helio"}).json()

    assert [p["codigo"] for p in data["paradas"]] == ["PR-T21-MEIO"]


def test_busca_por_nome_conta_linhas_distintas(paradas_da_busca):
    with _geocodificador([]):
        data = client.get("/mobilidade/paradas/busca", params={"q": "estacao ceilandia teste us21"}).json()

    parada = data["paradas"][0]
    assert parada["qtd_linhas"] == 2  # 9.210 (IDA e VOLTA) + 9.211
    assert parada["distancia_m"] is None


def test_busca_por_nome_deixa_de_fora_parada_sem_linha(paradas_da_busca):
    with _geocodificador([]):
        data = client.get("/mobilidade/paradas/busca", params={"q": "abrigo sem linha teste us21"}).json()

    assert data["tipo"] == "nenhum"
    assert data["paradas"] == []


def test_busca_por_nome_trata_curinga_do_like_como_texto(paradas_da_busca):
    # "%" sem escape casaria com qualquer nome.
    with _geocodificador([]):
        data = client.get("/mobilidade/paradas/busca", params={"q": "us21 %%%"}).json()

    assert data["paradas"] == []


# -- Cenário 2: busca por endereço / ponto de referência ----------------------


def test_busca_por_endereco_traz_paradas_no_raio_de_500m_mais_proxima_primeiro(paradas_da_busca):
    lugar = Lugar(nome="Praça Teste", endereco="Praça Teste, Ceilândia",
                  lat=CENTRO_LAT, lng=CENTRO_LNG)

    with _geocodificador([lugar]):
        response = client.get("/mobilidade/paradas/busca", params={"q": "praca qualquer"})

    assert response.status_code == 200
    data = response.json()
    assert data["tipo"] == "endereco"
    assert data["referencia"]["nome"] == "Praça Teste"
    codigos = [p["codigo"] for p in data["paradas"]]
    # ~100 m e ~330 m entram; ~700 m fica fora; a sem linha também.
    assert codigos == ["PR-T21-PERTO", "PR-T21-MEIO"]
    distancias = [p["distancia_m"] for p in data["paradas"]]
    assert 90 <= distancias[0] <= 110
    assert distancias[0] < distancias[1] <= 500


# -- Cenário 3: nenhum resultado ----------------------------------------------


def test_sem_nome_e_sem_lugar_devolve_nenhum(paradas_da_busca):
    with _geocodificador([]):
        response = client.get("/mobilidade/paradas/busca", params={"q": "xyzw inexistente"})

    assert response.status_code == 200
    assert response.json() == {"tipo": "nenhum", "paradas": [], "referencia": None}


def test_lugar_sem_parada_no_raio_devolve_nenhum(paradas_da_busca):
    lugar = Lugar(nome="Meio do Nada", endereco="", lat=1.0, lng=1.0)

    with _geocodificador([lugar]):
        data = client.get("/mobilidade/paradas/busca", params={"q": "meio do nada"}).json()

    assert data["tipo"] == "nenhum"
    assert data["paradas"] == []


def test_termo_curto_nao_busca(paradas_da_busca):
    with _geocodificador([]) as geocode:
        data = client.get("/mobilidade/paradas/busca", params={"q": " a "}).json()

    assert data["tipo"] == "nenhum"
    geocode.assert_not_called()
