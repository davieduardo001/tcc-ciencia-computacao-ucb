from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_hello_gateway():
    response = client.get("/gateway/hello")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "gateway"
    assert data["status"] == "ok"
