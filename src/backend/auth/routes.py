from fastapi import APIRouter

router = APIRouter()


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
