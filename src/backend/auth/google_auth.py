import httpx
from shared.config import get_settings

settings = get_settings()


async def validar_token_google(id_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
        )
        resp.raise_for_status()
        dados = resp.json()

    if dados.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise ValueError("Client ID inválido")

    if dados.get("email_verified") != "true":
        raise ValueError("E-mail do Google não verificado")

    return {
        "email": dados.get("email"),
        "nome": dados.get("name"),
        "google_id": dados.get("sub"),
        "picture": dados.get("picture"),
    }