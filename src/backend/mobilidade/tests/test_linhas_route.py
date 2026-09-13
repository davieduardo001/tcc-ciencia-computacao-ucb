from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from mobilidade.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _sem_osrm_de_verdade():
    """
    Essas rotas usam o LinhaMockProvider real (sem GOOGLE_MAPS_API_KEY
    no CI), e a primeira busca de cada linha tenta road-snapping via
    OSRM (ver LinhaService._com_trajeto_real). Sem isso, os testes
    dependeriam de rede real pro router.project-osrm.org — flaky e
    lento. Retornar None aqui faz o LinhaService cair de volta pros
    pontos originais do mock, mantendo as asserções abaixo estáveis.
    """
    with patch(
        "mobilidade.linha_service.osrm_router.rotear",
        AsyncMock(return_value=None),
    ):
        yield


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


# ---------------------------------------------------------------------------
# US #17 (autocomplete) — GET /mobilidade/linhas?q=
# ---------------------------------------------------------------------------


def test_sugerir_linhas_sem_termo_lista_todas():
    response = client.get("/mobilidade/linhas")

    assert response.status_code == 200
    numeros = {item["numero"] for item in response.json()}
    assert {"0.110", "0.108"}.issubset(numeros)


def test_sugerir_linhas_por_numero():
    response = client.get("/mobilidade/linhas", params={"q": "0.110"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["numero"] == "0.110"
    assert data[0]["sentido"] == "Taguatinga → Rodoviária do Plano Piloto"


def test_sugerir_linhas_por_destino_sem_acento():
    # "ceilandia" (sem acento, minúsculo) deve encontrar a 0.108, que
    # passa por "Terminal Ceilândia Centro" — cenário real do pedido:
    # buscar por pra onde o ônibus vai, não só o número exato.
    response = client.get("/mobilidade/linhas", params={"q": "ceilandia"})

    assert response.status_code == 200
    numeros = {item["numero"] for item in response.json()}
    assert "0.108" in numeros
    assert "0.110" not in numeros


def test_sugerir_linhas_sem_combinacao_retorna_lista_vazia():
    response = client.get("/mobilidade/linhas", params={"q": "nao existe"})

    assert response.status_code == 200
    assert response.json() == []


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
