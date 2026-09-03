from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from shared.database import get_db
from shared.config import get_settings
from auth.models import Usuario, Sessao
from auth.schemas import LoginInput, LoginResponse, RegistrarInput, RegistrarResponse
from auth.security import hash_senha, verificar_senha, criar_access_token, criar_refresh_token

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