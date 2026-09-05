from fastapi import APIRouter

router = APIRouter()


@router.get("/hello")
def hello():
    return {"service": "colaboracao", "status": "ok"}


@router.get("/teste-vitoria")
def teste_vitoria():
    return {"service": "colaboracao", "autor": "Vitoria-Albuquerque", "mensagem": "hello world"}


@router.get("/teste-gualberto")
def teste_gualberto():
    return {"service": "colaboracao", "autor": "gualbertonathalia", "mensagem": "hello world"}
