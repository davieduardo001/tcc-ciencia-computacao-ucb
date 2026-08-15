from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import get_settings
from mobilidade.routes import router as mobilidade_router

settings = get_settings()

app = FastAPI(
    title="Movecity — Mobilidade",
    description="Serviço de mobilidade da API de mobilidade urbana colaborativa",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mobilidade_router, prefix="/mobilidade", tags=["mobilidade"])


@app.get("/")
def root():
    return {"message": "Movecity — Serviço mobilidade"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "mobilidade", "environment": settings.ENVIRONMENT}
