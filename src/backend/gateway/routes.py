from fastapi import APIRouter

router = APIRouter()


@router.get("/hello")
def hello():
    return {"service": "gateway", "status": "ok"}
