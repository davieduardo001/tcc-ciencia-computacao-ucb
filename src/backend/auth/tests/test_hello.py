from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_hello_auth():
    response = client.get("/auth/hello")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "auth"
    assert data["status"] == "ok"
