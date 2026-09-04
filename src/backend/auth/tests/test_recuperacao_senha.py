import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from auth.main import app
from auth.models.usuario import Usuario
from auth.models.token_reset_senha import TokenResetSenha
from auth.security import hash_senha
from shared.database import get_db

client = TestClient(app)


def _criar_usuario_mock() -> Usuario:
    return Usuario(
        id=uuid.uuid4(),
        nome="Teste User",
        email="teste@email.com",
        senha_hash=hash_senha("senha123"),
        lgpd_accepted_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )


def _override_get_db(mock_db):
    def _generator():
        yield mock_db
    return _generator()


@patch("auth.routes.enviar_email_reset_senha", return_value=True)
def test_esqueci_senha_email_cadastrado(mock_enviar_email):
    mock_db = MagicMock()
    usuario = _criar_usuario_mock()
    mock_db.query.return_value.filter.return_value.first.return_value = usuario

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            "/auth/esqueci-senha",
            json={"email": "teste@email.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "cadastrado" in data["mensagem"]
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
    finally:
        app.dependency_overrides.clear()


def test_esqueci_senha_email_nao_cadastrado():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            "/auth/esqueci-senha",
            json={"email": "inexistente@email.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "cadastrado" in data["mensagem"]
        mock_db.add.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_esqueci_senha_email_invalido():
    response = client.post(
        "/auth/esqueci-senha",
        json={"email": "email-invalido"},
    )

    assert response.status_code == 422


def test_redefinir_senha_sucesso():
    mock_db = MagicMock()
    usuario = _criar_usuario_mock()
    token_obj = TokenResetSenha(
        id=uuid.uuid4(),
        usuario_id=usuario.id,
        token="token-valido-123",
        usado=False,
        criado_em=datetime.now(timezone.utc),
        expira_em=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    def query_side_effect(model):
        mock_q = MagicMock()
        if model == TokenResetSenha:
            mock_q.filter.return_value.first.return_value = token_obj
        elif model == Usuario:
            mock_q.filter.return_value.first.return_value = usuario
        return mock_q

    mock_db.query.side_effect = query_side_effect

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            "/auth/redefinir-senha",
            json={
                "token": "token-valido-123",
                "nova_senha": "novaSenha123",
                "confirmacao_senha": "novaSenha123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "sucesso" in data["mensagem"]
        assert token_obj.usado is True
        mock_db.commit.assert_called()
    finally:
        app.dependency_overrides.clear()


def test_redefinir_senha_senhas_nao_coincidem():
    response = client.post(
        "/auth/redefinir-senha",
        json={
            "token": "qualquer-token",
            "nova_senha": "novaSenha123",
            "confirmacao_senha": "outraSenha123",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "coincidem" in data["detail"]


def test_redefinir_senha_senha_curta():
    response = client.post(
        "/auth/redefinir-senha",
        json={
            "token": "qualquer-token",
            "nova_senha": "curta",
            "confirmacao_senha": "curta",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "minimo" in data["detail"]


def test_redefinir_senha_token_invalido():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            "/auth/redefinir-senha",
            json={
                "token": "token-inexistente",
                "nova_senha": "novaSenha123",
                "confirmacao_senha": "novaSenha123",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "valido" in data["detail"]
    finally:
        app.dependency_overrides.clear()


def test_redefinir_senha_token_expirado():
    mock_db = MagicMock()

    token_obj = TokenResetSenha(
        id=uuid.uuid4(),
        usuario_id=uuid.uuid4(),
        token="token-expirado",
        usado=False,
        criado_em=datetime.now(timezone.utc) - timedelta(hours=2),
        expira_em=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    mock_db.query.return_value.filter.return_value.first.return_value = token_obj

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            "/auth/redefinir-senha",
            json={
                "token": "token-expirado",
                "nova_senha": "novaSenha123",
                "confirmacao_senha": "novaSenha123",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "valido" in data["detail"]
    finally:
        app.dependency_overrides.clear()


def test_redefinir_senha_token_ja_usado():
    mock_db = MagicMock()

    token_obj = TokenResetSenha(
        id=uuid.uuid4(),
        usuario_id=uuid.uuid4(),
        token="token-ja-usado",
        usado=True,
        criado_em=datetime.now(timezone.utc),
        expira_em=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    mock_db.query.return_value.filter.return_value.first.return_value = token_obj

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            "/auth/redefinir-senha",
            json={
                "token": "token-ja-usado",
                "nova_senha": "novaSenha123",
                "confirmacao_senha": "novaSenha123",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "valido" in data["detail"]
    finally:
        app.dependency_overrides.clear()
