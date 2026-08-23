import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth.main import app
from models.base import Base
from shared.database import get_db

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def banco_de_dados():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _payload(**overrides):
    dados = {
        "nome": "Ana Passageira",
        "email": "ana@example.com",
        "senha": "senha123",
        "termos_aceitos": True,
    }
    dados.update(overrides)
    return dados


def test_registro_com_dados_validos():
    response = client.post("/auth/registro", json=_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Ana Passageira"
    assert data["email"] == "ana@example.com"
    assert data["mensagem"] == "Verifique seu e-mail para confirmar a conta."


def test_registro_email_ja_existente():
    client.post("/auth/registro", json=_payload())
    response = client.post("/auth/registro", json=_payload(nome="Outra Pessoa"))
    assert response.status_code == 409
    assert "já está em uso" in response.json()["detail"]


def test_registro_nome_vazio():
    response = client.post("/auth/registro", json=_payload(nome=""))
    assert response.status_code == 422


def test_registro_email_vazio():
    response = client.post("/auth/registro", json=_payload(email=""))
    assert response.status_code == 422


def test_registro_senha_fraca():
    response = client.post("/auth/registro", json=_payload(senha="12345678"))
    assert response.status_code == 422


def test_registro_termos_nao_aceitos():
    response = client.post("/auth/registro", json=_payload(termos_aceitos=False))
    assert response.status_code == 422
