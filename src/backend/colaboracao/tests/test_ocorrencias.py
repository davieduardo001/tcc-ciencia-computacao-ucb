import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

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
