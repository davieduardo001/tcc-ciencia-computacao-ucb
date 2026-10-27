"""Testes de integração — US #26: Confirmar Ocorrência.

Cobre todos os cenários e critérios de aceite:
  - Confirmação válida de outro usuário
  - Persistência e contagem
  - Transição de status ao atingir o limite
  - Impedimento ao autor original
  - Impedimento de duplicata (via mock do IntegrityError)
  - Ocorrência inexistente
  - Ocorrência expirada/inativa
  - Sem autenticação
  - Preservação dos testes de US #22 (regressão)

Banco: SQLite in-memory para os testes de GET/integração;
MagicMock para os testes de regra de negócio do POST
(mesmo padrão de test_ocorrencias.py e test_favoritos.py).
"""
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from colaboracao.main import app
from colaboracao.models import Ocorrencia, ConfirmacaoOcorrencia
from shared.database import get_db

client = TestClient(app)

USUARIO_A = str(uuid.uuid4())  # autor da ocorrência
USUARIO_B = str(uuid.uuid4())  # confirma
USUARIO_C = str(uuid.uuid4())  # confirma
USUARIO_D = str(uuid.uuid4())  # confirma — atinge o limite

HEADERS_A = {"X-User-Id": USUARIO_A}
HEADERS_B = {"X-User-Id": USUARIO_B}
HEADERS_C = {"X-User-Id": USUARIO_C}
HEADERS_D = {"X-User-Id": USUARIO_D}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ocorrencia_mock(
    usuario_id: str = USUARIO_A,
    status: str = "pendente",
    contador: int = 0,
    expirada: bool = False,
    tipo: str = "atraso",
) -> Ocorrencia:
    agora = datetime.utcnow()
    oc = Ocorrencia()
    oc.id = uuid.uuid4()
    oc.usuario_id = uuid.UUID(usuario_id)
    oc.linha_numero = "0.110"
    oc.tipo = tipo
    oc.status = status
    oc.contador_confirmacoes = contador
    oc.criado_em = agora - timedelta(minutes=5)
    oc.expira_em = (agora - timedelta(minutes=1)) if expirada else (agora + timedelta(minutes=25))
    return oc


def _setup_mock_db(ocorrencia: Ocorrencia | None):
    """Configura o banco com mock retornando a ocorrência indicada."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = ocorrencia
    app.dependency_overrides[get_db] = lambda: mock_db
    return mock_db


# ---------------------------------------------------------------------------
# Banco SQLite real para testes de integração
# ---------------------------------------------------------------------------


def _banco_real(*registros):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Ocorrencia.__table__.create(bind=engine)
    ConfirmacaoOcorrencia.__table__.create(bind=engine)
    # expire_on_commit=False: mantém atributos acessíveis após a sessão fechar.
    # Necessário porque o TestClient e os testes acessam os atributos das
    # instâncias após o commit/close da sessão de setup.
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    sessao = SessionLocal()
    sessao.add_all(registros)
    sessao.commit()
    sessao.close()

    def _get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    return SessionLocal


def _ocorrencia_real(
    usuario_id: str = USUARIO_A,
    status: str = "pendente",
    contador: int = 0,
    expira_em_min: int = 25,
) -> Ocorrencia:
    agora = datetime.utcnow()
    return Ocorrencia(
        id=uuid.uuid4(),
        usuario_id=uuid.UUID(usuario_id),
        linha_numero="0.110",
        tipo="atraso",
        descricao=None,
        local=None,
        status=status,
        contador_confirmacoes=contador,
        criado_em=agora - timedelta(minutes=5),
        expira_em=agora + timedelta(minutes=expira_em_min),
    )


# ---------------------------------------------------------------------------
# POST /ocorrencias/{id}/confirmar — testes com mock DB
# ---------------------------------------------------------------------------


def test_confirmar_sem_autenticacao():
    """401 quando não há X-User-Id (Gateway rejeitaria antes, mas o serviço também bloqueia)."""
    oc = _ocorrencia_mock()
    _setup_mock_db(oc)
    try:
        response = client.post(f"/colaboracao/ocorrencias/{oc.id}/confirmar")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_confirmar_ocorrencia_inexistente():
    """404 quando a ocorrência não existe."""
    _setup_mock_db(None)
    try:
        response = client.post(
            f"/colaboracao/ocorrencias/{uuid.uuid4()}/confirmar",
            headers=HEADERS_B,
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_confirmar_ocorrencia_expirada():
    """422 para ocorrência já expirada."""
    oc = _ocorrencia_mock(expirada=True)
    _setup_mock_db(oc)
    try:
        response = client.post(
            f"/colaboracao/ocorrencias/{oc.id}/confirmar",
            headers=HEADERS_B,
        )
        assert response.status_code == 422
        assert response.json()["detail"] == "ocorrencia_inativa"
    finally:
        app.dependency_overrides.clear()


def test_confirmar_ocorrencia_status_expirada():
    """422 quando status == 'expirada' (mesmo que expira_em ainda seja futuro)."""
    oc = _ocorrencia_mock(status="expirada")
    # Garante que expira_em seja no futuro mas status = expirada
    oc.expira_em = datetime.utcnow() + timedelta(minutes=10)
    _setup_mock_db(oc)
    try:
        response = client.post(
            f"/colaboracao/ocorrencias/{oc.id}/confirmar",
            headers=HEADERS_B,
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_autor_nao_pode_confirmar_propria_ocorrencia():
    """403 quando o autor tenta confirmar a própria ocorrência."""
    oc = _ocorrencia_mock(usuario_id=USUARIO_A)
    _setup_mock_db(oc)
    try:
        response = client.post(
            f"/colaboracao/ocorrencias/{oc.id}/confirmar",
            headers=HEADERS_A,  # mesmo usuário que criou
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "autor_nao_pode_confirmar"
    finally:
        app.dependency_overrides.clear()


def test_confirmacao_duplicada_retorna_409():
    """409 quando o banco detecta UNIQUE violation (confirmação duplicada)."""
    oc = _ocorrencia_mock(usuario_id=USUARIO_A)
    mock_db = _setup_mock_db(oc)
    mock_db.flush.side_effect = IntegrityError("", {}, Exception())
    try:
        response = client.post(
            f"/colaboracao/ocorrencias/{oc.id}/confirmar",
            headers=HEADERS_B,
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "confirmacao_duplicada"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /ocorrencias/{id}/confirmar — testes com banco SQLite real
# ---------------------------------------------------------------------------


def test_confirmar_ocorrencia_sucesso_persiste_e_retorna_dados():
    """Cenário 1: confirmação válida persiste e retorna dados corretos."""
    oc = _ocorrencia_real(usuario_id=USUARIO_A)
    SessionLocal = _banco_real(oc)
    try:
        response = client.post(
            f"/colaboracao/ocorrencias/{oc.id}/confirmar",
            headers=HEADERS_B,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["ocorrencia_id"] == str(oc.id)
        assert data["status"] == "pendente"  # ainda não atingiu 3
        assert data["contador_confirmacoes"] == 1

        # Verifica persistência
        db = SessionLocal()
        confirmacoes = db.query(ConfirmacaoOcorrencia).filter(
            ConfirmacaoOcorrencia.ocorrencia_id == oc.id
        ).all()
        assert len(confirmacoes) == 1
        assert confirmacoes[0].usuario_id == uuid.UUID(USUARIO_B)
        db.close()
    finally:
        app.dependency_overrides.clear()


def test_status_permanece_pendente_antes_do_limite():
    """Status continua 'pendente' com 1 e 2 confirmações."""
    oc = _ocorrencia_real(usuario_id=USUARIO_A)
    _banco_real(oc)
    try:
        r1 = client.post(f"/colaboracao/ocorrencias/{oc.id}/confirmar", headers=HEADERS_B)
        assert r1.json()["status"] == "pendente"
        assert r1.json()["contador_confirmacoes"] == 1

        r2 = client.post(f"/colaboracao/ocorrencias/{oc.id}/confirmar", headers=HEADERS_C)
        assert r2.json()["status"] == "pendente"
        assert r2.json()["contador_confirmacoes"] == 2
    finally:
        app.dependency_overrides.clear()


def test_status_muda_para_confirmada_ao_atingir_limite():
    """Cenário 1: ao atingir 3 confirmações, status muda para 'confirmada'."""
    oc = _ocorrencia_real(usuario_id=USUARIO_A)
    _banco_real(oc)
    try:
        client.post(f"/colaboracao/ocorrencias/{oc.id}/confirmar", headers=HEADERS_B)
        client.post(f"/colaboracao/ocorrencias/{oc.id}/confirmar", headers=HEADERS_C)
        r3 = client.post(f"/colaboracao/ocorrencias/{oc.id}/confirmar", headers=HEADERS_D)

        assert r3.status_code == 200
        data = r3.json()
        assert data["status"] == "confirmada"
        assert data["contador_confirmacoes"] == 3
        assert "comunidade" in data["mensagem"]
    finally:
        app.dependency_overrides.clear()


def test_confirmacao_duplicada_banco_real_retorna_409():
    """O mesmo usuário não pode confirmar duas vezes — banco rejeita com 409."""
    oc = _ocorrencia_real(usuario_id=USUARIO_A)
    _banco_real(oc)
    try:
        r1 = client.post(f"/colaboracao/ocorrencias/{oc.id}/confirmar", headers=HEADERS_B)
        assert r1.status_code == 200

        r2 = client.post(f"/colaboracao/ocorrencias/{oc.id}/confirmar", headers=HEADERS_B)
        assert r2.status_code == 409
        assert r2.json()["detail"] == "confirmacao_duplicada"
    finally:
        app.dependency_overrides.clear()


def test_contagem_nao_sobe_apos_duplicata():
    """Duplicata rejeitada não altera o contador nem o status."""
    oc = _ocorrencia_real(usuario_id=USUARIO_A)
    SessionLocal = _banco_real(oc)
    try:
        client.post(f"/colaboracao/ocorrencias/{oc.id}/confirmar", headers=HEADERS_B)
        client.post(f"/colaboracao/ocorrencias/{oc.id}/confirmar", headers=HEADERS_B)  # duplicata

        db = SessionLocal()
        ocorrencia_atualizada = db.get(Ocorrencia, oc.id)
        assert ocorrencia_atualizada.contador_confirmacoes == 1
        db.close()
    finally:
        app.dependency_overrides.clear()


def test_autor_nao_pode_confirmar_banco_real():
    """Cenário 2: autor não pode confirmar — banco real."""
    oc = _ocorrencia_real(usuario_id=USUARIO_A)
    _banco_real(oc)
    try:
        response = client.post(
            f"/colaboracao/ocorrencias/{oc.id}/confirmar",
            headers=HEADERS_A,
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_confirmar_ocorrencia_expirada_banco_real():
    """Cenário 3: ocorrência expirada não pode ser confirmada."""
    oc = _ocorrencia_real(usuario_id=USUARIO_A, expira_em_min=-5)
    _banco_real(oc)
    try:
        response = client.post(
            f"/colaboracao/ocorrencias/{oc.id}/confirmar",
            headers=HEADERS_B,
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_dados_retornados_correspondem_ao_estado_persistido():
    """Os dados da resposta refletem exatamente o que foi gravado no banco."""
    oc = _ocorrencia_real(usuario_id=USUARIO_A)
    SessionLocal = _banco_real(oc)
    try:
        response = client.post(
            f"/colaboracao/ocorrencias/{oc.id}/confirmar",
            headers=HEADERS_B,
        )
        data = response.json()

        db = SessionLocal()
        ocorrencia_banco = db.get(Ocorrencia, oc.id)
        assert data["status"] == ocorrencia_banco.status
        assert data["contador_confirmacoes"] == ocorrencia_banco.contador_confirmacoes
        db.close()
    finally:
        app.dependency_overrides.clear()


def test_confirmacoes_simultâneas_de_usuarios_diferentes_nao_bagunçam_contagem():
    """
    Confirmações de B e C em sequência rápida devem resultar em contador = 2.
    (Concorrência real requereria threads; aqui testamos a consistência sequencial
    que o SQLite in-memory garante — o banco production usa transações isoladas.)
    """
    oc = _ocorrencia_real(usuario_id=USUARIO_A)
    _banco_real(oc)
    try:
        r_b = client.post(f"/colaboracao/ocorrencias/{oc.id}/confirmar", headers=HEADERS_B)
        r_c = client.post(f"/colaboracao/ocorrencias/{oc.id}/confirmar", headers=HEADERS_C)
        assert r_b.status_code == 200
        assert r_c.status_code == 200
        # C retorna o estado depois de B ter confirmado
        assert r_c.json()["contador_confirmacoes"] == 2
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Regressão US #22 — Worker não deve ser afetado
# ---------------------------------------------------------------------------


def test_regressao_us22_worker_continua_funcionando():
    """O Worker de notificações da US #22 não foi afetado."""
    response = client.post("/colaboracao/notificacoes/processar")
    assert response.status_code == 200
    assert response.json()["status"] == "ciclo_processado"
