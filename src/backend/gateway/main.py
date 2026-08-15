from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import get_settings
from gateway.routes import router as gateway_router

settings = get_settings()

app = FastAPI(
    title="Movecity — Gateway",
    description="Serviço de gateway da API de mobilidade urbana colaborativa",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gateway_router, prefix="/gateway", tags=["gateway"])


@app.get("/")
def root():
    return {"message": "Movecity — Serviço gateway"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway", "environment": settings.ENVIRONMENT}
