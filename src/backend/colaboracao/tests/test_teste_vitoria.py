from fastapi.testclient import TestClient

from colaboracao.main import app

client = TestClient(app)


def test_teste_vitoria():
    response = client.get("/colaboracao/teste-vitoria")
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "service": "colaboracao",
        "autor": "Vitoria-Albuquerque",
        "mensagem": "hello world",
    }
