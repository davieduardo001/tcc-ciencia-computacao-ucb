import uuid
from unittest.mock import MagicMock
from fastapi import Header, Depends

from mobilidade.routes import listar_alertas, listar_linhas_acompanhadas
from mobilidade.services.servico_rastreamento import ServicoRastreamento
from mobilidade.services.servico_notificacoes import NotificadorNulo
from mobilidade.providers.gtfs_mock import FornecedorGTFSMock
from mobilidade.models import LinhaAcompanhada, AlertaAtraso


def _mock_db():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.filter.return_value.first.return_value = None
    return mock_db


def _mock_servico():
    return MagicMock(spec=ServicoRastreamento)


def test_listar_alertas_retorna_lista():
    mock_db = _mock_db()
    mock_servico = _mock_servico()
    uid = str(uuid.uuid4())
    alerta = MagicMock(spec=AlertaAtraso)
    alerta.id = uuid.uuid4()
    alerta.linha_id = "123"
    alerta.status = "ativo"
    alerta.atraso_inicio_minutos = 15.0
    alerta.ultimo_atraso_notificado = 15.0
    alerta.ultimo_alerta_enviado_em = None
    alerta.criado_em = None
    alerta.cancelado_em = None
    mock_servico.listar_alertas.return_value = [alerta]

    response = listar_alertas(usuario_id=uid, db=mock_db, servico=mock_servico)

    assert isinstance(response, list)
    assert len(response) == 1


def test_listar_alertas_retorna_vazio():
    mock_db = _mock_db()
    mock_servico = _mock_servico()
    uid = str(uuid.uuid4())
    mock_servico.listar_alertas.return_value = []

    response = listar_alertas(usuario_id=uid, db=mock_db, servico=mock_servico)

    assert response == []


def test_listar_linhas_acompanhadas_retorna_lista():
    mock_db = _mock_db()
    mock_servico = _mock_servico()
    uid = str(uuid.uuid4())
    linha = MagicMock(spec=LinhaAcompanhada)
    linha.linha_id = "123"
    linha.criado_em = None
    linha.ativo = 1
    mock_servico.listar_linhas_acompanhadas.return_value = [linha]

    response = listar_linhas_acompanhadas(usuario_id=uid, db=mock_db, servico=mock_servico)

    assert isinstance(response, list)
    assert len(response) == 1
    assert response[0]["linha_id"] == "123"


def test_listar_linhas_acompanhadas_retorna_vazio():
    mock_db = _mock_db()
    mock_servico = _mock_servico()
    uid = str(uuid.uuid4())
    mock_servico.listar_linhas_acompanhadas.return_value = []

    response = listar_linhas_acompanhadas(usuario_id=uid, db=mock_db, servico=mock_servico)

    assert response == []


def test_usuario_id_eh_uma_string_uuid():
    uid = str(uuid.uuid4())
    assert uuid.UUID(uid) is not None


def test_usuario_id_diferentes_para_differentes_usuarios():
    uid1 = str(uuid.uuid4())
    uid2 = str(uuid.uuid4())
    assert uid1 != uid2


def test_listar_alertas_header_obrigatorio():
    """O endpoint requer o header X-User-Id. Sem ele, FastAPI retorna 422."""
    from fastapi.testclient import TestClient
    from mobilidade.main import app

    client = TestClient(app)
    response = client.get("/mobilidade/alertas")
    assert response.status_code == 422


def test_listar_linhas_header_obrigatorio():
    from fastapi.testclient import TestClient
    from mobilidade.main import app

    client = TestClient(app)
    response = client.get("/mobilidade/linhas-acompanhadas")
    assert response.status_code == 422