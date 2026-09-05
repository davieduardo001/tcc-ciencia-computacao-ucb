from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import get_settings
from gateway.routes import router as gateway_router
from gateway.middleware import AutenticacaoMiddleware

settings = get_settings()

app = FastAPI(
    title="Movecity — API Gateway",
    description="Ponto único de entrada — proxy para todos os serviços backend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AutenticacaoMiddleware)

app.include_router(gateway_router, prefix="/api", tags=["api"])


@app.get("/")
def root():
    return {"message": "Movecity — API Gateway"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway", "environment": settings.ENVIRONMENT}
