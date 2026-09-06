from authlib.integrations.httpx_client import AsyncOAuth2Client
from shared.config import get_settings

settings = get_settings()


async def validar_token_google(id_token: str) -> dict:
    async with AsyncOAuth2Client() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
        )
        resp.raise_for_status()
        dados = resp.json()

    if dados.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise ValueError("Client ID inválido")

    return {
        "email": dados.get("email"),
        "nome": dados.get("name"),
        "google_id": dados.get("sub"),
    }