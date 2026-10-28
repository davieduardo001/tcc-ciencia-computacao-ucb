import logging
import smtplib
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from auth.email_service import enviar_email_reset_senha, montar_link_reset
from auth.main import app
from shared.database import get_db

TOKEN = "tokensecretoabc123"
CONFIG = {
    "SMTP_USER": "conta@exemplo.com",
    "SMTP_PASSWORD": "senha-de-app-falsa",
    "SMTP_FROM": "Movecity <conta@exemplo.com>",
    "FRONTEND_URL": "https://movecity-frontend.vercel.app",
}


def _smtp_mock():
    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    return smtp


def _configurar(monkeypatch, **extra):
    for k, v in {**CONFIG, **extra}.items():
        monkeypatch.setenv(k, v)


def _limpar(monkeypatch):
    for k in CONFIG:
        monkeypatch.delenv(k, raising=False)


def test_envio_com_sucesso(monkeypatch):
    _configurar(monkeypatch)
    smtp = _smtp_mock()
    with patch("auth.email_service.smtplib.SMTP", return_value=smtp) as cls:
        assert enviar_email_reset_senha("ana@email.com", TOKEN) is True

    args, kwargs = cls.call_args
    assert args == ("smtp.gmail.com", 587)
    assert kwargs["timeout"] > 0
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with(CONFIG["SMTP_USER"], CONFIG["SMTP_PASSWORD"])
    smtp.send_message.assert_called_once()


def test_conteudo_e_host_do_link(monkeypatch):
    _configurar(monkeypatch, FRONTEND_URL=CONFIG["FRONTEND_URL"] + "/")
    smtp = _smtp_mock()
    with patch("auth.email_service.smtplib.SMTP", return_value=smtp):
        enviar_email_reset_senha("ana@email.com", TOKEN)

    msg = smtp.send_message.call_args[0][0]
    corpo = msg.get_content()
    assert msg["To"] == "ana@email.com"
    assert msg["From"] == CONFIG["SMTP_FROM"]
    assert (
        f"https://movecity-frontend.vercel.app/redefinir-senha?token={TOKEN}" in corpo
    )
    assert "localhost" not in corpo
    assert "expira" in corpo
    assert "ignorar" in corpo


def test_montar_link_sem_barra_duplicada():
    assert (
        montar_link_reset("https://site.com/", "abc")
        == "https://site.com/redefinir-senha?token=abc"
    )


def test_sem_configuracao_nao_envia(monkeypatch):
    _limpar(monkeypatch)
    with patch("auth.email_service.smtplib.SMTP") as cls:
        assert enviar_email_reset_senha("ana@email.com", TOKEN) is False
    cls.assert_not_called()


def test_configuracao_parcial_nao_envia(monkeypatch):
    _configurar(monkeypatch, SMTP_PASSWORD="")
    with patch("auth.email_service.smtplib.SMTP") as cls:
        assert enviar_email_reset_senha("ana@email.com", TOKEN) is False
    cls.assert_not_called()


def test_falha_de_rede_nao_levanta_e_nao_vaza_segredos(monkeypatch, caplog):
    _configurar(monkeypatch)
    erro = smtplib.SMTPException(f"falhou {TOKEN} {CONFIG['SMTP_PASSWORD']}")
    with caplog.at_level(logging.DEBUG):
        with patch("auth.email_service.smtplib.SMTP", side_effect=erro):
            assert enviar_email_reset_senha("ana@email.com", TOKEN) is False
    assert TOKEN not in caplog.text
    assert CONFIG["SMTP_PASSWORD"] not in caplog.text


def test_token_nao_aparece_no_log(monkeypatch, caplog):
    with caplog.at_level(logging.DEBUG):
        _limpar(monkeypatch)
        enviar_email_reset_senha("ana@email.com", TOKEN)
        _configurar(monkeypatch)
        with patch("auth.email_service.smtplib.SMTP", return_value=_smtp_mock()):
            enviar_email_reset_senha("ana@email.com", TOKEN)
    assert TOKEN not in caplog.text


def test_endpoint_responde_200_mesmo_com_falha_smtp(monkeypatch):
    _configurar(monkeypatch)
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(
        id="u1"
    )
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with patch("auth.email_service.smtplib.SMTP", side_effect=OSError("sem rede")):
            r = TestClient(app).post(
                "/auth/esqueci-senha", json={"email": "falha-smtp@email.com"}
            )
        assert r.status_code == 200
    finally:
        app.dependency_overrides.clear()
