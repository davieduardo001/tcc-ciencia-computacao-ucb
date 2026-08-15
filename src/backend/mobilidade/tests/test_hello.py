from fastapi.testclient import TestClient

from mobilidade.main import app

client = TestClient(app)


def test_hello_mobilidade():
    response = client.get("/mobilidade/hello")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "mobilidade"
    assert data["status"] == "ok"
