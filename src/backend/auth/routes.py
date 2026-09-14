import time
import logging
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.config import get_settings
from auth.models import Usuario, Sessao, TokenResetSenha
from auth.schemas import (
    LoginInput, LoginResponse, RegistrarInput, RegistrarResponse,
    GoogleLoginInput, GoogleLoginResponse, GoogleConfirmLinkInput,
    SolicitacaoResetSenha, RedefinirSenha, RespostaGenerica, MeResponse,
)
from auth.security import (
    hash_senha, verificar_senha, criar_access_token, criar_refresh_token,
    decodificar_access_token,
)
from auth.email_service import enviar_email_reset_senha
from auth.google_auth import validar_token_google

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

MAX_TENTATIVAS_FALHAS = 5
BLOQUEIO_MINUTOS = 15

_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 15 * 60


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


@router.post("/logout", response_model=RespostaGenerica)
def logout(request: Request, db: Session = Depends(get_db)):
    """
    Encerra a sessão associada ao access_token do cookie (se houver).

    O Gateway é quem limpa os cookies httpOnly de fato — este endpoint
    só remove o registro em `sessoes` para que o refresh token não
    possa mais ser usado. Idempotente: sem cookie ou sessão já removida,
    ainda responde sucesso.
    """
    token = request.cookies.get("access_token")
    if token:
        db.query(Sessao).filter(Sessao.access_token == token).delete()
        db.commit()

    return RespostaGenerica(mensagem="Logout realizado com sucesso.")


@router.get("/me", response_model=MeResponse)
def me(request: Request, db: Session = Depends(get_db)):
    """
    Dados do usuário autenticado, a partir do cookie access_token.

    O Gateway repassa o cookie ao proxyar a requisição (não injeta
    identidade via header) — este endpoint valida a assinatura do
    token ele mesmo, já que o Auth Service é alcançado pela URL
    pública do Fly.io, não por rede privada.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado.")

    payload = decodificar_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    try:
        usuario_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")

    return MeResponse(
        id=str(usuario.id),
        nome=usuario.nome,
        email=usuario.email,
        avatar_url=usuario.avatar_url,
    )


@router.post("/login", response_model=LoginResponse)
def login(dados: LoginInput, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )

    _verificar_bloqueio(usuario, db)

    if usuario.senha_hash is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )

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
        token_obj, token_plano = TokenResetSenha.criar_novo(usuario_id=usuario.id)
        db.add(token_obj)
        db.commit()

        enviar_email_reset_senha(dados.email, token_plano)
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
        .filter(TokenResetSenha.token == TokenResetSenha.hash_token(dados.token))
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


@router.post("/login/google", response_model=GoogleLoginResponse)
async def login_google(dados: GoogleLoginInput, db: Session = Depends(get_db)):
    try:
        dados_google = await validar_token_google(dados.id_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token Google inválido: {str(e)}",
        )

    email = dados_google["email"]
    nome = dados_google["nome"]
    google_id = dados_google["google_id"]
    picture = dados_google.get("picture")

    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if usuario:
        if usuario.status != "ativo":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Conta inativa. Verifique seu e-mail.",
            )
        if usuario.senha_hash is not None:
            # Não gravamos google_id/provider/avatar_url aqui: o vínculo só
            # deve virar fato em /link-google/confirmar, que revalida o
            # token do Google antes de tocar na conta.
            usuario.account_linking_pending = 1
            db.commit()
            db.refresh(usuario)
            return GoogleLoginResponse(
                access_token="",
                refresh_token="",
                account_linking_pending=True,
                account_linking_required=True,
            )
        usuario.tentativas_falhas = 0
        usuario.bloqueado_ate = None
        usuario.google_id = google_id
        usuario.provider = "google.com"
        if picture:
            usuario.avatar_url = picture
    else:
        usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=None,
            provider="google.com",
            google_id=google_id,
            avatar_url=picture,
            lgpd_accepted_at=datetime.utcnow(),
            status="ativo",
        )
        db.add(usuario)

    db.commit()
    db.refresh(usuario)

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

    return GoogleLoginResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/link-google/confirmar", response_model=GoogleLoginResponse)
async def confirmar_link_google(dados: GoogleConfirmLinkInput, db: Session = Depends(get_db)):
    try:
        dados_google = await validar_token_google(dados.id_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token Google inválido: {str(e)}",
        )

    if dados_google["email"] != dados.email or dados_google["google_id"] != dados.google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dados do Google não conferem com a solicitação de vinculação.",
        )

    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    if not usuario or usuario.account_linking_pending == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma conta aguardando vinculação com Google para este e-mail.",
        )

    if usuario.status != "ativo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta inativa. Verifique seu e-mail.",
        )

    usuario.senha_hash = None
    usuario.tentativas_falhas = 0
    usuario.bloqueado_ate = None
    usuario.google_id = dados_google["google_id"]
    usuario.provider = "google.com"
    if dados_google.get("picture"):
        usuario.avatar_url = dados_google["picture"]
    usuario.account_linking_pending = 0

    db.commit()
    db.refresh(usuario)

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

    return GoogleLoginResponse(access_token=access_token, refresh_token=refresh_token)