import logging

logger = logging.getLogger(__name__)


def enviar_email_reset_senha(email: str, token: str) -> bool:
    """Envia email com link de redefinicao de senha.

    Em producao, integrar com SendGrid, SES ou similar.
    Por enquanto, apenas loga o email para desenvolvimento.
    """
    link = f"http://localhost:3000/redefinir-senha?token={token}"
    logger.info(f"[ServicoEmail] Enviando email para {email}")
    logger.info(f"[ServicoEmail] Link de reset: {link}")
    return True
