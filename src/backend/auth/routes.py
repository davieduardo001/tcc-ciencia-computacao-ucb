from fastapi import APIRouter

router = APIRouter()


@router.get("/hello")
def hello():
    return {"service": "auth", "status": "ok"}
