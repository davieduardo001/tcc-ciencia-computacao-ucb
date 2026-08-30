from fastapi.testclient import TestClient

from auth.main import app

client = TestClient(app)


def test_hello_auth():
    response = client.get("/auth/hello")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "auth"
    assert data["status"] == "ok"

def test_teste_brenouchihar_auth():

    response = client.get("/auth/teste-brenouchihar")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "auth"
    assert data["autor"] == "brenouchihar"
    assert data["mensagem"] == "hello world"
