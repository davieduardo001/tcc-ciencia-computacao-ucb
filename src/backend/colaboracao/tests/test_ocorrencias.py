import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from colaboracao.main import app
from colaboracao.models import Ocorrencia
from shared.database import get_db

client = TestClient(app)

USUARIO_ID = "550e8400-e29b-41d4-a716-446655440000"
HEADERS = {"X-User-Id": USUARIO_ID}


def _setup_db(reportes_na_janela=None):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
        reportes_na_janela or []
    )
    app.dependency_overrides[get_db] = lambda: mock_db
    return mock_db


def _reporte_mock(criado_em: datetime) -> Ocorrencia:
    return Ocorrencia(
        id=uuid.uuid4(),
        usuario_id=uuid.UUID(USUARIO_ID),
        linha_numero="0.110",
        tipo="atraso",
        status="pendente",
        contador_confirmacoes=0,
        criado_em=criado_em,
        expira_em=criado_em + timedelta(minutes=30),
    )


# ---------------------------------------------------------------------------
# POST /ocorrencias
# ---------------------------------------------------------------------------


def test_reportar_ocorrencia_sucesso():
    _setup_db()
    try:
        response = client.post(
            "/colaboracao/ocorrencias",
            headers=HEADERS,
            json={"linha_numero": "0.110", "tipo": "atraso", "local": "Parada W3 Sul"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["linha_numero"] == "0.110"
        assert data["status"] == "pendente"
        assert data["contador_confirmacoes"] == 0
    finally:
        app.dependency_overrides.clear()


def test_reportar_ocorrencia_tipo_imediato_nao_fica_pendente():
    _setup_db()
    try:
        response = client.post(
            "/colaboracao/ocorrencias",
            headers=HEADERS,
            json={"linha_numero": "0.110", "tipo": "acidente"},
        )
        assert response.status_code == 201
        assert response.json()["status"] == "confirmada"
    finally:
        app.dependency_overrides.clear()


def test_reportar_ocorrencia_tipo_invalido():
    _setup_db()
    try:
        response = client.post(
            "/colaboracao/ocorrencias",
            headers=HEADERS,
            json={"linha_numero": "0.110", "tipo": "sabotagem"},
        )
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_reportar_ocorrencia_sem_autenticacao():
    _setup_db()
    try:
        response = client.post(
            "/colaboracao/ocorrencias",
            json={"linha_numero": "0.110", "tipo": "atraso"},
        )
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_reportar_ocorrencia_limite_excedido():
    agora = datetime.utcnow()
    tres_reportes = [_reporte_mock(agora - timedelta(minutes=m)) for m in (50, 30, 10)]
    _setup_db(tres_reportes)
    try:
        response = client.post(
            "/colaboracao/ocorrencias",
            headers=HEADERS,
            json={"linha_numero": "0.110", "tipo": "atraso"},
        )
        assert response.status_code == 429
        assert response.json()["detail"]["detail"] == "limite_reportes_excedido"
        assert "reset_em" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /ocorrencias (US #24)
#
# Banco SQLite de verdade, e não MagicMock: o que se testa aqui é o filtro
# (expiradas, linha) e a ordenação, que um mock encadeado não exercita.
# ---------------------------------------------------------------------------


def _banco_real(*ocorrencias: Ocorrencia):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Ocorrencia.__table__.create(bind=engine)
    SessionLocal = sessionmaker(bind=engine)

    sessao = SessionLocal()
    sessao.add_all(ocorrencias)
    sessao.commit()
    sessao.close()

    def _get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    return SessionLocal


def _ocorrencia(
    linha="0.110",
    tipo="atraso",
    status="pendente",
    contador=0,
    criada_ha_min=5,
    expira_em_min=25,
    usuario_id=None,
) -> Ocorrencia:
    agora = datetime.utcnow()
    return Ocorrencia(
        id=uuid.uuid4(),
        usuario_id=usuario_id or uuid.uuid4(),
        linha_numero=linha,
        tipo=tipo,
        descricao="Descrição de teste",
        local="Parada W3 Sul",
        status=status,
        contador_confirmacoes=contador,
        criado_em=agora - timedelta(minutes=criada_ha_min),
        expira_em=agora + timedelta(minutes=expira_em_min),
    )


def test_listar_ocorrencia_confirmada_vem_como_confirmada():
    """Cenário 1: confirmada por múltiplos usuários aparece como confirmada."""
    _banco_real(_ocorrencia(tipo="nao_passou", status="confirmada", contador=3))
    try:
        response = client.get("/colaboracao/ocorrencias", headers=HEADERS)
        assert response.status_code == 200
        [item] = response.json()
        assert item["status"] == "confirmada"
        assert item["contador_confirmacoes"] == 3
    finally:
        app.dependency_overrides.clear()


def test_listar_ocorrencia_com_um_reporte_vem_como_pendente():
    """Cenário 2: um único reporte aparece como pendente de validação."""
    _banco_real(_ocorrencia(status="pendente", contador=0))
    try:
        [item] = client.get("/colaboracao/ocorrencias", headers=HEADERS).json()
        assert item["status"] == "pendente"
    finally:
        app.dependency_overrides.clear()


def test_listar_nao_mostra_ocorrencia_expirada():
    """Cenário 3: passou de `expira_em`, sai da listagem."""
    _banco_real(
        _ocorrencia(linha="0.110", criada_ha_min=5, expira_em_min=25),
        _ocorrencia(linha="0.222", criada_ha_min=90, expira_em_min=-30),
    )
    try:
        itens = client.get("/colaboracao/ocorrencias", headers=HEADERS).json()
        assert [i["linha_numero"] for i in itens] == ["0.110"]
    finally:
        app.dependency_overrides.clear()


def test_listar_marca_a_expirada_no_banco_sem_apagar():
    """A expiração vira status `expirada` (histórico fica; retenção é 30 dias)."""
    expirada = _ocorrencia(criada_ha_min=90, expira_em_min=-30)
    id_expirada = expirada.id
    SessionLocal = _banco_real(expirada)
    try:
        client.get("/colaboracao/ocorrencias", headers=HEADERS)

        db = SessionLocal()
        registro = db.get(Ocorrencia, id_expirada)
        assert registro is not None
        assert registro.status == "expirada"
        db.close()
    finally:
        app.dependency_overrides.clear()


def test_listar_filtra_por_linha():
    _banco_real(_ocorrencia(linha="0.110"), _ocorrencia(linha="0.222"))
    try:
        itens = client.get(
            "/colaboracao/ocorrencias", headers=HEADERS, params={"linha": "0.222"}
        ).json()
        assert [i["linha_numero"] for i in itens] == ["0.222"]
    finally:
        app.dependency_overrides.clear()


def test_listar_ordena_da_mais_recente_para_a_mais_antiga():
    _banco_real(
        _ocorrencia(linha="0.antiga", criada_ha_min=20),
        _ocorrencia(linha="0.recente", criada_ha_min=2),
        _ocorrencia(linha="0.meio", criada_ha_min=10),
    )
    try:
        itens = client.get("/colaboracao/ocorrencias", headers=HEADERS).json()
        assert [i["linha_numero"] for i in itens] == ["0.recente", "0.meio", "0.antiga"]
    finally:
        app.dependency_overrides.clear()


def test_listar_mostra_ocorrencias_de_outros_usuarios_sem_expor_quem_reportou():
    outro_usuario = uuid.uuid4()
    _banco_real(_ocorrencia(usuario_id=outro_usuario))
    try:
        [item] = client.get("/colaboracao/ocorrencias", headers=HEADERS).json()
        assert "usuario_id" not in item
        assert str(outro_usuario) not in str(item)
    finally:
        app.dependency_overrides.clear()


def test_listar_devolve_horarios_em_utc_com_fuso_explicito():
    """Sem "Z" o navegador lê o horário como local e mostra "há 3 horas"."""
    _banco_real(_ocorrencia())
    try:
        [item] = client.get("/colaboracao/ocorrencias", headers=HEADERS).json()
        assert item["criado_em"].endswith("Z")
        assert item["expira_em"].endswith("Z")
    finally:
        app.dependency_overrides.clear()


def test_listar_vazio_quando_nao_ha_ocorrencias():
    _banco_real()
    try:
        response = client.get("/colaboracao/ocorrencias", headers=HEADERS)
        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.clear()


def test_listar_sem_autenticacao():
    _banco_real(_ocorrencia())
    try:
        assert client.get("/colaboracao/ocorrencias").status_code == 401
    finally:
        app.dependency_overrides.clear()
