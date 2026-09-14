from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from auth.main import app
from auth.routes import get_db as get_db_ref
from auth.models.usuario import Usuario
from auth.security import hash_senha

client = TestClient(app)


def _make_mock_db():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    return mock_db


def _criar_usuario(overrides=None) -> Usuario:
    kwargs = {
        "id": uuid.uuid4(),
        "nome": "Teste User",
        "email": "teste@email.com",
        "senha_hash": None,
        "provider": "local",
        "status": "ativo",
        "lgpd_accepted_at": None,
        "account_linking_pending": 0,
    }
    if overrides:
        kwargs.update(overrides)
    return Usuario(**kwargs)


def test_login_google_sucesso_novo_usuario():
    mock_db = _make_mock_db()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    mock_token_info = {
        "email": "novo@email.com",
        "nome": "Novo User",
        "google_id": "google-user-456",
        "picture": "https://example.com/avatar.png",
    }

    app.dependency_overrides[get_db_ref] = lambda: mock_db
    with patch("auth.routes.validar_token_google", new_callable=AsyncMock) as mock_validar:
        mock_validar.return_value = mock_token_info
        try:
            response = client.post("/auth/login/google", json={
                "id_token": "fake-google-token",
            })
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
            assert data["account_linking_pending"] is False
            assert data["account_linking_required"] is False
            assert mock_db.add.call_args is not None
            add_calls = [call for call in mock_db.add.call_args_list if call.args and isinstance(call.args[0], Usuario)]
            assert len(add_calls) > 0
            usuario_criado = add_calls[0].args[0]
            assert usuario_criado.provider == "google.com"
            assert usuario_criado.avatar_url == "https://example.com/avatar.png"
        finally:
            app.dependency_overrides.pop(get_db_ref, None)


def test_login_google_sucesso_usuario_existente():
    usuario = _criar_usuario()
    mock_db = _make_mock_db()
    mock_db.query.return_value.filter.return_value.first.return_value = usuario
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    mock_token_info = {
        "email": "teste@email.com",
        "nome": "Teste User",
        "google_id": "google-user-123",
        "picture": "https://example.com/avatar.png",
    }

    app.dependency_overrides[get_db_ref] = lambda: mock_db
    with patch("auth.routes.validar_token_google", new_callable=AsyncMock) as mock_validar:
        mock_validar.return_value = mock_token_info
        try:
            response = client.post("/auth/login/google", json={
                "id_token": "fake-google-token",
            })
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["account_linking_pending"] is False
            assert mock_db.commit.call_args is not None
            assert usuario.senha_hash is None
            assert usuario.google_id == "google-user-123"
            assert usuario.provider == "google.com"
            assert usuario.avatar_url == "https://example.com/avatar.png"
        finally:
            app.dependency_overrides.pop(get_db_ref, None)


def test_login_google_account_linking_necessario():
    usuario = _criar_usuario(overrides={"senha_hash": hash_senha("senha123"), "provider": "local"})
    mock_db = _make_mock_db()
    mock_db.query.return_value.filter.return_value.first.return_value = usuario
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    mock_token_info = {
        "email": "teste@email.com",
        "nome": "Teste User",
        "google_id": "google-user-789",
        "picture": "https://example.com/avatar.png",
    }

    app.dependency_overrides[get_db_ref] = lambda: mock_db
    with patch("auth.routes.validar_token_google", new_callable=AsyncMock) as mock_validar:
        mock_validar.return_value = mock_token_info
        try:
            response = client.post("/auth/login/google", json={
                "id_token": "fake-google-token",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["account_linking_pending"] is True
            assert data["account_linking_required"] is True
            assert data["access_token"] == ""
            assert data["refresh_token"] == ""
            assert usuario.account_linking_pending == 1
            # google_id/provider/avatar_url só devem ser gravados na
            # confirmação (/link-google/confirmar), não nessa primeira
            # chamada — o vínculo ainda não foi confirmado pelo usuário.
            assert usuario.google_id is None
            assert usuario.provider == "local"
            assert usuario.avatar_url is None
        finally:
            app.dependency_overrides.pop(get_db_ref, None)


def test_login_google_token_invalido():
    mock_db = _make_mock_db()

    app.dependency_overrides[get_db_ref] = lambda: mock_db
    with patch("auth.routes.validar_token_google", new_callable=AsyncMock) as mock_validar:
        mock_validar.side_effect = Exception("Token inválido")
        try:
            response = client.post("/auth/login/google", json={
                "id_token": "fake-google-token",
            })
            assert response.status_code == 401
            assert "Token Google inválido" in response.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_db_ref, None)


def test_confirmar_link_google_sucesso():
    usuario = _criar_usuario(overrides={"senha_hash": hash_senha("senha123"), "account_linking_pending": 1})
    mock_db = _make_mock_db()
    mock_db.query.return_value.filter.return_value.first.return_value = usuario
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    mock_token_info = {
        "email": "teste@email.com",
        "nome": "Teste User",
        "google_id": "google-user-789",
        "picture": "https://example.com/avatar.png",
    }

    app.dependency_overrides[get_db_ref] = lambda: mock_db
    with patch("auth.routes.validar_token_google", new_callable=AsyncMock) as mock_validar:
        mock_validar.return_value = mock_token_info
        try:
            response = client.post("/auth/link-google/confirmar", json={
                "id_token": "fake-google-token",
                "email": "teste@email.com",
                "google_id": "google-user-789",
            })
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert usuario.senha_hash is None
            assert usuario.account_linking_pending == 0
        finally:
            app.dependency_overrides.pop(get_db_ref, None)


def test_confirmar_link_google_sem_ligacao_pendente():
    usuario = _criar_usuario()
    mock_db = _make_mock_db()
    mock_db.query.return_value.filter.return_value.first.return_value = usuario

    app.dependency_overrides[get_db_ref] = lambda: mock_db
    with patch("auth.routes.validar_token_google", new_callable=AsyncMock) as mock_validar:
        mock_validar.return_value = {
            "email": "teste@email.com",
            "nome": "Teste User",
            "google_id": "google-user-999",
        }
        try:
            response = client.post("/auth/link-google/confirmar", json={
                "id_token": "fake-google-token",
                "email": "teste@email.com",
                "google_id": "google-user-999",
            })
            assert response.status_code == 404
            assert "Nenhuma conta aguardando vinculação" in response.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_db_ref, None)


def test_confirmar_link_google_dados_nao_conferem():
    usuario = _criar_usuario(overrides={"senha_hash": hash_senha("senha123"), "account_linking_pending": 1})
    mock_db = _make_mock_db()
    mock_db.query.return_value.filter.return_value.first.return_value = usuario

    app.dependency_overrides[get_db_ref] = lambda: mock_db
    with patch("auth.routes.validar_token_google", new_callable=AsyncMock) as mock_validar:
        mock_validar.return_value = {
            "email": "outro@email.com",
            "nome": "Outro User",
            "google_id": "google-user-different",
        }
        try:
            response = client.post("/auth/link-google/confirmar", json={
                "id_token": "fake-google-token",
                "email": "teste@email.com",
                "google_id": "google-user-789",
            })
            assert response.status_code == 400
            assert "não conferem" in response.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_db_ref, None)


def test_login_google_conta_inativa_com_linking():
    usuario = _criar_usuario(overrides={"senha_hash": hash_senha("senha123"), "status": "inativo", "account_linking_pending": 0})
    mock_db = _make_mock_db()
    mock_db.query.return_value.filter.return_value.first.return_value = usuario

    app.dependency_overrides[get_db_ref] = lambda: mock_db
    with patch("auth.routes.validar_token_google", new_callable=AsyncMock) as mock_validar:
        mock_validar.return_value = {
            "email": "teste@email.com",
            "nome": "Teste User",
            "google_id": "google-user-999",
        }
        try:
            response = client.post("/auth/login/google", json={
                "id_token": "fake-google-token",
            })
            assert response.status_code == 403
            assert "Conta inativa" in response.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_db_ref, None)