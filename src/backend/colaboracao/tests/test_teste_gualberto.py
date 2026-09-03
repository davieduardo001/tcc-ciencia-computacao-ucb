from fastapi.testclient import TestClient

from colaboracao.main import app

client = TestClient(app)


def test_teste_gualberto():
    response = client.get("/colaboracao/teste-gualberto")
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "service": "colaboracao",
        "autor": "gualbertonathalia",
        "mensagem": "hello world",
    }
