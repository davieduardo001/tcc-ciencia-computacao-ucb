import uuid
from unittest.mock import MagicMock, patch

from mobilidade.services.servico_rastreamento import ServicoRastreamento
from mobilidade.services.servico_notificacoes import NotificadorMock
from mobilidade.providers.gtfs_mock import FornecedorGTFSMock


def _criar_servico(atrasos=None, notificador=None):
    fornecedor = FornecedorGTFSMock(atrasos=atrasos)
    notif = notificador or NotificadorMock()
    return ServicoRastreamento(fornecedor, notif)


def _mock_db_com_linha(linha_id="123", usuario_id=None):
    mock_db = MagicMock()
    usuario_id = usuario_id or uuid.uuid4()
    linha = MagicMock()
    linha.linha_id = linha_id
    linha.usuario_id = usuario_id
    mock_db.query.return_value.filter.return_value.all.return_value = [linha]
    return mock_db, usuario_id


def test_servico_nao_cria_alerta_atraso_10_ou_menos():
    servico = _criar_servico(atrasos={"123": 10.0})
    mock_db, uid = _mock_db_com_linha()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    servico.verificar_e_disparar_alertas(uid, mock_db)

    mock_db.add.assert_not_called()


def test_servico_cria_alerta_atraso_maior_10():
    servico = _criar_servico(atrasos={"123": 15.0})
    mock_db, uid = _mock_db_com_linha()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    servico.verificar_e_disparar_alertas(uid, mock_db)

    assert mock_db.add.call_args is not None


def test_servico_atualiza_alerta_variacao_5_ou_mais():
    servico = _criar_servico(atrasos={"123": 20.0})
    mock_db = MagicMock()
    usuario_id = uuid.uuid4()
    linha = MagicMock()
    linha.linha_id = "123"
    linha.usuario_id = usuario_id
    mock_db.query.return_value.filter.return_value.all.return_value = [linha]
    alerta_existente = MagicMock()
    alerta_existente.usuario_id = usuario_id
    alerta_existente.linha_id = "123"
    alerta_existente.status = "ativo"
    alerta_existente.ultimo_atraso_notificado = 10.0
    alerta_existente.ultimo_alerta_enviado_em = None

    mock_db.query.return_value.filter.return_value.first.return_value = alerta_existente
    mock_db.commit = MagicMock()

    servico.verificar_e_disparar_alertas(usuario_id, mock_db)

    assert alerta_existente.ultimo_atraso_notificado == 20.0


def test_servico_nao_atualiza_variacao_menos_que_5():
    servico = _criar_servico(atrasos={"123": 12.0})
    mock_db = MagicMock()
    usuario_id = uuid.uuid4()
    linha = MagicMock()
    linha.linha_id = "123"
    linha.usuario_id = usuario_id
    mock_db.query.return_value.filter.return_value.all.return_value = [linha]
    alerta_existente = MagicMock()
    alerta_existente.usuario_id = usuario_id
    alerta_existente.linha_id = "123"
    alerta_existente.status = "ativo"
    alerta_existente.ultimo_atraso_notificado = 10.0

    mock_db.query.return_value.filter.return_value.first.return_value = alerta_existente

    servico.verificar_e_disparar_alertas(usuario_id, mock_db)

    mock_db.commit.assert_not_called()


def test_servico_cancela_alerta_abaixo_de_5():
    servico = _criar_servico(atrasos={"123": 4.0})
    mock_db = MagicMock()
    usuario_id = uuid.uuid4()
    linha = MagicMock()
    linha.linha_id = "123"
    linha.usuario_id = usuario_id
    mock_db.query.return_value.filter.return_value.all.return_value = [linha]
    alerta_existente = MagicMock()
    alerta_existente.usuario_id = usuario_id
    alerta_existente.linha_id = "123"
    alerta_existente.status = "ativo"

    mock_db.query.return_value.filter.return_value.first.return_value = alerta_existente
    mock_db.commit = MagicMock()

    servico.verificar_e_disparar_alertas(usuario_id, mock_db)

    assert alerta_existente.status == "cancelado"


def test_servico_nao_cancela_atraso_igual_a_5():
    servico = _criar_servico(atrasos={"123": 5.0})
    mock_db = MagicMock()
    usuario_id = uuid.uuid4()
    linha = MagicMock()
    linha.linha_id = "123"
    linha.usuario_id = usuario_id
    mock_db.query.return_value.filter.return_value.all.return_value = [linha]
    alerta_existente = MagicMock()
    alerta_existente.usuario_id = usuario_id
    alerta_existente.linha_id = "123"
    alerta_existente.status = "ativo"

    mock_db.query.return_value.filter.return_value.first.return_value = alerta_existente

    servico.verificar_e_disparar_alertas(usuario_id, mock_db)

    assert alerta_existente.status == "ativo"


def test_servico_idempotencia_integrity_error_nao_derruba():
    servico = _criar_servico(atrasos={"123": 15.0})
    mock_db = MagicMock()
    usuario_id = uuid.uuid4()
    linha = MagicMock()
    linha.linha_id = "123"
    linha.usuario_id = usuario_id
    mock_db.query.return_value.filter.return_value.all.return_value = [linha]
    alerta_existente = MagicMock()
    alerta_existente.usuario_id = usuario_id
    alerta_existente.linha_id = "123"
    alerta_existente.status = "ativo"
    alerta_existente.ultimo_atraso_notificado = 10.0
    mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [None]

    from sqlalchemy.exc import IntegrityError
    mock_db.add.side_effect = IntegrityError("unique constraint", "stmt", "params")

    servico.verificar_e_disparar_alertas(usuario_id, mock_db)

    mock_db.rollback.assert_called()


def test_servico_fornecedor_none_nao_quebra():
    servico = _criar_servico(atrasos={"123": None})
    mock_db, uid = _mock_db_com_linha()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    servico.verificar_e_disparar_alertas(uid, mock_db)

    mock_db.add.assert_not_called()


def test_servico_notificador_mock_registra_chamadas():
    notificador = NotificadorMock()
    servico = _criar_servico(atrasos={"123": 15.0}, notificador=notificador)
    mock_db, uid = _mock_db_com_linha()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    servico.verificar_e_disparar_alertas(uid, mock_db)

    assert len(notificador.chamadas) > 0
    assert notificador.chamadas[0][0] == "disparado"