from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import get_settings

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


@app.get("/")
def root():
    return {"message": "Movecity API — Mobilidade Urbana Colaborativa"}


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
