from fastapi.testclient import TestClient

from auth.main import app

client = TestClient(app)


def _payload(**extra):
    base = {
        "nome": "Usuária Termos",
        "email": "termos@teste.com",
        "senha": "senha123",
    }
    base.update(extra)
    return base


def test_registrar_com_termos_false_retorna_422():
    response = client.post(
        "/auth/registrar",
        json=_payload(email="termos-false@teste.com", termos_aceitos=False),
    )

    assert response.status_code == 422


def test_registrar_sem_campo_termos_retorna_422():
    response = client.post(
        "/auth/registrar",
        json=_payload(email="termos-ausente@teste.com"),
    )

    assert response.status_code == 422


def test_registrar_com_termos_false_nao_cria_a_conta():
    email = "termos-nao-cria@teste.com"
    client.post("/auth/registrar", json=_payload(email=email, termos_aceitos=False))

    login = client.post("/auth/login", json={"email": email, "senha": "senha123"})

    assert login.status_code == 401


def test_registrar_com_termos_true_continua_funcionando():
    response = client.post(
        "/auth/registrar",
        json=_payload(email="termos-true@teste.com", termos_aceitos=True),
    )

    assert response.status_code == 200
