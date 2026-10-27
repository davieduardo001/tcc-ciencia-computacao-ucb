from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from jose import jwt

from auth.main import app
from shared.config import get_settings

client = TestClient(app)
settings = get_settings()


def _registrar_e_logar(email: str) -> dict:
    client.post("/auth/registrar", json={
        "nome": "Usuária Refresh",
        "email": email,
        "senha": "senha123",
        "termos_aceitos": True,
    })
    login = client.post("/auth/login", json={"email": email, "senha": "senha123"})
    assert login.status_code == 200
    return login.json()


def test_refresh_com_token_valido_emite_novo_par():
    tokens = _registrar_e_logar("refresh-valido@teste.com")

    response = client.post(
        "/auth/refresh", cookies={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] != tokens["access_token"]
    assert data["refresh_token"] != tokens["refresh_token"]

    me = client.get("/auth/me", cookies={"access_token": data["access_token"]})
    assert me.status_code == 200
    assert me.json()["email"] == "refresh-valido@teste.com"


def test_refresh_rotaciona_e_o_token_antigo_deixa_de_valer():
    tokens = _registrar_e_logar("refresh-rotaciona@teste.com")
    client.post("/auth/refresh", cookies={"refresh_token": tokens["refresh_token"]})

    response = client.post(
        "/auth/refresh", cookies={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 401


def test_refresh_sem_cookie_retorna_401():
    response = client.post("/auth/refresh")

    assert response.status_code == 401


def test_refresh_com_token_invalido_retorna_401():
    response = client.post("/auth/refresh", cookies={"refresh_token": "token-invalido"})

    assert response.status_code == 401


def test_refresh_com_token_expirado_retorna_401():
    tokens = _registrar_e_logar("refresh-expirado@teste.com")
    sub = jwt.get_unverified_claims(tokens["refresh_token"])["sub"]
    expirado = jwt.encode(
        {"sub": sub, "exp": datetime.utcnow() - timedelta(minutes=1)},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = client.post("/auth/refresh", cookies={"refresh_token": expirado})

    assert response.status_code == 401


def test_refresh_apos_logout_retorna_401():
    tokens = _registrar_e_logar("refresh-logout@teste.com")
    client.post("/auth/logout", cookies={"access_token": tokens["access_token"]})

    response = client.post(
        "/auth/refresh", cookies={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 401


def test_refresh_com_assinatura_valida_mas_sem_sessao_retorna_401():
    tokens = _registrar_e_logar("refresh-sem-sessao@teste.com")
    sub = jwt.get_unverified_claims(tokens["refresh_token"])["sub"]
    avulso = jwt.encode(
        {"sub": sub, "exp": datetime.utcnow() + timedelta(days=1), "jti": "avulso"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = client.post("/auth/refresh", cookies={"refresh_token": avulso})

    assert response.status_code == 401
