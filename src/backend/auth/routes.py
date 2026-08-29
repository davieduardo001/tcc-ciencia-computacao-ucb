from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from auth.schemas import (
    RegistroRequest,
    LoginRequest,
    UsuarioResponse,
    MensagemResponse,
)
from auth.service import (
    registrar_usuario,
    autenticar_usuario,
    criar_access_token,
    criar_refresh_token,
    criar_sessao,
    decodificar_token,
    revogar_sessao,
    validar_refresh_token,
)
from auth.dependencies import get_db, get_current_user
from auth.models.usuario import Usuario
from auth.models.sessao import Sessao

router = APIRouter()

ACCESS_TOKEN_EXPIRY = timedelta(minutes=60)
REFRESH_TOKEN_EXPIRY = timedelta(days=7)


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=int(ACCESS_TOKEN_EXPIRY.total_seconds()),
        path="/api",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=int(REFRESH_TOKEN_EXPIRY.total_seconds()),
        path="/api/auth",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/api")
    response.delete_cookie(key="refresh_token", path="/api/auth")


@router.post(
    "/registrar",
    response_model=MensagemResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar(body: RegistroRequest, db: Session = Depends(get_db)):
    try:
        registrar_usuario(db, body.nome, body.email, body.senha)
        return MensagemResponse(mensagem="Conta criada com sucesso. Faça login.")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=MensagemResponse)
def login(
    body: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
    usuario = autenticar_usuario(db, body.email, body.senha)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
        )

    access_token = criar_access_token(str(usuario.id))
    refresh_token = criar_refresh_token(str(usuario.id))

    user_agent = request.headers.get("user-agent")
    criar_sessao(db, usuario.id, refresh_token, user_agent)

    set_auth_cookies(response, access_token, refresh_token)

    return MensagemResponse(mensagem="Login realizado com sucesso")


@router.post("/refresh")
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token não encontrado",
        )

    sessao = validar_refresh_token(db, refresh_token)
    if not sessao:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada",
        )

    access_token = criar_access_token(str(sessao.usuario_id))

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=int(ACCESS_TOKEN_EXPIRY.total_seconds()),
        path="/api",
    )

    return MensagemResponse(mensagem="Token renovado")


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        payload = decodificar_token(refresh_token)
        if payload:
            sessao = (
                db.query(Sessao)
                .filter(
                    Sessao.usuario_id == payload.get("sub"),
                    Sessao.revogado == False,
                )
                .first()
            )
            if sessao:
                revogar_sessao(db, sessao.id)

    clear_auth_cookies(response)
    return MensagemResponse(mensagem="Logout realizado com sucesso")


@router.get("/me", response_model=UsuarioResponse)
def me(usuario: Usuario = Depends(get_current_user)):
    return usuario
