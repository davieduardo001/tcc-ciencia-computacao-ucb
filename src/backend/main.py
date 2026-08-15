from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from gateway.routes import router as gateway_router
from auth.routes import router as auth_router
from mobilidade.routes import router as mobilidade_router
from colaboracao.routes import router as colaboracao_router

settings = get_settings()

app = FastAPI(
    title="Movecity API",
    description="API de mobilidade urbana colaborativa para o DF",
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
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(mobilidade_router, prefix="/mobilidade", tags=["mobilidade"])
app.include_router(colaboracao_router, prefix="/colaboracao", tags=["colaboracao"])


@app.get("/")
def root():
    return {"message": "Movecity API — Mobilidade Urbana Colaborativa"}


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
