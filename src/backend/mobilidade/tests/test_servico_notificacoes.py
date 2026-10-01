import uuid
from unittest.mock import MagicMock

from mobilidade.services.servico_notificacoes import NotificadorMock


def test_notificador_mock_registra_disparado():
    notif = NotificadorMock()
    notif.alerta_disparado(str(uuid.uuid4()), "123", 15.0)
    assert ("disparado",) in [(c[0],) for c in notif.chamadas]


def test_notificador_mock_registra_atualizado():
    notif = NotificadorMock()
    notif.alerta_atualizado(str(uuid.uuid4()), "123", 20.0)
    assert ("atualizado",) in [(c[0],) for c in notif.chamadas]


def test_notificador_mock_registra_cancelado():
    notif = NotificadorMock()
    notif.alerta_cancelado(str(uuid.uuid4()), "123")
    assert ("cancelado",) in [(c[0],) for c in notif.chamadas]


def test_notificador_mock_chamadas_iniciais_vazias():
    notif = NotificadorMock()
    assert notif.chamadas == []


def test_notificador_mock_conta_por_tipo():
    notif = NotificadorMock()
    notif.alerta_disparado("u1", "123", 15.0)
    notif.alerta_atualizado("u1", "123", 20.0)
    notif.alerta_cancelado("u1", "123")

    tipos = [c[0] for c in notif.chamadas]
    assert tipos == ["disparado", "atualizado", "cancelado"]