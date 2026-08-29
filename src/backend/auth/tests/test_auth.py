from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth.main import app
from auth.database import get_db
from models.base import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def setup_module():
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def test_registrar_usuario():
    response = client.post(
        "/auth/registrar",
        json={
            "nome": "Teste",
            "email": "teste@email.com",
            "senha": "senha123",
        },
    )
    assert response.status_code == 201
    assert response.json()["mensagem"] == "Conta criada com sucesso. Faça login."


def test_registrar_email_duplicado():
    response = client.post(
        "/auth/registrar",
        json={
            "nome": "Teste 2",
            "email": "teste@email.com",
            "senha": "senha456",
        },
    )
    assert response.status_code == 400


def test_login_sucesso():
    response = client.post(
        "/auth/login",
        json={"email": "teste@email.com", "senha": "senha123"},
    )
    assert response.status_code == 200
    assert response.json()["mensagem"] == "Login realizado com sucesso"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_login_credenciais_invalidas():
    response = client.post(
        "/auth/login",
        json={"email": "teste@email.com", "senha": "senha_errada"},
    )
    assert response.status_code == 401


def test_me_autenticado():
    client.post(
        "/auth/login",
        json={"email": "teste@email.com", "senha": "senha123"},
    )
    response = client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "teste@email.com"


def test_me_nao_autenticado():
    client.cookies.clear()
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout():
    client.post(
        "/auth/login",
        json={"email": "teste@email.com", "senha": "senha123"},
    )
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert "access_token" not in response.cookies
    assert "refresh_token" not in response.cookies
