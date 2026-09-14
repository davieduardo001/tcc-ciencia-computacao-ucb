from fastapi.testclient import TestClient

from auth.main import app

client = TestClient(app)


def _registrar_e_logar(email: str) -> str:
    client.post("/auth/registrar", json={
        "nome": "Usuária de Teste",
        "email": email,
        "senha": "senha123",
        "termos_aceitos": True,
    })

    login_response = client.post("/auth/login", json={
        "email": email,
        "senha": "senha123",
    })
    return login_response.json()["access_token"]


def test_me_com_token_valido_retorna_dados_do_usuario():
    token = _registrar_e_logar("me-valido@teste.com")

    response = client.get("/auth/me", cookies={"access_token": token})

    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Usuária de Teste"
    assert data["email"] == "me-valido@teste.com"
    assert "id" in data


def test_me_sem_cookie_retorna_401():
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_com_token_invalido_retorna_401():
    response = client.get("/auth/me", cookies={"access_token": "token-invalido"})

    assert response.status_code == 401
