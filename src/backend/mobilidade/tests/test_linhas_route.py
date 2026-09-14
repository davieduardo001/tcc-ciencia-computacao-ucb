from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from mobilidade.main import app
from mobilidade.models.linha import Linha
from mobilidade.routes import _linha_service
from shared.database import SessionLocal, engine

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
    # O LinhaService guarda o catálogo em memória (CATALOGO_CACHE_SEGUNDOS)
    # e é um singleton de módulo em routes.py — sem invalidar, um teste
    # veria as linhas semeadas pelo anterior e o resultado passaria a
    # depender da ordem de execução.
    _linha_service.invalidar_catalogo()

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
    _linha_service.invalidar_catalogo()


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


def test_autocomplete_nao_carrega_a_geometria_do_trajeto(catalogo_semeado):
    """
    Regressão: o autocomplete usava `db.query(Linha)`, que traz a coluna
    `trajeto` junto. Com as 923 linhas reais do SEMOB isso são ~930 mil
    coordenadas (~30 MB) lidas e desserializadas a cada tecla digitada —
    em produção a rota passou a responder 502 depois de 57s. Com o mock
    de 2 linhas o custo era invisível, por isso nenhum teste pegou.
    """
    consultas: list[str] = []

    def registrar(conn, cursor, statement, parameters, context, executemany):
        consultas.append(statement)

    event.listen(engine, "before_cursor_execute", registrar)
    try:
        response = client.get("/mobilidade/linhas", params={"q": "ceilandia"})
    finally:
        event.remove(engine, "before_cursor_execute", registrar)

    assert response.status_code == 200

    consultas_na_linha = [c for c in consultas if "linha" in c.lower()]
    assert consultas_na_linha, "esperava ao menos uma consulta à tabela linha"
    for consulta in consultas_na_linha:
        assert "trajeto" not in consulta.lower(), (
            f"autocomplete não deve ler a coluna trajeto: {consulta}"
        )


def test_autocomplete_reaproveita_o_catalogo_em_memoria(catalogo_semeado):
    """
    A segunda sugestão seguida não deve reconsultar o banco: o catálogo
    só muda quando a ingestão do SEMOB roda, e o autocomplete dispara a
    cada tecla digitada.
    """
    client.get("/mobilidade/linhas", params={"q": "ceilandia"})

    consultas: list[str] = []

    def registrar(conn, cursor, statement, parameters, context, executemany):
        consultas.append(statement)

    event.listen(engine, "before_cursor_execute", registrar)
    try:
        response = client.get("/mobilidade/linhas", params={"q": "sobradinho"})
    finally:
        event.remove(engine, "before_cursor_execute", registrar)

    assert response.status_code == 200
    assert [c for c in consultas if "linha" in c.lower()] == []


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
