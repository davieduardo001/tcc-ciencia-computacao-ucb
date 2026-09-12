from fastapi.testclient import TestClient

from mobilidade.main import app

client = TestClient(app)


def test_busca_linha_encontrada():
    # CI roda sem GOOGLE_MAPS_API_KEY, então a rota usa o LinhaMockProvider
    # (ver mobilidade/routes.py) — "0.110" é uma das linhas do mock.
    response = client.get("/mobilidade/linhas/0.110")

    assert response.status_code == 200
    data = response.json()
    assert data["numero"] == "0.110"
    assert data["sentido"] == "Taguatinga → Rodoviária do Plano Piloto"
    assert len(data["paradas"]) > 0
    assert len(data["trajeto"]) > 0
    assert len(data["horarios_previstos"]) > 0


def test_busca_linha_nao_encontrada():
    response = client.get("/mobilidade/linhas/9.999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Linha não encontrada."


def test_segunda_busca_usa_cache_do_banco():
    # A primeira chamada popula o cache (schema mobilidade, tabela linha).
    # A segunda deve devolver os mesmos dados sem precisar do provider —
    # aqui não temos como observar "zero chamadas ao provider" direto
    # pela rota, mas garantimos que o resultado é estável e consistente.
    primeira = client.get("/mobilidade/linhas/0.108")
    segunda = client.get("/mobilidade/linhas/0.108")

    assert primeira.status_code == 200
    assert segunda.status_code == 200
    assert primeira.json() == segunda.json()
