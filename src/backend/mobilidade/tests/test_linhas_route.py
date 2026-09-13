from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from mobilidade.main import app
from mobilidade.models.linha import Linha
from shared.database import SessionLocal

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
#
# O autocomplete lê o catálogo da tabela `linha` (populada pela ingestão
# do SEMOB). Como outros testes deste arquivo cacheiam linhas ali, estes
# semeiam o próprio par de linhas e afirmam só sobre ele — assim não
# dependem da ordem de execução nem do que o mock conhece.
# ---------------------------------------------------------------------------

LINHA_COM_CEILANDIA = "9.990"
LINHA_SEM_CEILANDIA = "9.991"


@pytest.fixture
def catalogo_semeado():
    db = SessionLocal()
    db.query(Linha).filter(
        Linha.numero.in_([LINHA_COM_CEILANDIA, LINHA_SEM_CEILANDIA])
    ).delete(synchronize_session=False)
    db.add(
        Linha(
            numero=LINHA_COM_CEILANDIA,
            nome=f"{LINHA_COM_CEILANDIA} — Circular Ceilândia / Plano Piloto",
            sentido="Circular",
            paradas=[{"nome": "Terminal Ceilândia Centro", "lat": -15.81, "lng": -48.10}],
            trajeto=[[-15.81, -48.10]],
            horarios_previstos=["06:00"],
        )
    )
    db.add(
        Linha(
            numero=LINHA_SEM_CEILANDIA,
            nome=f"{LINHA_SEM_CEILANDIA} — Circular Sobradinho / Plano Piloto",
            sentido="Circular",
            paradas=[{"nome": "Terminal Sobradinho", "lat": -15.65, "lng": -47.79}],
            trajeto=[[-15.65, -47.79]],
            horarios_previstos=["07:00"],
        )
    )
    db.commit()
    yield
    db.query(Linha).filter(
        Linha.numero.in_([LINHA_COM_CEILANDIA, LINHA_SEM_CEILANDIA])
    ).delete(synchronize_session=False)
    db.commit()
    db.close()


def test_sugerir_linhas_sem_termo_lista_todas(catalogo_semeado):
    response = client.get("/mobilidade/linhas")

    assert response.status_code == 200
    numeros = {item["numero"] for item in response.json()}
    assert {LINHA_COM_CEILANDIA, LINHA_SEM_CEILANDIA}.issubset(numeros)


def test_sugerir_linhas_por_numero(catalogo_semeado):
    response = client.get("/mobilidade/linhas", params={"q": LINHA_COM_CEILANDIA})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["numero"] == LINHA_COM_CEILANDIA
    assert data[0]["sentido"] == "Circular"


def test_sugerir_linhas_por_destino_sem_acento(catalogo_semeado):
    # "ceilandia" (sem acento, minúsculo) tem que achar a linha que passa
    # por "Terminal Ceilândia Centro" — cenário real do pedido: buscar
    # por pra onde o ônibus vai, não só pelo número exato.
    response = client.get("/mobilidade/linhas", params={"q": "ceilandia"})

    assert response.status_code == 200
    numeros = {item["numero"] for item in response.json()}
    assert LINHA_COM_CEILANDIA in numeros
    assert LINHA_SEM_CEILANDIA not in numeros


def test_sugerir_linhas_sem_combinacao_retorna_lista_vazia(catalogo_semeado):
    response = client.get(
        "/mobilidade/linhas", params={"q": "zzz nao existe linha assim"}
    )

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
