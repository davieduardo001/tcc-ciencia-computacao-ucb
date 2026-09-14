import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from auth.google_auth import validar_token_google


def _mock_tokeninfo_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=payload)
    return resp


def test_validar_token_google_email_nao_verificado_rejeitado():
    payload = {
        "aud": "client-id-valido",
        "email": "teste@email.com",
        "email_verified": "false",
        "name": "Teste User",
        "sub": "google-user-123",
    }

    with patch("auth.google_auth.settings") as mock_settings:
        mock_settings.GOOGLE_CLIENT_ID = "client-id-valido"
        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_mock_tokeninfo_response(payload))):
            with pytest.raises(ValueError, match="não verificado"):
                asyncio.run(validar_token_google("fake-token"))


def test_validar_token_google_email_verificado_aceito():
    payload = {
        "aud": "client-id-valido",
        "email": "teste@email.com",
        "email_verified": "true",
        "name": "Teste User",
        "sub": "google-user-123",
        "picture": "https://example.com/avatar.png",
    }

    with patch("auth.google_auth.settings") as mock_settings:
        mock_settings.GOOGLE_CLIENT_ID = "client-id-valido"
        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_mock_tokeninfo_response(payload))):
            dados = asyncio.run(validar_token_google("fake-token"))

    assert dados["email"] == "teste@email.com"
    assert dados["google_id"] == "google-user-123"
