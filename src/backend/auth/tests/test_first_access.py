from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from auth.main import app
from auth.models.usuario import Usuario
from auth.security import criar_access_token
from shared.database import get_db

client = TestClient(app)


def _criar_usuario_mock(first_access: bool = True) -> Usuario:
    usuario = Usuario(
        nome="Teste User",
        email="teste@email.com",
        senha_hash="hash123",
        lgpd_accepted_at="2026-01-01T00:00:00",
        status="ativo",
        first_access=first_access,
    )
    usuario.id = "550e8400-e29b-41d4-a716-446655440000"
    return usuario


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------

def test_me_retorna_first_access_true_por_padrao():
    mock_db = MagicMock()
    usuario = _criar_usuario_mock(first_access=True)
    mock_db.query.return_value.filter.return_value.first.return_value = usuario

    token = "dummy-token"
    # O decodificar_access_token valida assinatura, entao mockamos
    import auth.routes
    original_decodificar = auth.routes.decodificar_access_token
    auth.routes.decodificar_access_token = lambda t: {"sub": "550e8400-e29b-41d4-a716-446655440000"}

    mock_db.query.return_value.filter.return_value.first.return_value = usuario

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            "/auth/me",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_access"] is True
    finally:
        app.dependency_overrides.clear()
        auth.routes.decodificar_access_token = original_decodificar


def test_me_retorna_first_access_false():
    mock_db = MagicMock()
    usuario = _criar_usuario_mock(first_access=False)
    mock_db.query.return_value.filter.return_value.first.return_value = usuario

    token = "dummy-token"
    import auth.routes
    original_decodificar = auth.routes.decodificar_access_token
    auth.routes.decodificar_access_token = lambda t: {"sub": "550e8400-e29b-41d4-a716-446655440000"}

    mock_db.query.return_value.filter.return_value.first.return_value = usuario

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            "/auth/me",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_access"] is False
    finally:
        app.dependency_overrides.clear()
        auth.routes.decodificar_access_token = original_decodificar


# ---------------------------------------------------------------------------
# PUT /me/first-access
# ---------------------------------------------------------------------------

def test_atualizar_first_access_para_false():
    mock_db = MagicMock()
    usuario = _criar_usuario_mock(first_access=True)
    mock_db.query.return_value.filter.return_value.first.return_value = usuario

    token = "dummy-token"
    import auth.routes
    original_decodificar = auth.routes.decodificar_access_token
    auth.routes.decodificar_access_token = lambda t: {"sub": "550e8400-e29b-41d4-a716-446655440000"}

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.put(
            "/auth/me/first-access",
            json={"first_access": False},
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_access"] is False
        mock_db.commit.assert_called()
    finally:
        app.dependency_overrides.clear()
        auth.routes.decodificar_access_token = original_decodificar


def test_atualizar_first_access_para_true():
    mock_db = MagicMock()
    usuario = _criar_usuario_mock(first_access=False)
    mock_db.query.return_value.filter.return_value.first.return_value = usuario

    token = "dummy-token"
    import auth.routes
    original_decodificar = auth.routes.decodificar_access_token
    auth.routes.decodificar_access_token = lambda t: {"sub": "550e8400-e29b-41d4-a716-446655440000"}

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.put(
            "/auth/me/first-access",
            json={"first_access": True},
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_access"] is True
    finally:
        app.dependency_overrides.clear()
        auth.routes.decodificar_access_token = original_decodificar


def test_atualizar_first_access_sem_token():
    response = client.put(
        "/auth/me/first-access",
        json={"first_access": False},
    )
    assert response.status_code == 401


def test_atualizar_first_access_token_invalido():
    import auth.routes
    original_decodificar = auth.routes.decodificar_access_token
    auth.routes.decodificar_access_token = lambda t: None

    response = client.put(
        "/auth/me/first-access",
        json={"first_access": False},
        cookies={"access_token": "token-invalido"},
    )
    assert response.status_code == 401
    auth.routes.decodificar_access_token = original_decodificar