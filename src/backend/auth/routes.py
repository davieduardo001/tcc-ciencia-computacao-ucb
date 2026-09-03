import time
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.config import get_settings
from auth.models import Usuario, Sessao, TokenResetSenha
from auth.schemas import (
    LoginInput, LoginResponse, RegistrarInput, RegistrarResponse,
    SolicitacaoResetSenha, RedefinirSenha, RespostaGenerica,
)
from auth.security import hash_senha, verificar_senha, criar_access_token, criar_refresh_token
from auth.email_service import enviar_email_reset_senha

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

MAX_TENTATIVAS_FALHAS = 5
BLOQUEIO_MINUTOS = 15


def _verificar_bloqueio(usuario: Usuario, db: Session):
    if usuario.bloqueado_ate and usuario.bloqueado_ate > datetime.utcnow():
        minutos_restantes = int((usuario.bloqueado_ate - datetime.utcnow()).total_seconds() // 60)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Conta bloqueada. Tente novamente em {minutos_restantes} minutos.",
        )
    if usuario.bloqueado_ate and usuario.bloqueado_ate <= datetime.utcnow():
        usuario.tentativas_falhas = 0
        usuario.bloqueado_ate = None
        db.commit()


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


@router.post("/login", response_model=LoginResponse)
def login(dados: LoginInput, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )

    _verificar_bloqueio(usuario, db)

    if not verificar_senha(dados.senha, usuario.senha_hash):
        usuario.tentativas_falhas += 1
        if usuario.tentativas_falhas >= MAX_TENTATIVAS_FALHAS:
            usuario.bloqueado_ate = datetime.utcnow() + timedelta(minutes=BLOQUEIO_MINUTOS)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Conta bloqueada por muitas tentativas falhas.",
            )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )

    if usuario.status != "ativo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta inativa. Verifique seu e-mail.",
        )

    usuario.tentativas_falhas = 0
    usuario.bloqueado_ate = None

    access_token = criar_access_token({"sub": str(usuario.id)})
    refresh_token = criar_refresh_token({"sub": str(usuario.id)})
    expires_at = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)

    sessao = Sessao(
        usuario_id=usuario.id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )
    db.add(sessao)
    db.commit()
    db.refresh(sessao)

    return LoginResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/registrar", response_model=RegistrarResponse)
def registrar(dados: RegistrarInput, db: Session = Depends(get_db)):
    existente = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está em uso.",
        )

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        lgpd_accepted_at=datetime.utcnow(),
        status="ativo",
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return RegistrarResponse(
        id=str(usuario.id),
        nome=usuario.nome,
        email=usuario.email,
        mensagem="Verifique seu e-mail para confirmar a conta.",
    )


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