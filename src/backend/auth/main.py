from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import get_settings
from auth.routes import router as auth_router

settings = get_settings()

app = FastAPI(
    title="Movecity — Auth",
    description="Serviço de auth da API de mobilidade urbana colaborativa",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/")
def root():
    return {"message": "Movecity — Serviço auth"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "auth", "environment": settings.ENVIRONMENT}
