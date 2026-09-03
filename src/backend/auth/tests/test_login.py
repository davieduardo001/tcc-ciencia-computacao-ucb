from fastapi.testclient import TestClient

from auth.main import app

client = TestClient(app)


def test_login_sucesso():
    response = client.post("/auth/registrar", json={
        "nome": "Ana Passageira",
        "email": "ana@teste.com",
        "senha": "senha123",
        "termos_aceitos": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "ana@teste.com"

    login_response = client.post("/auth/login", json={
        "email": "ana@teste.com",
        "senha": "senha123",
    })
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_senha_incorreta():
    client.post("/auth/registrar", json={
        "nome": "Carlos",
        "email": "carlos@teste.com",
        "senha": "senha123",
        "termos_aceitos": True,
    })

    response = client.post("/auth/login", json={
        "email": "carlos@teste.com",
        "senha": "senha_errada",
    })
    assert response.status_code == 401
    assert "senha inválidos" in response.json()["detail"].lower() or "inválidos" in response.json()["detail"].lower()


def test_login_usuario_nao_encontrado():
    response = client.post("/auth/login", json={
        "email": "inexistente@teste.com",
        "senha": "qualquer",
    })
    assert response.status_code == 401
    assert "inválidos" in response.json()["detail"].lower()


def test_login_conta_bloqueada():
    client.post("/auth/registrar", json={
        "nome": "Bloqueio Teste",
        "email": "bloqueio@teste.com",
        "senha": "senha123",
        "termos_aceitos": True,
    })

    for _ in range(5):
        client.post("/auth/login", json={
            "email": "bloqueio@teste.com",
            "senha": "errada",
        })

    response = client.post("/auth/login", json={
        "email": "bloqueio@teste.com",
        "senha": "senha123",
    })
    assert response.status_code == 423


def test_registrar_email_duplicado():
    client.post("/auth/registrar", json={
        "nome": "Duplo",
        "email": "duplo@teste.com",
        "senha": "senha123",
        "termos_aceitos": True,
    })

    response = client.post("/auth/registrar", json={
        "nome": "Duplo 2",
        "email": "duplo@teste.com",
        "senha": "senha456",
        "termos_aceitos": True,
    })
    assert response.status_code == 409


def test_registro_sucesso():
    response = client.post("/auth/registrar", json={
        "nome": "Novo Usuario",
        "email": "novo@teste.com",
        "senha": "senha123",
        "termos_aceitos": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Novo Usuario"
    assert data["email"] == "novo@teste.com"