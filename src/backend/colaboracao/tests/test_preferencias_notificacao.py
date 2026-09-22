import uuid
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from colaboracao.main import app
from colaboracao.models.preferencia_notificacao import PreferenciaNotificacao
from shared.database import get_db

client = TestClient(app)


def _override_get_db(mock_db):
    def _generator():
        yield mock_db
    return _generator()


def _criar_preferencia_mock(usuario_id: str = None) -> PreferenciaNotificacao:
    if usuario_id is None:
        usuario_id = str(uuid.uuid4())
    return PreferenciaNotificacao(
        id=uuid.uuid4(),
        usuario_id=uuid.UUID(usuario_id),
        antecedencia_minutos=30,
        notificacoes_ativas=True,
        alerta_chegada=True,
        alerta_cancelamento=True,
    )


# ---------------------------------------------------------------------------
# GET /preferencias/{usuario_id}
# ---------------------------------------------------------------------------

def test_carregar_preferenciasexistentes():
    mock_db = MagicMock()
    preferencia = _criar_preferencia_mock("550e8400-e29b-41d4-a716-446655440000")
    mock_db.query.return_value.filter.return_value.first.return_value = preferencia

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/colaboracao/preferencias/550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 200
        data = response.json()
        assert data["antecedencia_minutos"] == 30
        assert data["notificacoes_ativas"] is True
        assert data["alerta_chegada"] is True
        assert data["alerta_cancelamento"] is True
    finally:
        app.dependency_overrides.clear()


def test_carregar_preferencias_novo_usuario():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/colaboracao/preferencias/550e8400-e29b-41d4-a716-446655440001")
        assert response.status_code == 200
        data = response.json()
        assert data["antecedencia_minutos"] == 30
        assert data["notificacoes_ativas"] is True
        mock_db.add.assert_called_once()
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# PUT /preferencias/{usuario_id}/antecedencia
# ---------------------------------------------------------------------------

def test_salvar_antecedencia_sucesso():
    mock_db = MagicMock()
    preferencia = _criar_preferencia_mock("550e8400-e29b-41d4-a716-446655440000")
    mock_db.query.return_value.filter.return_value.first.return_value = preferencia

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.put(
            "/colaboracao/preferencias/550e8400-e29b-41d4-a716-446655440000/antecedencia",
            json={"antecedencia_minutos": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["antecedencia_minutos"] == 10
        mock_db.commit.assert_called()
    finally:
        app.dependency_overrides.clear()


def test_salvar_antecedencia_invalida():
    mock_db = MagicMock()
    preferencia = _criar_preferencia_mock("550e8400-e29b-41d4-a716-446655440000")
    mock_db.query.return_value.filter.return_value.first.return_value = preferencia

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.put(
            "/colaboracao/preferencias/550e8400-e29b-41d4-a716-446655440000/antecedencia",
            json={"antecedencia_minutos": 7},
        )
        assert response.status_code == 400
        assert "inválida" in response.json()["detail"].lower() or "inválida" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# PUT /preferencias/{usuario_id}/tipo/{tipo}
# ---------------------------------------------------------------------------

def test_desativar_tipo_cancelamento():
    mock_db = MagicMock()
    preferencia = _criar_preferencia_mock("550e8400-e29b-41d4-a716-446655440000")
    mock_db.query.return_value.filter.return_value.first.return_value = preferencia

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.put(
            "/colaboracao/preferencias/550e8400-e29b-41d4-a716-446655440000/tipo/cancelamento",
            json={"ativo": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["alerta_cancelamento"] is False
        assert data["alerta_chegada"] is True
        mock_db.commit.assert_called()
    finally:
        app.dependency_overrides.clear()


def test_desativar_tipo_chegada():
    mock_db = MagicMock()
    preferencia = _criar_preferencia_mock("550e8400-e29b-41d4-a716-446655440000")
    mock_db.query.return_value.filter.return_value.first.return_value = preferencia

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.put(
            "/colaboracao/preferencias/550e8400-e29b-41d4-a716-446655440000/tipo/chegada",
            json={"ativo": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["alerta_chegada"] is False
        assert data["alerta_cancelamento"] is True
    finally:
        app.dependency_overrides.clear()


def test_tipo_notificacao_invalido():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.put(
            "/colaboracao/preferencias/550e8400-e29b-41d4-a716-446655440000/tipo/invalido",
            json={"ativo": False},
        )
        assert response.status_code == 400
        assert "inválido" in response.json()["detail"].lower() or "inválido" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# PUT /preferencias/{usuario_id}/desativar-todas
# ---------------------------------------------------------------------------

def test_desativar_todas_notificacoes():
    mock_db = MagicMock()
    preferencia = _criar_preferencia_mock("550e8400-e29b-41d4-a716-446655440000")
    mock_db.query.return_value.filter.return_value.first.return_value = preferencia

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.put(
            "/colaboracao/preferencias/550e8400-e29b-41d4-a716-446655440000/desativar-todas",
            json={"ativas": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notificacoes_ativas"] is False
        mock_db.commit.assert_called()
    finally:
        app.dependency_overrides.clear()


def test_reativar_notificacoes():
    mock_db = MagicMock()
    preferencia = _criar_preferencia_mock("550e8400-e29b-41d4-a716-446655440000")
    preferencia.notificacoes_ativas = False
    mock_db.query.return_value.filter.return_value.first.return_value = preferencia

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.put(
            "/colaboracao/preferencias/550e8400-e29b-41d4-a716-446655440000/desativar-todas",
            json={"ativas": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notificacoes_ativas"] is True
    finally:
        app.dependency_overrides.clear()
