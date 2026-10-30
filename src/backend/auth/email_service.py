import logging
import os
import smtplib
from email.message import EmailMessage
from urllib.parse import quote

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_TIMEOUT_SEGUNDOS = 10
VALIDADE_LINK_MINUTOS = 60

_VARIAVEIS = ("SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM", "FRONTEND_URL")


def _ler_configuracao() -> dict[str, str] | None:
    """Le a configuracao SMTP do ambiente. Retorna None se algum valor faltar."""
    valores = {nome: os.environ.get(nome, "").strip() for nome in _VARIAVEIS}
    if not all(valores.values()):
        return None
    return valores


def montar_link_reset(frontend_url: str, token: str) -> str:
    return f"{frontend_url.rstrip('/')}/redefinir-senha?token={quote(token)}"


def _montar_mensagem(remetente: str, destinatario: str, link: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = "Movecity - redefinição de senha"
    msg["From"] = remetente
    msg["To"] = destinatario
    msg.set_content(
        "Olá!\n\n"
        "Recebemos um pedido para redefinir a senha da sua conta no Movecity.\n"
        "Para criar uma nova senha, acesse o link abaixo:\n\n"
        f"{link}\n\n"
        f"O link expira em {VALIDADE_LINK_MINUTOS} minutos e só pode ser usado uma vez.\n\n"
        "Se você não pediu a redefinição, pode ignorar este e-mail: "
        "sua senha continua a mesma.\n\n"
        "Equipe Movecity\n"
    )
    return msg


def enviar_email_reset_senha(email: str, token: str) -> bool:
    """Envia o e-mail de recuperacao de senha por SMTP.

    Nunca levanta excecao e nunca registra o token nem a senha SMTP.
    Retorna True se o e-mail foi entregue ao servidor SMTP.
    """
    config = _ler_configuracao()
    if config is None:
        logger.warning(
            "[ServicoEmail] SMTP nao configurado; e-mail de recuperacao nao enviado."
        )
        return False

    try:
        link = montar_link_reset(config["FRONTEND_URL"], token)
        msg = _montar_mensagem(config["SMTP_FROM"], email, link)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SEGUNDOS) as smtp:
            smtp.starttls()
            smtp.login(config["SMTP_USER"], config["SMTP_PASSWORD"])
            smtp.send_message(msg)
    except Exception as exc:
        # Registra so o tipo do erro: a mensagem pode conter dados sensiveis.
        logger.error(
            "[ServicoEmail] Falha ao enviar e-mail de recuperacao (%s).",
            type(exc).__name__,
        )
        return False

    logger.info("[ServicoEmail] E-mail de recuperacao enviado.")
    return True
