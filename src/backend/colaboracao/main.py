from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import get_settings
from colaboracao.routes import router as colaboracao_router

settings = get_settings()

app = FastAPI(
    title="Movecity — Colaboracao",
    description="Serviço de colaboracao da API de mobilidade urbana colaborativa",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(colaboracao_router, prefix="/colaboracao", tags=["colaboracao"])


@app.get("/")
def root():
    return {"message": "Movecity — Serviço colaboracao"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "colaboracao", "environment": settings.ENVIRONMENT}
