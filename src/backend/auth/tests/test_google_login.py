from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from auth.main import app
from auth.models.usuario import Usuario
from auth.security import hash_senha
from shared.database import get_db

client = TestClient(app)


def _override_get_db(mock_db):
    def _generator():
        yield mock_db
    return _generator()


def _criar_usuario() -> Usuario:
    return Usuario(
        id=uuid.uuid4(),
        nome="Teste User",
        email="teste@email.com",
        senha_hash=hash_senha("senha123"),
        provider="local",
        lgpd_accepted_at=None,
    )


def test_login_google_sucesso_usuario_existente():
    usuario = _criar_usuario()

    mock_db = MagicMock()

    def mock_query(model):
        m = MagicMock()
        m.filter.return_value.first.return_value = usuario
        return m

    mock_db.query.side_effect = mock_query

    mock_token_info = {
        "email": "teste@email.com",
        "nome": "Teste User",
        "google_id": "google-user-123",
    }

    with patch("auth.routes.validar_token_google", new_callable=AsyncMock) as mock_validar:
        mock_validar.return_value = mock_token_info
        with patch("shared.database.get_db", return_value=_override_get_db(mock_db)):
            response = client.post("/auth/login/google", json={
                "id_token": "fake-google-token",
            })
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"


def test_login_google_sucesso_novo_usuario():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    mock_token_info = {
        "email": "novo@email.com",
        "nome": "Novo User",
        "google_id": "google-user-456",
    }

    with patch("auth.routes.validar_token_google", new_callable=AsyncMock) as mock_validar:
        mock_validar.return_value = mock_token_info
        with patch("shared.database.get_db", return_value=_override_get_db(mock_db)):
            response = client.post("/auth/login/google", json={
                "id_token": "fake-google-token",
            })
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"


def test_login_google_token_invalido():
    mock_db = MagicMock()

    with patch("auth.routes.validar_token_google", new_callable=AsyncMock) as mock_validar:
        mock_validar.side_effect = Exception("Token inválido")
        with patch("shared.database.get_db", return_value=_override_get_db(mock_db)):
            response = client.post("/auth/login/google", json={
                "id_token": "fake-google-token",
            })
            assert response.status_code == 401
            assert "Token Google inválido" in response.json()["detail"]


