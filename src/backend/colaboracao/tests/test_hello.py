from fastapi.testclient import TestClient

from colaboracao.main import app

client = TestClient(app)


def test_hello_colaboracao():
    response = client.get("/colaboracao/hello")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "colaboracao"
    assert data["status"] == "ok"
