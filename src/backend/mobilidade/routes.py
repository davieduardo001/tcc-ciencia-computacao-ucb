from fastapi import APIRouter

router = APIRouter()


@router.get("/hello")
def hello():
    return {"service": "mobilidade", "status": "ok"}
