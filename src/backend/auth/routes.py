import time
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from shared.database import get_db
from auth.models.usuario import Usuario
from auth.models.token_reset_senha import TokenResetSenha
from auth.schemas import SolicitacaoResetSenha, RedefinirSenha, RespostaGenerica
from auth.security import hash_senha, verificar_senha
from auth.email_service import enviar_email_reset_senha

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limit simples: max 5 solicitacoes por email em 15 minutos
_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 15 * 60  # 15 minutos em segundos


def _verificar_rate_limit(email: str) -> bool:
    agora = time.time()
    if email not in _rate_limit_store:
        _rate_limit_store[email] = []

    _rate_limit_store[email] = [
        t for t in _rate_limit_store[email] if agora - t < RATE_LIMIT_WINDOW
    ]

    if len(_rate_limit_store[email]) >= RATE_LIMIT_MAX:
        return False

    _rate_limit_store[email].append(agora)
    return True


@router.get("/hello")
def hello():
    return {"service": "auth", "status": "ok"}


@router.get("/teste-brenouchihar")
def teste_brenouchihar():
    return {
        "service": "auth",
        "autor": "brenouchihar",
        "mensagem": "hello world"
    }


@router.post("/esqueci-senha", response_model=RespostaGenerica)
def esqueci_senha(
    dados: SolicitacaoResetSenha,
    db: Session = Depends(get_db),
):
    if not _verificar_rate_limit(dados.email):
        raise HTTPException(
            status_code=429,
            detail="Muitas solicitacoes. Tente novamente mais tarde.",
        )

    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    if usuario:
        token_obj = TokenResetSenha.criar_novo(usuario_id=usuario.id)
        db.add(token_obj)
        db.commit()
        db.refresh(token_obj)

        enviar_email_reset_senha(dados.email, token_obj.token)
        logger.info(f"Token de reset gerado para {dados.email}")

    return RespostaGenerica(
        mensagem="Se o e-mail estiver cadastrado, voce recebera um link de redefinicao."
    )


@router.post("/redefinir-senha", response_model=RespostaGenerica)
def redefinir_senha(
    dados: RedefinirSenha,
    db: Session = Depends(get_db),
):
    if dados.nova_senha != dados.confirmacao_senha:
        raise HTTPException(
            status_code=400,
            detail="As senhas nao coincidem.",
        )

    if len(dados.nova_senha) < 8:
        raise HTTPException(
            status_code=400,
            detail="A senha deve ter no minimo 8 caracteres.",
        )

    token_obj = (
        db.query(TokenResetSenha)
        .filter(TokenResetSenha.token == dados.token)
        .first()
    )

    if not token_obj or not token_obj.valido:
        raise HTTPException(
            status_code=400,
            detail="Este link nao e mais valido ou expirou.",
        )

    usuario = db.query(Usuario).filter(Usuario.id == token_obj.usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=400,
            detail="Usuario nao encontrado.",
        )

    usuario.senha_hash = hash_senha(dados.nova_senha)
    token_obj.usado = True
    db.commit()

    logger.info(f"Senha redefinida com sucesso para {usuario.email}")

    return RespostaGenerica(mensagem="Senha redefinida com sucesso.")
